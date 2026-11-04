"""파스쿠찌 대전갤러리아점 협찬 릴스 편집 스크립트 (캡컷 TTS + 자막 + BGM).

필요한 것 (업로드 폴더):
- 촬영본 5개(_talkv_dJMcboDTM*.mp4)
- 캡컷 TTS 영상 copy_0977E93B-...mov (7개 텍스트 클립)
- BGM copy_E934EEC6-...mov (페어미션 때 받은 음원)
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

def up(pat):
    c = sorted(glob.glob(U + pat), key=os.path.getmtime)
    assert c, pat
    return c[-1]
V = {'tree': up('*_talkv_dJMcboDTMCw_*.mp4'), 'table': up('*_talkv_dJMcboDTMDl_*.mp4'), 'cake': up('*_talkv_dJMcboDTMDK_*.mp4'),
     'hall1': up('*_talkv_dJMcboDTMEb_*.mp4'), 'hall2': up('*_talkv_dJMcboDTMEr_*.mp4')}
HDR = {'table', 'hall1'}
TTS = up('*-copy_0977E93B-11E0-4AE8-BFDD-D79B7F9AA57D.mov')
BGM = up('*-copy_E934EEC6-76BD-467A-8B83-6741C39297DE.mov')

# ---------------- 목소리 ----------------
TITLE = ['아니 여기가 미술관이 아니라', '둔산동 카페라고요?!']
STORE = '파스쿠찌 대전갤러리아점'
LINES = [tuple(TITLE),
         ('안쪽으로 들어가면 그림 액자 가득해서', '진짜 미술관 온 것 같은 기분임!'),
         ('세련된 계단 따라 이어지는 공간도', '화초 덕분에 분위기 깔끔함'),
         ('홀도 완전 넓어서 부스석에 앉아', '친구들이랑 수다 떨기 딱 좋음!'),
         ('음료 두 잔에 케이크 두 조각 올려주니', '디저트 차림도 완전 알참!'),
         ('가까이서 보니까 더 예뻐서', '사진 무조건 찍게 되더라고요'),
         ('12월 대전 크리스마스 트리 카페는', '파스쿠찌 갤러리아점 저장해두고 가요!')]
# 캡컷 텍스트 클립 경계(초): 화면 글자가 바뀌는 시점과 무음 구간으로 확인
BOUND = [0.0, 3.60, 9.60, 14.90, 20.55, 27.15, 31.85, 37.17]
SCN, TOTAL = rk.tts_layout(TTS, BOUND, LINES, S, speed=1.1, tail=1.3)
F = [round(a * FPS) for a, _, _ in SCN]
TOTF = round(TOTAL * FPS); F.append(TOTF)
for k, (a, b, c) in enumerate(SCN): print(f'장면 {k+1}: {F[k]/FPS:5.2f}~{F[k+1]/FPS:5.2f}')

# ---------------- 영상 ----------------
# (영상, 원본 시작, 원본 길이, 시작 프레임, 끝 프레임, 느리게 허용)
H2A = round(3.9 * FPS)   # 그림 벽(다른 각도) 길이
BOOTH = round(1.3 * FPS)
SHOTS = [('hall1', 0.0, None, 0, F[2] - H2A),        # 1~2 그림 걸린 벽 (썸네일 문구)
         ('hall2', 2.7, 3.9, F[2] - H2A, F[2]),      # 2 그림 벽 따라 안쪽으로
         ('hall1', 5.4, 4.5, F[2], F[3]),            # 3 계단, 화초
         ('hall2', 7.5, 3.6, F[3], F[4] - BOOTH),    # 4 넓은 홀
         ('hall2', 0.0, 1.3, F[4] - BOOTH, F[4]),    # 4 부스석
         ('table', 0.0, 5.33, F[4], F[5]),           # 5 음료 두 잔, 케이크 두 조각
         ('cake', 0.0, 2.53, F[5], F[6], True),      # 6 케이크 클로즈업 (원본 2.5초뿐이라 프레임 섞어 늘림)
         ('tree', 0.0, 6.3, F[6], TOTF)]             # 7 크리스마스 트리
parts = []
for i, (k, ss, src, f0, f1, *slow) in enumerate(SHOTS):
    dur = (f1 - f0) / FPS
    out = S + f'seg/{i}.mp4'
    rk.clip(V[k], ss, src or dur, dur, out, hdr=k in HDR, slow=bool(slow))
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
