"""레커버거 둔산점 협찬 릴스 (디너의여왕 캠페인) — 캡컷 TTS + 자막 + BGM.

참고 릴스 방식: 1~1.5초마다 컷, 컷마다 짧은 한 줄 자막(흰 글자+검정 테두리, 강조는 노란색 1~2곳만)
자막은 컷마다 음식·간판을 가리지 않는 빈 곳에 둠.
첫 컷: 패티 많은 버거(왕커버거) 클로즈업 + "패티가 몇 개야?" (= 썸네일 문구)
캠페인 필수: 30~50초, 영상에 썸네일 문구, 초반에 '대전 배달 맛집으로 이미 소문남'(둘째 컷), 음료 무한리필(알림받기·매장 식사),
            수제버거인데 종류 다양, 특제소스·수제패티 풍미. 메뉴 이름·가격은 넣지 않음.
필요한 것: 업로드 폴더의 IMG_1812~1822.mov (4K HDR), BGM copy_E934EEC6-...mov,
         캡컷 TTS copy_BF67C104-...mov (텍스트 클립 4개, 문장 20개 + 끝 문장 2개)
실행: /usr/bin/python3 -I tools/lecker_build.py
"""
import os, sys, glob, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reelkit as rk
from reelkit import W, H, FPS

S = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/m24/'
U = '/root/.claude/uploads/56b70c86-dc21-539d-984f-e6a7533bf099/'
FONT = S + '../fonts_dl/x_pretendard/package/dist/public/static/Pretendard-Black.otf'
OUT = '/home/user/LURLUR/lecker_reel.mp4'
THUMB = '/home/user/LURLUR/lecker_thumb.jpg'
os.makedirs(S + 'seg3', exist_ok=True)
up = lambda p: sorted(glob.glob(U + p), key=os.path.getmtime)[-1]
V = {n: up(f'*-IMG_{n}.mov') for n in range(1812, 1823)}
BGM = up('*-copy_E934EEC6-76BD-467A-8B83-6741C39297DE.mov')
# 색: HDR을 밝게 변환하고 채도는 거의 그대로 (매장 조명이 원래 빨개서 채도를 올리면 벽까지 빨갛게 번짐)
LOOK = ('zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,'
        'zscale=p=bt709,tonemap=tonemap=mobius:param=0.5:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,',
        'eq=saturation=1.04:contrast=1.06')
# 1820: 위쪽에 같이 먹은 분 턱이 걸림 → 위 142px만 자르고(1.08배 확대), 닭강정 상자 쪽으로 살짝 옮김
CHIN = 'crop=1000:1778:80:142,scale=1080:1920:flags=lanczos'
Y = (255, 226, 74)

TTS = up('*-copy_BF67C104-A766-46F4-91BB-8B596F74981B.mov')
import json, wave
import numpy as np
SR = 48000
# ---------------- 목소리: 문장 22개의 위치 (캡컷 클립 경계 4.88/18.72/28.18초 + 쉬는 자리로 찾음) ----------------
PHR = [(0.09, 1.27), (1.58, 4.38),
       (5.08, 6.84), (7.08, 9.40), (9.70, 11.13), (11.32, 13.25), (13.43, 16.45), (16.69, 18.64),
       (18.89, 20.28), (20.77, 22.27), (22.64, 24.14), (24.73, 26.48), (26.82, 27.85),
       (28.35, 29.32), (29.61, 30.98), (31.27, 32.53), (32.60, 33.40), (33.74, 34.72), (35.05, 35.91),
       (36.23, 37.32), (37.55, 38.77)]
PAD, GAP, HOOK_GAP, TAIL = 0.04, 0.12, 0.45, 0.8
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', TTS, '-vn', '-ac', '2', '-ar', str(SR), '-c:a', 'pcm_s16le', S + 'tts.wav'])
_w = wave.open(S + 'tts.wav'); X = np.frombuffer(_w.readframes(_w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32)
pos = []; t = 0.05
for k, (a0, b0) in enumerate(PHR):
    pos.append(t); t += (b0 - a0) + 2 * PAD
    if k + 1 < len(PHR):
        g = PHR[k + 1][0] - b0
        t += HOOK_GAP if k == 0 else min(max(g - 2 * PAD, 0.0), GAP)
VEND = t; TOTAL = VEND + TAIL
buf = np.zeros((int(TOTAL * SR) + SR, 2), np.float32)
for (a0, b0), t0 in zip(PHR, pos):
    seg = X[int((a0 - PAD) * SR):int((b0 + PAD) * SR)].copy(); f = int(0.008 * SR)
    seg[:f] *= np.linspace(0, 1, f)[:, None]; seg[-f:] *= np.linspace(1, 0, f)[:, None]
    i0 = int(round(t0 * SR)); buf[i0:i0 + len(seg)] += seg
buf = buf[:int(round(TOTAL * SR))]
_o = wave.open(S + 'voice.wav', 'wb'); _o.setnchannels(2); _o.setsampwidth(2); _o.setframerate(SR)
_o.writeframes(np.clip(buf, -32768, 32767).astype(np.int16).tobytes()); _o.close()
# 컷 경계 = 문장이 시작하는 순간(0.05초 먼저). 마지막 두 문장(둔산동 레커버거 / 저장해두고 가보세요)은 한 컷.
CUTT = [0.0] + [p - 0.05 for p in pos[1:20]] + [TOTAL]
CF = [round(x * FPS) for x in CUTT]
LINE2_F = round((pos[20] - 0.05) * FPS)          # 끝 컷의 둘째 줄이 나오는 프레임
for k in range(20): print(f'컷 {k+1:2d}: {CF[k]/FPS:5.2f}~{CF[k+1]/FPS:5.2f} ({(CF[k+1]-CF[k])/FPS:.2f}s)')

# (촬영본, 시작, 자막(줄 또는 줄 묶음), 노란 강조, 특수, 자막 가운데 y, 글자 크기) — 길이는 목소리로 정해짐, 원본 속도
# 자막 y: 화면 맨 위 300px 안과 1480px 아래는 릴스 화면의 버튼·글자와 겹쳐서 쓰지 않음
CUTS = [(1817, 0.4, '패티가 몇 개야?', None, 'hook', 340, 118),                          # 왕커버거 클로즈업 (썸네일 문구)
        (1815, 0.0, ('대전에서 이미', '배달 맛집으로 소문난 곳'), None, None, 1250, 84),   # 밤 외관 간판 (캠페인 필수, 초반)
        (1813, 0.0, '매장 들어가자마자', None, None, 930, 84),
        (1812, 0.0, '미국 다이너 감성 그대로', None, None, 560, 84),
        (1812, 'next', '수제버거인데', None, None, 760, 84),
        (1812, 'next', '버거 종류도 다양하고', None, None, 760, 84),
        (1814, 0.0, '알림받기 하고 매장에서 먹으면', None, None, 760, 84),               # 매장 좌석
        (1812, 6.55, '음료 무한리필!', '무한리필!', 'drink', 1330, 84),                   # 셀프 음료대
        (1816, 1.8, '둘이서 시킨 한 상', None, None, 310, 84),
        (1817, 'after_hook', '수제 패티가 겹겹이', None, None, 310, 84),
        (1817, 'next', '치즈까지 녹아내림', None, None, 310, 84),
        (1819, 4.1, '바삭한 치킨버거까지', None, None, 1420, 84),
        (1820, 4.2, '닭강정까지', None, 'chin', 330, 84),
        (1821, 0.0, '한 입 베어 물면', None, None, 310, 84),
        (1821, 'next', '특제소스랑 수제패티', None, None, 310, 84),
        (1822, 0.0, '풍미가 꽉 차요', '풍미', None, 330, 84),
        (1822, 2.3, '속이 꽉 찬 단면', None, None, 310, 84),
        (1818, 0.0, '배달로만 먹기엔', None, None, 320, 84),
        (1818, 'next', '아까운 비주얼', None, None, 320, 84),
        (1813, 1.78, ('둔산동 레커버거', '저장해두고 가보세요!'), None, 'end', 940, 80)]   # 네온 간판 아래 흰 벽
SHOTS = []; last_end = {}
for k, (n, ss, txt, emph, sp, sy, size) in enumerate(CUTS):
    d = (CF[k + 1] - CF[k]) / FPS
    if ss == 'next': ss = last_end[n]
    elif ss == 'after_hook': ss = SHOTS[0][1] + SHOTS[0][2]
    elif ss == 'after3': ss = SHOTS[2][1] + SHOTS[2][2]
    dur_src = rk.probe_dur(V[n])
    assert ss + d + 2 / FPS <= dur_src + 1e-3, f'컷 {k+1}: 원본 {n} 길이 부족 ({ss:.2f}+{d:.2f} > {dur_src:.2f})'
    SHOTS.append((n, ss, d, txt, emph, sp, sy, size)); last_end[n] = ss + d

parts = []
for i, (n, ss, d, *_r) in enumerate(SHOTS):
    out = S + f'seg3/{i}.mp4'
    rk.clip(V[n], ss, d, d, out, hdr=True, crop=CHIN if _r[2] == 'chin' else None, look=LOOK)
    parts.append(out)
starts = CF[:]; TOTF = CF[-1]
rk.concat(parts, S + 'cat3.txt', S + 'base3.mp4')
print('total', TOTF / FPS)

# ---------------- 자막 ----------------
def line_img(txt, emph=None, size=84):
    while True:
        f = ImageFont.truetype(FONT, size)
        if f.getlength(txt) <= 980: break
        size -= 4
    stroke = max(7, size // 12); pad = 30
    w = int(f.getlength(txt)) + 2 * pad; asc, desc = f.getmetrics(); h = asc + desc + 2 * pad
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((pad, pad + 6), txt, font=f, fill=(0, 0, 0, 160), stroke_width=stroke + 2, stroke_fill=(0, 0, 0, 160))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img); x = pad
    segs = [(txt, None)]
    if emph and emph in txt:
        a = txt.index(emph); segs = [(txt[:a], None), (emph, Y), (txt[a + len(emph):], None)]
    for s, c in segs:
        if s:
            d.text((x, pad), s, font=f, fill=c or (255, 255, 255), stroke_width=stroke, stroke_fill=(10, 10, 10)); x += f.getlength(s)
    return img
SUBS = []
for i, (n, ss, d, txt, emph, sp, sy, size) in enumerate(SHOTS):
    imgs = [line_img(txt, emph, size)] if isinstance(txt, str) else [line_img(x, None, size) for x in txt]
    SUBS.append((starts[i], starts[i + 1], imgs, sy, LINE2_F if sp == 'end' else None))
DRINK = [i for i, s in enumerate(SHOTS) if s[5] == 'drink'][0]

def drink_circle(fr, k, t_src):
    """'SELF DRINK' 간판에 빨간 동그라미. 카메라가 움직여서 간판 위치를 시간에 맞춰 옮김 (7.6초 x=230 → 8.75초 x=416).
    간판이 화면 안에 다 들어오는 7.3초부터 그림."""
    if t_src < 7.3: return
    cx = 230 + (t_src - 7.6) / 1.15 * 186; cy = 584; rx, ry = 200, 64
    a = min(1.0, (t_src - 7.3) * FPS / 5)
    lay = Image.new('RGBA', (W * 2, H * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    bb = ((cx - rx) * 2, (cy - ry) * 2, (cx + rx) * 2, (cy + ry) * 2)
    d.arc((bb[0] - 6, bb[1] - 6, bb[2] + 6, bb[3] + 6), -100, -100 + 360 * a, fill=(255, 255, 255, 220), width=24)
    d.arc(bb, -100, -100 + 360 * a, fill=(255, 48, 48, 255), width=16)
    fr.alpha_composite(lay.resize((W, H), Image.LANCZOS))

CHK = {starts[0] + 20, starts[1] + 30, starts[6] + 20, starts[DRINK + 1] - 5, starts[12] + 20, TOTF - 10}
dec, enc = rk.open_io(S + 'base3.mp4', S + 'comp3.mp4', TOTF)
last = None
for fi in range(TOTF):
    raw = dec.stdout.read(W * H * 3)
    if len(raw) < W * H * 3: raw = last
    last = raw
    fr = Image.frombytes('RGB', (W, H), raw).convert('RGBA')
    if starts[DRINK] <= fi < starts[DRINK + 1]:
        k = fi - starts[DRINK]; drink_circle(fr, k, SHOTS[DRINK][1] + k / FPS)
    for f0, f1, imgs, sy, l2 in SUBS:
        if f0 <= fi < f1:
            y = sy - sum(im.height for im in imgs) // 2 + 20 * (len(imgs) - 1)
            for li, im in enumerate(imgs):
                s0 = l2 if (li == 1 and l2) else f0          # 끝 컷 둘째 줄은 그 문장을 말할 때 나타남
                al = min(1.0, (fi - s0 + 1) / 3)              # 튀어나오는 효과 없이 살짝 나타나기만
                if al > 0:
                    if al < 1:
                        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * al)))
                    fr.alpha_composite(im, ((W - im.width) // 2, y))
                y += imgs[li].height - 40
    if fi in CHK:
        fr.convert('RGB').save(S + f'chk3_{fi}.png')
    enc.stdin.write(fr.convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()

# ---------------- 소리: 목소리 + BGM (목소리보다 작게, 말할 때 더 줄어듦) ----------------
tot = TOTF / FPS
rk.mix_bgm(S + 'voice.wav', BGM, tot, S + 'mix_raw.wav')
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', S + 'mix_raw.wav', '-af', 'ebur128', '-f', 'null', '-'],
                   capture_output=True, text=True).stderr
I = float(r.split('Summary:')[1].split('I:')[1].split('LUFS')[0])
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', S + 'mix_raw.wav', '-af', f'volume={-14 - I:.2f}dB,alimiter=limit=0.89:level=false',
        '-ar', '48000', '-c:a', 'pcm_s16le', S + 'mix.wav'])
vk = rk.final(S + 'comp3.mp4', OUT, TOTF, S, audio=S + 'mix.wav')

# ---------------- 썸네일 (영상 첫 컷 문구와 같음) ----------------
# 배경: 첫 컷과 같은 왕커버거 클로즈업. 문구는 위쪽 의자 배경(프로필 격자에서 잘리지 않는 240px 아래)에 크게.
rk.run(['ffmpeg', '-y', '-v', 'error', '-ss', '1.2', '-i', V[1817], '-frames:v', '1', '-vf',
        LOOK[0] + 'scale=1080:1920:flags=lanczos,' + LOOK[1], S + 'thumb_bg2.png'])
bg = Image.open(S + 'thumb_bg2.png').convert('RGBA')
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
for y in range(H):
    d.line([(0, y), (W, y)], fill=(0, 0, 0, int(70 * max(0, 1 - abs(y - 380) / 320))))
bg = Image.alpha_composite(bg, ov)
hook = line_img('패티가 몇 개야?', None, 132)
bg.alpha_composite(hook, ((W - hook.width) // 2, 380 - hook.height // 2))
bg.convert('RGB').save(THUMB, quality=95)
print('total', round(tot, 2), 'kbps', vk, 'MB', round(os.path.getsize(OUT) / 1e6, 1))
