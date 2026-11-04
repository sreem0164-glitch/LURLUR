"""유원옥 리뷰 릴스 편집 스크립트 (캡컷 TTS + 자막 + BGM).

필요한 것 (업로드 폴더):
- 촬영본 (_talkv_dJMcb*.mp4)
- 캡컷 TTS 영상 copy_B2BE569F-...mov (6개 텍스트 클립: 소스·반찬·셀프·테이블 문장은 뺌)
- BGM copy_E934EEC6-...mov (페어미션 때 받은 음원)
실행: /usr/bin/python3 tools/yuwonok_build.py
"""
import os, glob, sys
from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import subfx, reelkit as rk
from reelkit import W, H, FPS

S = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/m17/'
U = '/root/.claude/uploads/56b70c86-dc21-539d-984f-e6a7533bf099/'
OUT = '/home/user/LURLUR/yuwonok_reel.mp4'
THUMB = '/home/user/LURLUR/yuwonok_thumb.jpg'
os.makedirs(S + 'seg', exist_ok=True)

def up(pat):
    c = sorted(glob.glob(U + pat), key=os.path.getmtime)
    assert c, pat
    return c[-1]
V = {k: up(f'*_talkv_{t}_*.mp4') for k, t in
     {'soup_a': 'dJMcbpbKxNR', 'soup_lift': 'dJMcboDTMHW', 'rib_lift': 'dJMcbmF45Tu', 'rib_cut': 'dJMcbmF45SV',
      'rib_steam': 'dJMcbmF45Si', 'rib_bowl': 'dJMcbmF45RZ'}.items()}
HDR = {'soup_a', 'soup_lift', 'rib_steam'}
# 갈비 드는 장면은 위쪽에 얼굴(턱)이 걸려서 위 20%를 잘라냄
CROP = {'rib_lift': 'crop=864:1536:108:384,scale=1080:1920:flags=lanczos'}
TTS = up('*-copy_B2BE569F-EC79-4B02-B367-CB772FB2BA34.mov')
BGM = up('*-copy_E934EEC6-76BD-467A-8B83-6741C39297DE.mov')

# ---------------- 목소리 ----------------
TITLE = ['손목 얼얼하게 만드는 갈비는', '진짜 처음이라 당황함!']
STORE = '유원옥'
LINES = [tuple(TITLE),
         ('긴 갈비뼈에서 고기가 계속 나와서', '가위질하는 손맛이 미쳤음!'),
         ('김 모락모락 나는 뜨끈한 국물에', '계란 지단이랑 파 고명도 듬뿍!'),
         ('국물 안쪽까지 휘휘 저어보니까', '속에도 고기가 알차게 들어있음'),
         ('한 숟가락 가득 올려지는 고기 보니까', '마음까지 든든해지는 기분!'),
         ('푸짐한 갈비 생각날 땐', '유원옥 저장해두고 가보세요!')]
# 캡컷 텍스트 클립 경계(초): 화면 글자가 바뀌는 시점과 무음 구간으로 확인
BOUND = [0.0, 4.95, 10.55, 15.30, 19.60, 25.45, 30.07]
SCN, TOTAL = rk.tts_layout(TTS, BOUND, LINES, S, speed=1.1, tail=1.3)
F = [round(a * FPS) for a, _, _ in SCN]
TOTF = round(TOTAL * FPS); F.append(TOTF)
for k in range(len(SCN)): print(f'장면 {k+1}: {F[k]/FPS:5.2f}~{F[k+1]/FPS:5.2f}')

# ---------------- 영상 ----------------
# (영상, 원본 시작, 원본 길이, 시작 프레임, 끝 프레임)
STEAM2 = round(1.2 * FPS)
SHOTS = [('rib_lift', 1.0, 4.4, F[0], F[1]),               # 1 갈비 들어 올리기 (썸네일 문구)
         ('rib_cut', 2.5, 5.0, F[1], F[2]),                # 2 긴 갈비뼈 들고 가위로 자르기
         ('rib_steam', 0.0, 4.3, F[2], F[3]),              # 3 김 나는 국물, 지단, 파
         ('soup_a', 2.5, 4.1, F[3], F[4]),                 # 4 국물 저어 보기
         ('soup_lift', 0.0, 5.4, F[4], F[5]),              # 5 고기 한 숟가락
         ('rib_steam', 4.3, 1.25, F[5], F[5] + STEAM2),    # 6 지단·갈비 가까이
         ('rib_bowl', 0.0, 3.9, F[5] + STEAM2, TOTF)]      # 6 끓는 갈비 국물 (마무리)
parts = []
for i, (k, ss, src, f0, f1) in enumerate(SHOTS):
    out = S + f'seg/{i}.mp4'
    rk.clip(V[k], ss, src, (f1 - f0) / FPS, out, hdr=k in HDR, crop=CROP.get(k))
    parts.append(out)
rk.concat(parts, S + 'cat.txt', S + 'base.mp4')

# ---------------- 소리 (목소리 + BGM) ----------------
rk.mix_bgm(S + 'voice.wav', BGM, TOTAL, S + 'mix.wav')

# ---------------- 글자 ----------------
TITLE_IMG = subfx.make_title(TITLE, STORE)
SUB_OBJS = []
for k in range(1, len(LINES)):
    a, b, c = SCN[k]
    sub = subfx.make_sub(list(LINES[k]), 70)
    st = [round(x * FPS) - F[k] for x in rk.word_starts(LINES[k], a, b, c)]
    SUB_OBJS.append((F[k], F[k + 1], sub, st))
CY = 1380
TITLE_CY = int(H * 0.40)

dec, enc = rk.open_io(S + 'base.mp4', S + 'comp.mp4', TOTF)
last = None; thumb_bg = None
for fi in range(TOTF):
    raw = dec.stdout.read(W * H * 3)
    if len(raw) < W * H * 3: raw = last
    last = raw
    fr = Image.frombytes('RGB', (W, H), raw).convert('RGBA')
    if fi == 45: thumb_bg = fr.copy()
    if fi < F[1]:
        subfx.draw_title(fr, TITLE_IMG, fi, TITLE_CY)
    for f0, f1, sub, st in SUB_OBJS:
        if f0 <= fi < f1:
            subfx.draw_sub(fr, sub, fi - f0, CY, st)
    enc.stdin.write(fr.convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()
vk = rk.final(S + 'comp.mp4', OUT, TOTF, S, audio=S + 'mix.wav')

# ---------------- 썸네일 (영상 첫 장면 문구와 동일) ----------------
bg = ImageEnhance.Brightness(thumb_bg.convert('RGB')).enhance(1.02).convert('RGBA')
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
for y in range(H):
    a = int(70 * max(0, 1 - abs(y - TITLE_CY) / 600))
    d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
bg = Image.alpha_composite(bg, ov)
bg.alpha_composite(TITLE_IMG, (0, int(TITLE_CY - TITLE_IMG.height / 2)))
bg.convert('RGB').save(THUMB, quality=95)
print('total', TOTF / FPS, 'video kbps', vk, 'size MB', round(os.path.getsize(OUT) / 1e6, 1))
