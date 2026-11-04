"""릴스 편집 공통 처리 (화질·끊김 개선판).

- 크기 조절: lanczos + 약한 샤프닝(밝기 채널만, unsharp 0.5)
- 배속: 프레임을 버리지 않고 앞뒤 프레임을 섞어 30fps로 다시 만듦(framerate).
  예전 방식(setpts+fps)은 1.2~1.5배속에서 몇 프레임마다 한 장이 빠져 화면이 툭툭 튀었음.
- 장면 중간 파일: crf 10 (화질 손실 거의 없음)
- 최종 파일: 2-pass로 정한 용량(기본 28.5MB) 안에서 가장 높은 화질
"""
import subprocess, os

W, H, FPS = 1080, 1920, 30
TM = ('zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=100,format=gbrpf32le,'
      'zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,')
EQ = 'eq=saturation=1.10:contrast=1.04:brightness=0.02'
SHARP = 'unsharp=5:5:0.5:5:5:0'
SCALE = f'scale={W}:{H}:flags=lanczos+accurate_rnd+full_chroma_int'
COLOR = ['-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']
MID = ['-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '10', '-pix_fmt', 'yuv420p', '-r', '30'] + COLOR


def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        print(' '.join(c)[:400]); print(r.stderr[-1500:]); raise SystemExit(1)


def probe_dur(f):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def clip(src, ss, srclen, dur, out, hdr=False, crop=None, slow=False):
    """원본 ss초부터 srclen초를 화면 dur초로 넣음 (srclen>dur이면 빨라짐).
    느리게는 기본으로 막음. slow=True인 장면만 프레임을 섞어 느리게 해서 같은 프레임이
    반복되는 끊김이 없게 함 (카메라 움직임이 거의 없는 장면에만 씀).
    움직임 보간(minterpolate)도 시험했으나 이 촬영본에서는 섞는 방식이 더 매끄럽게 측정됨."""
    n = round(dur * FPS); sp = srclen / dur
    assert sp >= 0.97 or slow, f'슬로우 금지: {src} {sp:.2f}'
    vf = (TM if hdr else '') + SCALE + (',' + crop if crop else '') + f',{EQ},{SHARP},setsar=1'
    if abs(sp - 1) > 0.01:
        vf += f',setpts=PTS/{sp:.5f},framerate=fps=30'
    else:
        vf += ',fps=30'
    vf += ',tpad=stop_mode=clone:stop_duration=2'
    # 섞을 다음 프레임이 있도록 원본을 2프레임 더 읽음 (원본 끝을 넘지 않게)
    t = min(srclen + 2 / FPS, probe_dur(src) - ss)
    run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{ss:.3f}', '-t', f'{t:.3f}', '-i', src, '-vf', vf,
         '-frames:v', str(n)] + MID + [out])
    return n


def concat(parts, listfile, out):
    open(listfile, 'w').write(''.join(f"file '{p}'\n" for p in parts))
    run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', listfile, '-c', 'copy', out])


def open_io(base, comp, totf):
    """base.mp4를 RGB로 읽고, 글자 얹은 프레임을 comp.mp4(고화질 중간 파일)로 쓰는 파이프."""
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', base, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-r', '30', '-i', '-', '-frames:v', str(totf)] + MID + [comp], stdin=subprocess.PIPE)
    return dec, enc


def final(comp, out, totf, workdir, audio=None, target_mb=28.5, max_kbps=14000):
    """2-pass 최종 인코딩. audio가 없으면 무음 트랙을 넣음."""
    dur = totf / FPS
    ab = 192 if audio else 128
    vk = int(min(max_kbps, (target_mb * 8e6 / dur - ab * 1e3) * 0.97 / 1000))
    log = os.path.join(workdir, 'x264pass')
    v = ['-c:v', 'libx264', '-preset', 'slower', '-profile:v', 'high', '-b:v', f'{vk}k',
         '-maxrate', f'{vk * 2}k', '-bufsize', f'{vk * 2}k', '-pix_fmt', 'yuv420p', '-r', '30',
         '-x264-params', 'aq-mode=3', '-passlogfile', log] + COLOR
    run(['ffmpeg', '-y', '-v', 'error', '-i', comp, '-frames:v', str(totf)] + v + ['-pass', '1', '-an', '-f', 'null', '/dev/null'])
    ain = ['-i', audio] if audio else ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']
    run(['ffmpeg', '-y', '-v', 'error', '-i', comp] + ain + ['-map', '0:v', '-map', '1:a', '-frames:v', str(totf)] + v +
        ['-pass', '2', '-af', 'apad', '-c:a', 'aac', '-b:a', f'{ab}k', '-shortest', '-movflags', '+faststart', out])
    return vk


# ---------------- TTS(캡컷) 맞추기 ----------------
SR = 48000

def syl(t):
    return sum(1 for ch in t if '가' <= ch <= '힣' or ch.isalnum())


def tts_layout(tts, bound, lines, workdir, speed=1.1, gap_scene=0.12, gmax=0.18, pad=0.04, tail=0.7):
    """캡컷 TTS 영상에서 목소리만 뽑아 장면 사이 쉼을 줄이고 speed배로 빠르게 함.
    bound: 캡컷 텍스트 클립 경계(초), lines: 장면별 (1줄, 2줄).
    돌려주는 것: 장면별 (말 시작, 말 끝, 2줄이 시작되는 시점), 전체 길이(초) — 모두 결과 영상 기준.
    목소리 파일은 workdir/voice.wav 로 저장. tail은 마지막 말 뒤 여유(결과 기준 초)."""
    import wave, numpy as np
    raw = os.path.join(workdir, 'tts48.wav')
    run(['ffmpeg', '-y', '-v', 'error', '-i', tts, '-vn', '-ac', '2', '-ar', str(SR), raw])
    w = wave.open(raw); X = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32)
    mono = X.mean(axis=1) / 32768
    db = np.array([20 * np.log10(np.sqrt(np.mean(mono[i:i + 480] ** 2)) + 1e-9) for i in range(0, len(mono) - 480, 480)])
    runs = []; s = None
    for i, a in enumerate(db > -38):
        if a and s is None: s = i
        if not a and s is not None: runs.append([s * 0.01, i * 0.01]); s = None
    if s is not None: runs.append([s * 0.01, len(db) * 0.01])
    m = []
    for r in runs:
        if m and r[0] - m[-1][1] < 0.10: m[-1][1] = r[1]
        else: m.append(r)
    runs = [r for r in m if r[1] - r[0] > 0.05]
    pieces = []; scenes = []; tcur = 0.0
    for k in range(len(lines)):
        sr_ = [[max(r[0], bound[k]), min(r[1], bound[k + 1])] for r in runs if r[1] > bound[k] + 0.03 and r[0] < bound[k + 1] - 0.03]
        a0 = max(0, sr_[0][0] - pad); b0 = sr_[-1][1] + pad
        segs = [[max(a0, r[0] - pad), min(b0, r[1] + pad)] for r in sr_]
        mm = []
        for sg in segs:
            if mm and sg[0] <= mm[-1][1]: mm[-1][1] = max(mm[-1][1], sg[1])
            else: mm.append(sg)
        mp = []; t = tcur
        for i, (a, b) in enumerate(mm):
            if i: t += min(gmax, a - mm[i - 1][1])
            mp.append((a, b, t)); pieces.append((a, b, t)); t += b - a
        act = sum(b - a for a, b in sr_)
        target = act * syl(lines[k][0]) / (syl(lines[k][0]) + syl(lines[k][1]))
        cum = 0; best = None
        for i in range(1, len(sr_)):
            cum += sr_[i - 1][1] - sr_[i - 1][0]; gap = sr_[i][0] - sr_[i - 1][1]
            sc = abs(cum - target) - 0.6 * min(gap, 0.6)
            if gap >= 0.10 and (best is None or sc < best[0]): best = (sc, sr_[i][0])
        def m2n(x):
            for a, b, tt in mp:
                if a - 0.001 <= x <= b + 0.001: return tt + (x - a)
            for a, b, tt in mp:
                if x < a: return tt
            a, b, tt = mp[-1]; return tt + (b - a)
        split = m2n(best[1]) if best else tcur + (t - tcur) * target / act
        scenes.append((tcur, t, split)); tcur = t + gap_scene
    total = scenes[-1][1] + tail * speed
    buf = np.zeros((int(total * SR) + SR, 2), np.float32)
    for a, b, t in pieces:
        seg = X[int(a * SR):int(b * SR)].copy(); f = int(0.008 * SR)
        seg[:f] *= np.linspace(0, 1, f)[:, None]; seg[-f:] *= np.linspace(1, 0, f)[:, None]
        i = int(round(t * SR)); buf[i:i + len(seg)] += seg
    buf = buf[:int(round(total * SR))]
    o = wave.open(os.path.join(workdir, 'voice_raw.wav'), 'wb'); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
    o.writeframes(np.clip(buf, -32768, 32767).astype(np.int16).tobytes()); o.close()
    run(['ffmpeg', '-y', '-v', 'error', '-i', os.path.join(workdir, 'voice_raw.wav'), '-af', f'atempo={speed}',
         os.path.join(workdir, 'voice.wav')])
    return [(a / speed, b / speed, c / speed) for a, b, c in scenes], total / speed


def word_starts(lines, a, b, split, lead=0.05):
    """두 줄 자막의 단어별 등장 시각(초). 1줄은 a~split, 2줄은 split~b 사이에 글자 수 비율로 배치."""
    out = []
    for (t0, t1), line in zip(((a, split), (split, b)), lines):
        ws = line.split(' '); tot = sum(syl(x) for x in ws) or 1; cum = 0
        for x in ws:
            out.append(max(0.0, t0 + (t1 - t0) * cum / tot - lead)); cum += syl(x)
    return out


def mix_bgm(voice, bgm, total, out, vol=0.40):
    """BGM을 목소리보다 작게 깔고, 말할 때는 더 줄어들게(덕킹). 앞 0.4초 페이드인, 끝 1.5초 페이드아웃."""
    fo = round(total - 1.5, 2)
    run(['ffmpeg', '-y', '-v', 'error', '-i', voice, '-i', bgm, '-filter_complex',
         f'[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f},volume={vol},'
         f'afade=t=in:d=0.4,afade=t=out:st={fo}:d=1.5[b];'
         '[0:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:' + f'{total:.3f}' + ',asplit=2[v][sc];'
         '[b][sc]sidechaincompress=threshold=0.02:ratio=3:attack=30:release=350[bd];'
         '[v][bd]amix=inputs=2:normalize=0:duration=first[a]',
         '-map', '[a]', '-c:a', 'pcm_s16le', out])
