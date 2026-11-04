"""파스쿠찌 대전갤러리아점 협찬 릴스 편집 스크립트 (자막만, 나레이션·BGM 없음).

필요한 것: 업로드 폴더의 촬영본 5개(_talkv_dJMcboDTM*.mp4).
실행: /usr/bin/python3 tools/pascucci_build.py
"""
import os, glob, sys
from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import subfx, reelkit as rk
from reelkit import W, H, FPS

S = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/m16/'
U = '/root/.claude/uploads/56b70c86-dc21-539d-984f-e6a7533bf099/'
OUT = '/home/user/LURLUR/pascucci_reel.mp4'
THUMB = '/home/user/LURLUR/pascucci_thumb.jpg'
os.makedirs(S + 'seg', exist_ok=True)

def up(tag):
    c = sorted(glob.glob(U + f'*_talkv_{tag}_*.mp4'), key=os.path.getmtime)
    assert c, tag
    return c[-1]
V = {'tree': up('dJMcboDTMCw'), 'table': up('dJMcboDTMDl'), 'cake': up('dJMcboDTMDK'),
     'hall1': up('dJMcboDTMEb'), 'hall2': up('dJMcboDTMEr')}
HDR = {'table', 'hall1'}

# (영상, 시작, 원본 길이, 화면 길이)
PLAN = [('hall1', 0.0, 4.6, 4.0),     # 0 그림 걸린 벽 (썸네일 문구 '미술관이 아니라 카페?')
        ('hall2', 2.4, 3.0, 3.0),     # 1 그림 벽 (다른 각도)
        ('hall1', 4.6, 5.3, 4.4),     # 2 계단, 식물
        ('hall2', 0.0, 1.3, 1.2),     # 3 부스 좌석
        ('hall2', 5.4, 6.9, 5.5),     # 4 넓은 홀
        ('table', 0.0, 5.3, 5.0),     # 5 음료, 케이크
        ('cake', 0.0, 2.5, 2.5),      # 6 케이크 클로즈업
        ('tree', 0.0, 9.1, 7.0)]      # 7 크리스마스 트리 (마무리)
parts = []; starts = []; t = 0
for i, (k, ss, src, dur) in enumerate(PLAN):
    out = S + f'seg/{i}.mp4'; n = rk.clip(V[k], ss, src, dur, out, hdr=k in HDR); parts.append(out); starts.append(t); t += n
TOTF = t
rk.concat(parts, S + 'cat.txt', S + 'base.mp4')
sec = lambda f: f / FPS

# ---------------- 글자 ----------------
TITLE = ['아니 여기가 미술관이 아니라', '둔산동 카페라고요?!']
STORE = '파스쿠찌 대전갤러리아점'
# (시작초, 끝초, 1줄, 2줄)  — 장면 1(첫 장면)은 썸네일 문구 라벨로 표시
SUBS = [(sec(starts[1]), sec(starts[2]), '안쪽으로 들어가면 그림 액자 가득해서', '진짜 미술관 온 것 같은 기분임!'),
        (sec(starts[2]), sec(starts[3]), '세련된 계단 따라 이어지는 공간도', '초록 식물 덕분에 분위기 깔끔함'),
        (sec(starts[3]), sec(starts[5]), '홀도 완전 넓어서 부스석에 앉아', '친구들이랑 수다 떨기 딱 좋음!'),
        (sec(starts[5]), sec(starts[6]) - 1.5, '음료 두 잔에 케이크 두 조각 올려주니', '디저트 차림도 완전 알참!'),
        (sec(starts[6]) - 1.5, sec(starts[7]), '가까이서 보니까 더 예뻐서', '사진 무조건 찍게 되더라고요'),
        (sec(starts[7]), sec(TOTF), '12월 대전 크리스마스 분위기는', '파스쿠찌 대전갤러리아점 저장!')]

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
