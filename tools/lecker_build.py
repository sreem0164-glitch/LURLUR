"""레커버거 둔산점 협찬 릴스 (디너의여왕 캠페인) — 자막 + BGM, 나레이션 없음.

참고 릴스 방식: 1~1.5초마다 컷, 컷마다 짧은 한 줄 자막(흰 글자+검정 테두리, 강조는 노란색 1~2곳만)
자막은 컷마다 음식·간판을 가리지 않는 빈 곳에 둠.
첫 컷: 패티 많은 버거(왕커버거) 클로즈업 + "패티가 몇 개야?" (= 썸네일 문구)
캠페인 필수: 30~50초, 영상에 썸네일 문구, 초반에 '대전 배달 맛집으로 이미 소문남'(둘째 컷), 음료 무한리필(알림받기·매장 식사),
            수제버거인데 종류 다양, 특제소스·수제패티 풍미. 메뉴 이름·가격은 넣지 않음.
필요한 것: 업로드 폴더의 IMG_1812~1822.mov (4K HDR), BGM copy_E934EEC6-...mov
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
os.makedirs(S + 'seg2', exist_ok=True)
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

# (촬영본, 시작, 길이, 자막(줄 또는 줄 묶음), 노란 강조, 특수, 자막 가운데 y, 글자 크기)
# 자막 y: 화면 맨 위 300px 안과 1480px 아래는 릴스 화면의 버튼·글자와 겹쳐서 쓰지 않음
SHOTS = [(1817, 0.4, 2.0, '패티가 몇 개야?', None, 'hook', 340, 118),                  # 왕커버거 클로즈업 (썸네일 문구)
         (1813, 0.3, 1.8, ('대전에서 이미', '배달 맛집으로 소문난 곳'), None, None, 930, 84),  # 캠페인 필수 (초반)
         (1814, 1.4, 1.6, '매장 들어가자마자', None, None, 740, 84),
         (1812, 0.0, 1.4, '미국 다이너 감성 그대로', None, None, 560, 84),
         (1812, 4.2, 1.4, '수제버거인데', None, None, 760, 84),
         (1812, 5.6, 1.2, '버거 종류도 다양하고', None, None, 760, 84),
         (1812, 6.8, 1.1, '알림받기 + 매장 식사면', None, None, 1330, 84),
         (1812, 7.9, 0.8, '음료 무한리필!', '무한리필!', 'drink', 1330, 84),
         (1816, 2.0, 1.5, '둘이서 시킨 한 상', None, None, 310, 84),
         (1817, 2.4, 1.5, '수제 패티가 겹겹이', None, None, 310, 84),
         (1817, 3.9, 1.5, '치즈까지 녹아내림', None, None, 310, 84),
         (1819, 4.3, 1.5, '바삭한 치킨버거까지', None, None, 1420, 84),
         (1820, 4.2, 1.4, '닭강정까지', None, 'chin', 330, 84),
         (1821, 0.0, 1.7, '한 입 베어 물면', None, None, 310, 84),
         (1821, 1.7, 1.7, '특제소스랑 수제패티', None, None, 310, 84),
         (1822, 0.0, 1.6, '풍미가 꽉 차요', '풍미', None, 330, 84),
         (1822, 2.3, 1.3, '속이 꽉 찬 단면', None, None, 310, 84),
         (1818, 0.0, 1.7, '배달로만 먹기엔', None, None, 320, 84),
         (1818, 1.7, 1.7, '아까운 비주얼', None, None, 320, 84),
         (1813, 2.85, 2.4, ('둔산동 레커버거', '저장해두고 가보세요!'), None, 'end', 940, 80)]  # 네온 간판 아래 흰 벽

parts = []; starts = []; t = 0
for i, (n, ss, d, *_r) in enumerate(SHOTS):
    out = S + f'seg2/{i}.mp4'
    if not (os.environ.get('REUSE_BASE') and os.path.exists(out)):
        rk.clip(V[n], ss, d, d, out, hdr=True, crop=CHIN if _r[2] == 'chin' else None, look=LOOK)
    parts.append(out); starts.append(t); t += round(d * FPS)
TOTF = t; starts.append(TOTF)
rk.concat(parts, S + 'cat2.txt', S + 'base2.mp4')
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
    SUBS.append((starts[i], starts[i + 1], imgs, sy))
DRINK = [i for i, s in enumerate(SHOTS) if s[5] == 'drink'][0]

def drink_circle(fr, k, t_src):
    """'SELF DRINK' 간판에 빨간 동그라미. 카메라가 움직여서 간판 위치를 시간에 맞춰 옮김 (7.6초 x=230 → 8.75초 x=416)."""
    cx = 230 + (t_src - 7.6) / 1.15 * 186; cy = 584; rx, ry = 200, 64
    a = min(1.0, (k + 1) / 5)
    lay = Image.new('RGBA', (W * 2, H * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    bb = ((cx - rx) * 2, (cy - ry) * 2, (cx + rx) * 2, (cy + ry) * 2)
    d.arc((bb[0] - 6, bb[1] - 6, bb[2] + 6, bb[3] + 6), -100, -100 + 360 * a, fill=(255, 255, 255, 220), width=24)
    d.arc(bb, -100, -100 + 360 * a, fill=(255, 48, 48, 255), width=16)
    fr.alpha_composite(lay.resize((W, H), Image.LANCZOS))

CHK = {starts[0] + 20, starts[1] + 20, starts[DRINK] + 15, starts[12] + 20, TOTF - 10}
dec, enc = rk.open_io(S + 'base2.mp4', S + 'comp2.mp4', TOTF)
last = None
for fi in range(TOTF):
    raw = dec.stdout.read(W * H * 3)
    if len(raw) < W * H * 3: raw = last
    last = raw
    fr = Image.frombytes('RGB', (W, H), raw).convert('RGBA')
    if starts[DRINK] <= fi < starts[DRINK + 1]:
        k = fi - starts[DRINK]; drink_circle(fr, k, SHOTS[DRINK][1] + k / FPS)
    for f0, f1, imgs, sy in SUBS:
        if f0 <= fi < f1:
            al = min(1.0, (fi - f0 + 1) / 3)     # 튀어나오는 효과 없이 살짝 나타나기만
            y = sy - sum(im.height for im in imgs) // 2 + 20 * (len(imgs) - 1)
            for im in imgs:
                if al < 1:
                    im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * al)))
                fr.alpha_composite(im, ((W - im.width) // 2, y)); y += im.height - 40
    if fi in CHK:
        fr.convert('RGB').save(S + f'chk2_{fi}.png')
    enc.stdin.write(fr.convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()

# ---------------- BGM (나레이션 없음) ----------------
tot = TOTF / FPS
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', BGM, '-vn', '-t', f'{tot:.3f}', '-af',
        f'aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.3,afade=t=out:st={tot - 1.5:.3f}:d=1.5',
        '-ar', '48000', '-c:a', 'pcm_s16le', S + 'bgm_raw.wav'])
# 음량을 -14 LUFS 정도로 일정하게 (음악 모양은 그대로, 전체 크기만 맞춤)
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', S + 'bgm_raw.wav', '-af', 'ebur128', '-f', 'null', '-'],
                   capture_output=True, text=True).stderr
I = float(r.split('Summary:')[1].split('I:')[1].split('LUFS')[0])
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', S + 'bgm_raw.wav', '-af', f'volume={-14 - I:.2f}dB,alimiter=limit=0.89:level=false',
        '-ar', '48000', '-c:a', 'pcm_s16le', S + 'bgm.wav'])
vk = rk.final(S + 'comp2.mp4', OUT, TOTF, S, audio=S + 'bgm.wav')

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
