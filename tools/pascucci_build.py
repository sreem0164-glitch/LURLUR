"""파스쿠찌 대전갤러리아점 협찬 릴스 편집 스크립트 (자막만, 나레이션·BGM 없음).

필요한 것: 업로드 폴더의 촬영본 5개(_talkv_dJMcboDTM*.mp4).
실행: /usr/bin/python3 tools/pascucci_build.py
"""
import subprocess, os, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

S = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/m16/'
U = '/root/.claude/uploads/56b70c86-dc21-539d-984f-e6a7533bf099/'
FONT = S + '../fonts_dl/x_pretendard/package/dist/public/static/Pretendard-Black.otf'
FONT_B = S + '../fonts_dl/x_pretendard/package/dist/public/static/Pretendard-Bold.otf'
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
TM = ('zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=100,format=gbrpf32le,'
      'zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,')
EQ = 'eq=saturation=1.10:contrast=1.04:brightness=0.02'
W, H, FPS = 1080, 1920, 30
VENC = ['-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30',
        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']

def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        print(' '.join(c)[:300]); print(r.stderr[-1500:]); raise SystemExit(1)

def clip(key, ss, src, dur, out):
    """원본 src초를 dur초로 (src>dur이면 빨라짐). 슬로우는 쓰지 않음."""
    n = round(dur * FPS); sp = src / dur
    vf = (TM if key in HDR else '') + f'scale={W}:{H},{EQ},setsar=1'
    if abs(sp - 1) > 0.01: vf += f',setpts=PTS/{sp:.4f}'
    vf += ',fps=30,tpad=stop_mode=clone:stop_duration=2'
    run(['ffmpeg', '-y', '-v', 'error', '-ss', str(ss), '-t', str(src), '-i', V[key], '-vf', vf, '-frames:v', str(n)] + VENC + [out])
    return n

# (영상, 시작, 원본 길이, 화면 길이)
PLAN = [('tree', 0.0, 5.2, 5.2),      # 0 트리 (첫 2.6초는 썸네일 문구)
        ('hall1', 0.0, 4.6, 4.0),     # 1 그림 걸린 벽
        ('hall1', 4.6, 5.3, 4.4),     # 2 계단, 식물
        ('hall2', 0.0, 1.3, 1.2),     # 3 부스 좌석 (흰 벽만 나오는 1.3~2.7초는 뺌)
        ('hall2', 2.7, 9.6, 7.4),     # 4 그림 벽 → 넓은 홀
        ('table', 0.0, 5.3, 5.0),     # 5 음료, 케이크
        ('cake', 0.0, 2.5, 2.5),      # 6 케이크 클로즈업
        ('tree', 5.2, 3.9, 3.9)]      # 7 트리 (마무리)
parts = []; starts = []; t = 0
for i, (k, ss, src, dur) in enumerate(PLAN):
    out = S + f'seg/{i}.mp4'; n = clip(k, ss, src, dur, out); parts.append(out); starts.append(t); t += n
TOTF = t
open(S + 'cat.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', S + 'cat.txt', '-c', 'copy', S + 'base.mp4'])
sec = lambda f: f / FPS

# ---------------- 글자 ----------------
TITLE = ['대전 크리스마스 카페', '트리 맛집 찾았다!']
STORE = '파스쿠찌 대전갤러리아점'
# (시작초, 끝초, 1줄, 2줄)
SUBS = [(sec(starts[0]) + 2.6, sec(starts[1]), '창가에 트리가 줄지어 있어서', '들어가자마자 연말 분위기 가득'),
        (sec(starts[1]), sec(starts[2]), '벽마다 그림이 걸려 있어서', '갤러리 온 느낌'),
        (sec(starts[2]), sec(starts[3]), '계단이랑 초록 식물 인테리어로', '공간이 탁 트여 있고'),
        (sec(starts[3]), sec(starts[4]) + 2.6, '자리 종류도 다양해서', '혼자든 여럿이든 OK'),
        (sec(starts[4]) + 2.6, sec(starts[5]), '자리 간격도 넉넉해서', '오래 있기 좋아요'),
        (sec(starts[5]), sec(starts[6]), '음료랑 케이크도', '같이 시켜 봤는데'),
        (sec(starts[6]), sec(starts[7]), '케이크 비주얼부터', '합격!'),
        (sec(starts[7]), sec(TOTF), '12월 대전 크리스마스 카페 찾는다면', '파스쿠찌 대전갤러리아점!')]

import subfx
TITLE_IMG = subfx.make_title(TITLE, STORE)
SUB_OBJS = [(round(a * FPS), round(b * FPS), subfx.make_sub([l1, l2], 70)) for a, b, l1, l2 in SUBS]
TITLE_F = (0, round(2.6 * FPS))
CY = 1380
TITLE_CY = int(H * 0.40)

dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', S + 'base.mp4', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                        '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-map', '0:v', '-map', '1:a', '-frames:v', str(TOTF),
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '30',
                        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
                        '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
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

# ---------------- 썸네일 (영상 첫 장면 문구와 동일) ----------------
bg = ImageEnhance.Brightness(thumb_bg.convert('RGB')).enhance(1.02).convert('RGBA')
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
for y in range(H):
    a = int(70 * max(0, 1 - abs(y - TITLE_CY) / 600))
    d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
bg = Image.alpha_composite(bg, ov)
bg.alpha_composite(TITLE_IMG, (0, int(TITLE_CY - TITLE_IMG.height / 2)))
bg.convert('RGB').save(THUMB, quality=93)
print('total', TOTF / FPS)
