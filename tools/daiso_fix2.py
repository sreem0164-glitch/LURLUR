"""다이소 PDRN(4차 개인미션) 2차 수정본 — 카페에 올린 완성본(BGM·아웃트로 포함)을 직접 고침.

운영 사무국 피드백(2026-10-30)
1. 나레이션이 BGM에 약간 묻힘 → 목소리만 있는 원래 편집본으로 완성본에서 BGM을 꺼내, 목소리 1.0 + BGM 0.6배로 다시 섞음
   (그 파일이 없으면 목소리 대역 EQ만)
2. 10초 스마트렌즈 진입 장면이 너무 빠름 → 네이버 홈 화면을 0.4초 → 약 1.07초로 늘리고, 렌즈 아이콘에 동그라미·화살표·확대 표시
   (전체 길이와 목소리 타이밍은 그대로: 뒤쪽의 빠르게 지나가던 카메라 화면 0.67초를 대신 줄임)
3. 34.5초부터 캡컷 아웃트로 → 34.5초에서 자름 (끝 0.3초 소리 줄임)

필요한 것: 업로드 폴더의 _talkv_dJMcbqhrByw_*.mp4 (카페에 올린 완성본, 37초),
         m4_daiso_pdrn_send.mp4 (BGM 넣기 전 목소리만 있는 편집본)
실행: /usr/bin/python3 -I tools/daiso_fix2.py
"""
import os, sys, glob, math, subprocess
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reelkit as rk
from reelkit import W, H, FPS

S = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/m18/'
U = '/root/.claude/uploads/56b70c86-dc21-539d-984f-e6a7533bf099/'
OUT = '/home/user/LURLUR/daiso_pdrn_v2.mp4'
os.makedirs(S, exist_ok=True)
SRC = sorted(glob.glob(U + '*_talkv_dJMcbqhrByw_*.mp4'), key=os.path.getmtime)[-1]

END = 1035                 # 34.5초: 여기서부터 캡컷 아웃트로
HOME0 = 304                # 네이버 홈 화면 시작 (10.133초)
POP_END = 308              # 자막이 다 나타난 프레임
FREEZE = 309               # 멈춰 둘 홈 화면 프레임
HL_END = 336               # 홈 화면 보강 끝 (이 프레임부터 렌즈 여는 화면)
OPEN = [316, 317, 318]     # 렌즈 열리는 원래 프레임
RESUME = 339               # 이후는 원래 프레임 그대로
ICON = (806, 308)          # 스마트렌즈 아이콘 중심
RED = (255, 48, 48)

def ease(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def overlay(base, k):
    """k: 보강 구간 안의 프레임 번호(0부터). 2배 크기로 그리고 줄여서 테두리를 매끄럽게."""
    SS = 2
    lay = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy = ICON[0] * SS, ICON[1] * SS
    # 1) 확대 표시: 아이콘 주변을 2.6배로 키워 왼쪽 아래에 보여 줌 (k 4~10 동안 서서히 나타남)
    e = ease((k - 4) / 6)
    mag = None
    if e > 0:
        R = int(150 * (0.85 + 0.15 * e)); zoom = 2.6
        src = base.crop((int(ICON[0] - R / zoom), int(ICON[1] - R / zoom), int(ICON[0] + R / zoom), int(ICON[1] + R / zoom)))
        src = src.resize((2 * R, 2 * R), Image.LANCZOS).convert('RGBA')
        m = Image.new('L', (2 * R, 2 * R), 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * R - 1, 2 * R - 1), fill=int(255 * e))
        mag = (src, m, R, (330, 640))
    # 2) 아이콘 동그라미: k 0~7 동안 한 바퀴 그려짐
    a = ease(k / 7)
    if a > 0:
        r = 72 * SS
        d.arc((cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6), -90, -90 + 360 * a, fill=(255, 255, 255, 230), width=13 * SS)
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * a, fill=RED + (255,), width=9 * SS)
    # 3) 화살표: 확대 표시 쪽에서 아이콘 쪽으로 (k 6~12 동안 뻗어 나감, 이후 살짝 앞뒤로 움직임)
    g = ease((k - 6) / 6)
    if g > 0:
        x0, y0 = 470 * SS, 545 * SS; x1, y1 = 742 * SS, 362 * SS
        bob = 0 if k < 12 else 6 * SS * math.sin((k - 12) / 30 * 2 * math.pi * 1.6)
        ux, uy = (x1 - x0), (y1 - y0); L = math.hypot(ux, uy); ux, uy = ux / L, uy / L
        ex, ey = x0 + (x1 - x0) * g + ux * bob, y0 + (y1 - y0) * g + uy * bob
        for col, wd in (((255, 255, 255, 230), 22 * SS), (RED + (255,), 12 * SS)):
            d.line((x0, y0, ex - ux * 20 * SS, ey - uy * 20 * SS), fill=col, width=wd)
            hl, hw = 46 * SS + (wd - 12 * SS), 30 * SS + (wd - 12 * SS) // 2
            px, py = -uy, ux
            d.polygon([(ex + ux * (wd - 12 * SS) / 2, ey + uy * (wd - 12 * SS) / 2),
                       (ex - ux * hl + px * hw, ey - uy * hl + py * hw),
                       (ex - ux * hl - px * hw, ey - uy * hl - py * hw)], fill=col)
    # 4) 누르는 표시: k 20 이후 아이콘에서 퍼지는 원
    if k >= 20:
        t = (k - 20) / 8; rr = (40 + 70 * ease(t)) * SS; al = int(200 * (1 - min(1, t)))
        if al > 0:
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(255, 255, 255, al), width=6 * SS)
    lay = lay.resize((W, H), Image.LANCZOS)
    fr = base.convert('RGBA')
    if mag:
        src, m, R, (mx, my) = mag
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse((mx - R - 4, my - R + 8, mx + R + 4, my + R + 16), fill=(0, 0, 0, int(90 * e)))
        fr = Image.alpha_composite(fr, sh.filter(ImageFilter.GaussianBlur(12)))
        ring = Image.new('RGBA', (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
        rd.ellipse((mx - R - 8, my - R - 8, mx + R + 8, my + R + 8), fill=(255, 255, 255, int(255 * e)))
        fr = Image.alpha_composite(fr, ring)
        fr.paste(src, (mx - R, my - R), m)
        ring2 = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ring2).ellipse((mx - R, my - R, mx + R, my + R), outline=RED + (int(255 * e),), width=6)
        fr = Image.alpha_composite(fr, ring2)
    return Image.alpha_composite(fr, lay).convert('RGB')

# ---------------- 영상 ----------------
# 필요한 원래 프레임(멈춰 둘 홈 화면, 렌즈 여는 화면)을 먼저 따로 뽑아 둠
KEEP = [FREEZE] + OPEN
sel = '+'.join(f'eq(n\\,{n})' for n in KEEP)
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', SRC, '-vf', f"select='{sel}'", '-vsync', '0', S + 'keep_%d.png'])
KF = {n: Image.open(S + f'keep_{j + 1}.png').convert('RGB') for j, n in enumerate(KEEP)}
base = KF[FREEZE]
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-frames:v', str(END), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30',
                        '-i', '-', '-frames:v', str(END)] + rk.MID + [S + 'comp.mp4'], stdin=subprocess.PIPE)
for i in range(END):
    raw = dec.stdout.read(W * H * 3)
    if POP_END <= i < HL_END:
        out = overlay(base, i - POP_END).tobytes()
    elif HL_END <= i < RESUME:
        out = KF[OPEN[i - HL_END]].tobytes()
    else:
        out = raw
    enc.stdin.write(out)
    if i in (POP_END + 4, POP_END + 14, HL_END - 4):
        Image.frombytes('RGB', (W, H), out).save(S + f'chk_{i}.png')
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()

# ---------------- 소리 ----------------
dur = END / FPS
VOICE = sorted(glob.glob(U + '*-m4_daiso_pdrn_send.mp4'), key=os.path.getmtime)
if VOICE:
    # 목소리만 있는 원래 편집본(m4_daiso_pdrn_send.mp4)이 있으면:
    # 완성본 = g×목소리 + BGM 이므로 BGM = 완성본 − g×목소리 로 BGM만 꺼낸 뒤,
    # 목소리는 원래 크기(1.0)로, BGM은 0.6배(약 −4.4dB)로 다시 섞음 → 목소리가 BGM보다 약 5.6dB 더 또렷해짐.
    import wave, numpy as np
    rk.run(['ffmpeg', '-y', '-v', 'error', '-i', SRC, '-vn', '-ac', '2', '-ar', '48000', '-c:a', 'pcm_s16le', S + 'mix_in.wav'])
    rk.run(['ffmpeg', '-y', '-v', 'error', '-i', VOICE[-1], '-vn', '-ac', '2', '-ar', '48000', '-c:a', 'pcm_s16le', S + 'voice_in.wav'])
    def rd(p):
        w = wave.open(p); return np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32768
    Fm, Vv = rd(S + 'mix_in.wav'), rd(S + 'voice_in.wav')
    n = int(round(dur * 48000)); Fm = Fm[:n]
    if len(Vv) < n: Vv = np.vstack([Vv, np.zeros((n - len(Vv), 2))])
    Vv = Vv[:n]
    g = float((Fm * Vv).sum() / (Vv * Vv).sum())          # 완성본 속 목소리 크기 (측정값 약 0.87)
    bgm = Fm - g * Vv
    out = 1.0 * Vv + 0.6 * bgm
    w = wave.open(S + 'remix.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(48000)
    w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    print('voice gain in mix', round(g, 3))
    rk.run(['ffmpeg', '-y', '-v', 'error', '-i', S + 'remix.wav', '-af',
            f'volume=3dB,afade=t=out:st={dur - 0.3:.3f}:d=0.3,alimiter=limit=0.89:level=false',
            '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', S + 'audio_fix.wav'])
else:
    # 목소리 파일이 없으면: 목소리 대역(약 2.8kHz)을 살리고 BGM 저음(킥·베이스)을 줄이는 EQ만
    rk.run(['ffmpeg', '-y', '-v', 'error', '-i', SRC, '-vn', '-t', f'{dur:.3f}', '-af',
            'volume=2dB,equalizer=f=80:t=q:w=1.0:g=-6,equalizer=f=160:t=q:w=1.0:g=-2,'
            'equalizer=f=2800:t=q:w=1.2:g=3,equalizer=f=9000:t=q:w=1.0:g=-2,'
            f'afade=t=out:st={dur - 0.3:.3f}:d=0.3,alimiter=limit=0.89:level=false',
            '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', S + 'audio_fix.wav'])
vk = rk.final(S + 'comp.mp4', OUT, END, S, audio=S + 'audio_fix.wav')
print('total', END / FPS, 'video kbps', vk, 'size MB', round(os.path.getsize(OUT) / 1e6, 1))
