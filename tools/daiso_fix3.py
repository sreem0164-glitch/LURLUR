"""다이소 PDRN(4차 개인미션) 2차 수정본 v3 — 새로 녹화한 진입 화면(ScreenRecording_11-06-2026_12-13-35_1.mp4)을 넣음.

v2에서 바뀐 것
- 스마트렌즈 장면(10.1초~): 새 녹화의 선명한 네이버 홈 화면 1.5초(스마트렌즈 아이콘에 동그라미·화살표·확대·누르는 표시)
  → 원래 있던 렌즈 열림·제품 비추기 화면은 지우지 않고 그대로 (v2에서 줄였던 0.67초도 되살림)
  → 첫 줄 목소리 뒤에 1.1초 쉼을 넣어, 둘째 줄("제품 정보에 쇼핑까지 바로!")이 결과 화면과 같이 나오게 함
- AI탭 장면 시작(14.5초~): 새 녹화의 'AI 버튼 누르기 → AI탭 화면' 1.7초를 넣음 (AI 버튼에 동그라미·화살표·누르는 표시)
- 목소리: 원래 편집본 목소리에 위 두 곳만 쉼을 넣음. BGM: 완성본에서 꺼낸 BGM을 끊김 없이 전체 길이에 맞게 약 6% 느리게 늘림
- 목소리 1.0 + BGM 0.6배로 섞음 (v2와 같음), 캡컷 아웃트로 없음
필요한 것 (업로드 폴더): 카페에 올린 완성본 _talkv_dJMcbqhrByw_*.mp4, 목소리만 있는 m4_daiso_pdrn_send.mp4,
                       새 녹화 ScreenRecording_11-06-2026_12-13-35_1.mp4
실행: /usr/bin/python3 -I tools/daiso_fix3.py
"""
import os, sys, glob, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reelkit as rk
from reelkit import W, H, FPS

S = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/m19/'
U = '/root/.claude/uploads/56b70c86-dc21-539d-984f-e6a7533bf099/'
OUT = '/home/user/LURLUR/daiso_pdrn_v3.mp4'
os.makedirs(S, exist_ok=True)
up = lambda p: sorted(glob.glob(U + p), key=os.path.getmtime)[-1]
SRC = up('*_talkv_dJMcbqhrByw_*.mp4')
VOICE = up('*-m4_daiso_pdrn_send.mp4')
REC = up('*-ScreenRecording_11-06-2026_12-13-35_1.mp4')
FONT = S + '../fonts_dl/x_pretendard/package/dist/public/static/Pretendard-Black.otf'
SR = 48000

# ---------------- 원래 영상의 시점(프레임, 30fps) ----------------
END = 1035          # 34.5초부터 캡컷 아웃트로
A0 = 304            # 스마트렌즈 장면 시작 (네이버 홈)
CAM0, CAM1 = 316, 357   # 렌즈 열림 ~ 둘째 줄 자막 직전 (이 화면은 그대로 둠)
B0 = 435            # AI탭 장면 시작
HA = 45             # 새 홈 화면 길이 (1.5초)
HB1, HB2 = 24, 27   # AI 버튼 홈 화면 0.8초 + AI탭 화면 0.9초
SHIFT_A = HA + (CAM1 - CAM0) - (CAM1 - A0)   # 33프레임 = 1.1초
SHIFT_B = HB1 + HB2                          # 51프레임 = 1.7초
TOTF = END + SHIFT_A + SHIFT_B
VA_T, VB_T = 11.80, 14.45   # 목소리에 쉼을 넣을 시각 (원래 영상 기준, 말 사이 빈 곳)
RED = (255, 48, 48)

# ---------------- 새 녹화 프레임 (1206x2622 60fps → 1080x1920 30fps, 위쪽 상태바 일부 잘라냄) ----------------
REC_VF = 'fps=30,scale=1080:-2:flags=lanczos,crop=1080:1920:0:150,setsar=1'
def rec_frames(ss, n):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{ss:.3f}', '-i', REC, '-vf', REC_VF, '-frames:v', str(n),
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    out = []
    for _ in range(n):
        b = p.stdout.read(W * H * 3)
        out.append(Image.frombytes('RGB', (W, H), b) if len(b) == W * H * 3 else out[-1])
    p.stdout.close(); p.wait(); return out
R_LENS = rec_frames(0.0, HA)     # 홈 화면 (스마트렌즈 강조용)
R_AI1 = rec_frames(1.37, HB1)    # 홈 화면 (AI 버튼 강조용, 녹화 2.13초까지가 홈 화면)
R_AI2 = rec_frames(2.167, HB2)   # AI 버튼 누른 뒤 (홈 화면이 사라진 프레임부터) AI탭 화면
LENS_C = (730, 188)              # 스마트렌즈 아이콘 중심 (새 녹화, 위 좌표계)
AI_C = (895, 188)                # AI 버튼 중심
# 홈 화면 피드(연예 기사 광고·인물 사진 등)는 흐리게: 검색창·배너 아래부터
FEED_Y = 330
def blur_feed(im):
    im = im.copy(); box = (0, FEED_Y, W, H)
    im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(28)), box); return im
R_LENS = [blur_feed(f) for f in R_LENS]; R_AI1 = [blur_feed(f) for f in R_AI1]
R_LENS[20].save(S + 'chk_home.png')

def ease(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def highlight(fr, k, c, rx, ry, k_circle, k_arrow, k_tap, mag=None, arrow_from=None):
    """동그라미(그려지며 나타남) + 화살표 + 누르는 표시, 필요하면 확대 표시. 2배로 그려서 줄임."""
    SS = 2; lay = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy = c[0] * SS, c[1] * SS
    base = fr.convert('RGBA')
    if mag is not None:
        e = ease((k - mag[3]) / 6)
        if e > 0:
            (mx, my), R0, zoom = mag[0], mag[1], mag[2]; R = int(R0 * (0.85 + 0.15 * e))
            src = fr.crop((int(c[0] - R / zoom), int(c[1] - R / zoom), int(c[0] + R / zoom), int(c[1] + R / zoom)))
            src = src.resize((2 * R, 2 * R), Image.LANCZOS).convert('RGBA')
            m = Image.new('L', (2 * R, 2 * R), 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * R - 1, 2 * R - 1), fill=int(255 * e))
            sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse((mx - R - 4, my - R + 8, mx + R + 4, my + R + 16), fill=(0, 0, 0, int(90 * e)))
            base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(12)))
            ring = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse((mx - R - 8, my - R - 8, mx + R + 8, my + R + 8), fill=(255, 255, 255, int(255 * e)))
            base = Image.alpha_composite(base, ring); base.paste(src, (mx - R, my - R), m)
            ring2 = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ring2).ellipse((mx - R, my - R, mx + R, my + R), outline=RED + (int(255 * e),), width=6)
            base = Image.alpha_composite(base, ring2)
    a = ease((k - k_circle) / 7)
    if a > 0:
        bb = (cx - rx * SS, cy - ry * SS, cx + rx * SS, cy + ry * SS)
        d.arc((bb[0] - 6, bb[1] - 6, bb[2] + 6, bb[3] + 6), -90, -90 + 360 * a, fill=(255, 255, 255, 230), width=13 * SS)
        d.arc(bb, -90, -90 + 360 * a, fill=RED + (255,), width=9 * SS)
    g = ease((k - k_arrow) / 6)
    if g > 0 and arrow_from:
        x0, y0 = arrow_from[0] * SS, arrow_from[1] * SS
        ux, uy = cx - x0, cy - y0; L = math.hypot(ux, uy); ux, uy = ux / L, uy / L
        x1, y1 = cx - ux * (max(rx, ry) + 14) * SS, cy - uy * (max(rx, ry) + 14) * SS
        bob = 0 if k < k_arrow + 6 else 6 * SS * math.sin((k - k_arrow - 6) / 30 * 2 * math.pi * 1.6)
        ex, ey = x0 + (x1 - x0) * g + ux * bob, y0 + (y1 - y0) * g + uy * bob
        for col, wd in (((255, 255, 255, 230), 22 * SS), (RED + (255,), 12 * SS)):
            d.line((x0, y0, ex - ux * 20 * SS, ey - uy * 20 * SS), fill=col, width=wd)
            ex2 = (wd - 12 * SS); hl, hw = 46 * SS + ex2, 30 * SS + ex2 // 2; px, py = -uy, ux
            d.polygon([(ex + ux * ex2 / 2, ey + uy * ex2 / 2), (ex - ux * hl + px * hw, ey - uy * hl + py * hw),
                       (ex - ux * hl - px * hw, ey - uy * hl - py * hw)], fill=col)
    if k >= k_tap:
        t = (k - k_tap) / 8; rr = (30 + 60 * ease(t)) * SS; al = int(210 * (1 - min(1, t)))
        if al > 0:
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(255, 255, 255, al), width=6 * SS)
            d.ellipse((cx - rr * 0.6, cy - rr * 0.6, cx + rr * 0.6, cy + rr * 0.6), fill=(255, 255, 255, al // 3))
    return Image.alpha_composite(base, lay.resize((W, H), Image.LANCZOS)).convert('RGB')

# ---------------- 스마트렌즈 장면 첫 줄 자막 (원래 영상과 같은 스타일: 흰 글자+검정 테두리, '스마트렌즈' 초록, 튀어나오며 등장) ----------------
G = (3, 199, 90); CY = 1360
def render_line1(size=74):
    fn = ImageFont.truetype(FONT, size); fe = ImageFont.truetype(FONT, int(size * 1.12))
    parts = [('스마트렌즈', G), ('로', None), (' ', None), ('찍으니까', None)]
    wd = sum((fe if c else fn).getlength(t) for t, c in parts)
    lh = int(size * 1.32); stroke = max(6, size // 9)
    img = Image.new('RGBA', (W, lh + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(img); x = (W - wd) / 2; yc = 20 + lh / 2
    for t, c in parts:
        f = fe if c else fn
        if t.strip(): d.text((x, yc), t, font=f, fill=c or (255, 255, 255), stroke_width=stroke + (2 if c else 0), stroke_fill=(0, 0, 0), anchor='lm')
        x += f.getlength(t)
    return img
SUB1 = render_line1()
def pop(i):
    if i >= 6: return 1.0
    x = i / 6; c = 1.9; return 0.55 + 0.45 * (1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2)
def with_sub(fr, k):
    sc = pop(k); im = SUB1 if sc == 1.0 else SUB1.resize((max(1, int(SUB1.width * sc)), max(1, int(SUB1.height * sc))), Image.BILINEAR)
    f = fr.convert('RGBA'); f.alpha_composite(im, (int((W - im.width) / 2), int(CY - im.height / 2))); return f.convert('RGB')

# ---------------- 영상 이어 붙이기 ----------------
CAMF = {}
sel = '+'.join(f'eq(n\\,{n})' for n in range(CAM0, CAM1))
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', SRC, '-vf', f"select='{sel}'", '-vsync', '0', S + 'cam_%03d.png'])
CAMF = [Image.open(S + f'cam_{j + 1:03d}.png').convert('RGB') for j in range(CAM1 - CAM0)]

dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-frames:v', str(END), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30',
                        '-i', '-', '-frames:v', str(TOTF)] + rk.MID + [S + 'comp.mp4'], stdin=subprocess.PIPE)
nout = 0
def put(img, tag=None):
    global nout
    enc.stdin.write(img if isinstance(img, bytes) else img.tobytes())
    if tag: Image.frombytes('RGB', (W, H), img) .save(S + f'chk_{tag}.png') if isinstance(img, bytes) else img.save(S + f'chk_{tag}.png')
    nout += 1
for i in range(END):
    raw = dec.stdout.read(W * H * 3)
    if i == A0:
        for k in range(HA):   # 새 홈 화면 + 스마트렌즈 강조 + 첫 줄 자막
            fr = highlight(R_LENS[k], k, LENS_C, 62, 62, k_circle=4, k_arrow=10, k_tap=34,
                           mag=((330, 560), 150, 2.4, 8), arrow_from=(452, 472))
            put(with_sub(fr, k), 'lens' if k in (16, 38) and k == 16 else ('lens_tap' if k == 38 else None))
        for f in CAMF: put(f)   # 원래 렌즈 열림·제품 비추기 화면 그대로
    if A0 <= i < CAM1:
        continue                # 위에서 대신 넣음
    if i == B0:
        for k in range(HB1):    # AI 버튼 강조
            put(highlight(R_AI1[k], k, AI_C, 118, 70, k_circle=0, k_arrow=4, k_tap=15, arrow_from=(620, 480)),
                'ai' if k == 12 else None)
        for f in R_AI2: put(f)
    put(raw)
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()
assert nout == TOTF, (nout, TOTF)

# ---------------- 소리 ----------------
def rd(p):
    w = wave.open(p); return np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32768
def wr(p, x):
    w = wave.open(p, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', SRC, '-vn', '-ac', '2', '-ar', str(SR), '-c:a', 'pcm_s16le', S + 'mix_in.wav'])
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', VOICE, '-vn', '-ac', '2', '-ar', str(SR), '-c:a', 'pcm_s16le', S + 'voice_in.wav'])
Fm, Vv = rd(S + 'mix_in.wav'), rd(S + 'voice_in.wav')
n0 = len(Vv)
g = float((Fm[:n0] * Vv).sum() / (Vv * Vv).sum())      # 완성본 속 목소리 크기 (약 0.87)
Vpad = np.vstack([Vv, np.zeros((max(0, len(Fm) - n0), 2))])[:len(Fm)]
bgm = (Fm - g * Vpad)[:int(35.0 * SR)]                  # 완성본의 BGM은 35.0초까지 (34.5초 이후는 목소리 없음)
tot = TOTF / FPS
# 목소리: 두 곳에 쉼 넣기
a, b = int(VA_T * SR), int(VB_T * SR)
voice = np.concatenate([Vv[:a], np.zeros((int(round(SHIFT_A / FPS * SR)), 2)), Vv[a:b],
                        np.zeros((int(round(SHIFT_B / FPS * SR)), 2)), Vv[b:]])
voice = np.vstack([voice, np.zeros((max(0, int(tot * SR) - len(voice)), 2))])[:int(tot * SR)]
wr(S + 'bgm_raw.wav', bgm)
rate = (len(bgm) / SR) / tot
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', S + 'bgm_raw.wav', '-af', f'atempo={rate:.5f}', '-ar', str(SR), '-ac', '2',
        '-c:a', 'pcm_s16le', S + 'bgm_long.wav'])
bl = rd(S + 'bgm_long.wav'); bl = np.vstack([bl, np.zeros((max(0, len(voice) - len(bl)), 2))])[:len(voice)]
fo = int(0.8 * SR); bl[-fo:] *= np.linspace(1, 0, fo)[:, None]
wr(S + 'remix.wav', voice * 1.0 + bl * 0.6)
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', S + 'remix.wav', '-af',
        f'volume=3dB,afade=t=out:st={tot - 0.3:.3f}:d=0.3,alimiter=limit=0.89:level=false',
        '-ar', str(SR), '-ac', '2', '-c:a', 'pcm_s16le', S + 'audio_fix.wav'])
vk = rk.final(S + 'comp.mp4', OUT, TOTF, S, audio=S + 'audio_fix.wav')
print('voice gain', round(g, 3), 'bgm tempo', round(rate, 4), 'total', round(tot, 2), 'kbps', vk,
      'MB', round(os.path.getsize(OUT) / 1e6, 1))
