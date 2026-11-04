"""유원옥 리뷰 릴스 편집 스크립트 (자막만, 나레이션·BGM 없음).

필요한 것: 업로드 폴더의 촬영본 12개.
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

def up(tag):
    c = sorted(glob.glob(U + f'*_talkv_{tag}_*.mp4'), key=os.path.getmtime)
    assert c, tag
    return c[-1]
V = {'room': up('dJMcbpbKxNu'), 'soup_a': up('dJMcbpbKxNR'), 'soup_b': up('dJMcbquW0jO'), 'dip': up('dJMcbpbKxOV'),
     'soup_lift': up('dJMcboDTMHW'), 'soup_c': up('dJMcbmF45TP'), 'rib_lift': up('dJMcbmF45Tu'), 'rib_cut': up('dJMcbmF45SV'),
     'rib_steam': up('dJMcbmF45Si'), 'rib_bowl': up('dJMcbmF45RZ'), 'sides': up('dJMcbmF45RG'), 'self': up('dJMcbmF45Ri')}
HDR = {'room', 'soup_a', 'soup_b', 'dip', 'soup_lift', 'soup_c', 'rib_steam'}
# 갈비 드는 장면은 위쪽에 얼굴(턱)이 걸려서 위 20%를 잘라냄
CROP = {'rib_lift': 'crop=864:1536:108:384,scale=1080:1920:flags=lanczos'}
# 안내문 장면: 자막이 '여기 있습니다' 글씨를 가려서 10% 키우고 위로 올림
SIGN = 'scale=1188:2112:flags=lanczos,crop=1080:1920:54:192'

# (영상, 시작, 원본 길이, 화면 길이)
PLAN = [('rib_lift', 1.0, 4.0, 4.0),   # 0 갈비 들어 올리기 (첫 2.6초 썸네일 문구)
        ('rib_cut', 2.5, 8.0, 6.0),    # 1 가위로 자르기
        ('rib_steam', 0.0, 5.0, 3.5),  # 2 김 나는 국물, 지단
        ('soup_a', 2.5, 6.0, 4.0),     # 3 고기 든 국물
        ('soup_lift', 0.0, 3.6, 3.0),  # 4 고기 떠 올리기
        ('dip', 0.0, 3.6, 3.0),        # 5 소스 찍기
        ('sides', 0.0, 3.3, 3.0),      # 6 반찬
        ('self', 0.5, 2.3, 2.3),       # 7 셀프 온육수 따르기
        ('self', 4.25, 1.0, 1.0, SIGN),  # 8 안내문 (흰 벽만 나오는 부분은 뺌)
        ('room', 0.0, 4.4, 3.5),       # 9 매장
        ('rib_bowl', 0.0, 3.9, 3.0)]   # 10 마무리
parts = []; starts = []; t = 0
for i, (k, ss, src, dur, *cr) in enumerate(PLAN):
    out = S + f'seg/{i}.mp4'
    n = rk.clip(V[k], ss, src, dur, out, hdr=k in HDR, crop=cr[0] if cr else CROP.get(k))
    parts.append(out); starts.append(t); t += n
TOTF = t
rk.concat(parts, S + 'cat.txt', S + 'base.mp4')
sec = lambda f: f / FPS

# ---------------- 글자 ----------------
TITLE = ['손목 얼얼하게 만드는 갈비는', '진짜 처음이라 당황함!']
STORE = '유원옥'
# (시작초, 끝초, 1줄, 2줄)  — 장면 1(첫 장면)은 썸네일 문구 라벨로 표시
SUBS = [(sec(starts[1]), sec(starts[2]), '긴 갈비뼈에서 고기가 계속 나와서', '가위질하는 손맛이 미쳤음!'),
        (sec(starts[2]), sec(starts[3]), '김 모락모락 나는 뜨끈한 국물에', '계란 지단이랑 파 고명도 듬뿍!'),
        (sec(starts[3]), sec(starts[4]), '뽀얀 국물 안쪽까지 저어보니까', '속에도 고기가 알차게 들어있음'),
        (sec(starts[4]), sec(starts[5]), '한 숟가락 가득 올려지는 고기 보니까', '마음까지 든든해지는 기분!'),
        (sec(starts[5]), sec(starts[6]), '야들야들한 고기 간장 소스에', '콕 찍어 먹으면 완전 맛있음!'),
        (sec(starts[6]), sec(starts[7]), '김치에 깍두기, 무생채까지', '국물이랑 같이 먹기 좋은 조합!'),
        (sec(starts[7]), sec(starts[9]), '셀프 코너에서 따뜻한 온육수까지', '직접 따라 마실 수 있는 것도 꿀임!'),
        (sec(starts[9]), sec(starts[10]), '원목 테이블이라 깔끔하고 넓어서', '편하게 식사하고 오기 딱이에요'),
        (sec(starts[10]), sec(TOTF), '푸짐한 갈비 생각날 땐', '유원옥 저장해두고 가보세요!')]

TITLE_IMG = subfx.make_title(TITLE, STORE)
SUB_OBJS = [(round(a * FPS), round(b * FPS), subfx.make_sub([l1, l2], 70)) for a, b, l1, l2 in SUBS]
TITLE_F = (0, starts[1])  # 첫 장면 내내 썸네일 문구
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
    if TITLE_F[0] <= fi < TITLE_F[1]:
        subfx.draw_title(fr, TITLE_IMG, fi - TITLE_F[0], TITLE_CY)
    for f0, f1, sub in SUB_OBJS:
        if f0 <= fi < f1:
            subfx.draw_sub(fr, sub, fi - f0, CY)
    enc.stdin.write(fr.convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()
vk = rk.final(S + 'comp.mp4', OUT, TOTF, S)

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
