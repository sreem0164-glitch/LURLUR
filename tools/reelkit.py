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


def clip(src, ss, srclen, dur, out, hdr=False, crop=None):
    """원본 ss초부터 srclen초를 화면 dur초로 넣음 (srclen>dur이면 빨라짐, 슬로우는 쓰지 않음)."""
    n = round(dur * FPS); sp = srclen / dur
    assert sp >= 0.99, f'슬로우 금지: {src} {sp:.2f}'
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
    vk = int(min(max_kbps, (target_mb * 8e6 / dur - 128e3) * 0.97 / 1000))
    log = os.path.join(workdir, 'x264pass')
    v = ['-c:v', 'libx264', '-preset', 'slower', '-profile:v', 'high', '-b:v', f'{vk}k',
         '-maxrate', f'{vk * 2}k', '-bufsize', f'{vk * 2}k', '-pix_fmt', 'yuv420p', '-r', '30',
         '-x264-params', 'aq-mode=3', '-passlogfile', log] + COLOR
    run(['ffmpeg', '-y', '-v', 'error', '-i', comp, '-frames:v', str(totf)] + v + ['-pass', '1', '-an', '-f', 'null', '/dev/null'])
    ain = ['-i', audio] if audio else ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']
    run(['ffmpeg', '-y', '-v', 'error', '-i', comp] + ain + ['-map', '0:v', '-map', '1:a', '-frames:v', str(totf)] + v +
        ['-pass', '2', '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', out])
    return vk
