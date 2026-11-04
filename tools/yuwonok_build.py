"""유원옥 리뷰 릴스 편집 스크립트 (자막만, 나레이션·BGM 없음).

필요한 것: 업로드 폴더의 촬영본 12개.
실행: /usr/bin/python3 tools/yuwonok_build.py
"""
import subprocess, os, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

S = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/m17/'
U = '/root/.claude/uploads/56b70c86-dc21-539d-984f-e6a7533bf099/'
FONT = S + '../fonts_dl/x_pretendard/package/dist/public/static/Pretendard-Black.otf'
FONT_B = S + '../fonts_dl/x_pretendard/package/dist/public/static/Pretendard-Bold.otf'
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
CROP = {'rib_lift': 'crop=864:1536:108:384,scale=1080:1920'}
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
    vf = (TM if key in HDR else '') + f'scale={W}:{H},' + (CROP[key] + ',' if key in CROP else '') + f'{EQ},setsar=1'
    if abs(sp - 1) > 0.01: vf += f',setpts=PTS/{sp:.4f}'
    vf += ',fps=30,tpad=stop_mode=clone:stop_duration=2'
    run(['ffmpeg', '-y', '-v', 'error', '-ss', str(ss), '-t', str(src), '-i', V[key], '-vf', vf, '-frames:v', str(n)] + VENC + [out])
    return n

# (영상, 시작, 원본 길이, 화면 길이)
PLAN = [('rib_lift', 1.0, 4.0, 4.0),   # 0 갈비 들어 올리기 (첫 2.6초 썸네일 문구)
        ('rib_cut', 2.5, 8.0, 6.0),    # 1 가위로 자르기
        ('rib_steam', 0.0, 5.0, 3.5),  # 2 김 나는 국물, 지단
        ('soup_a', 2.5, 6.0, 4.0),     # 3 고기 든 국물
        ('soup_lift', 0.0, 3.6, 3.0),  # 4 고기 떠 올리기
        ('dip', 0.0, 3.6, 3.0),        # 5 소스 찍기
        ('sides', 0.0, 3.3, 3.0),      # 6 반찬
        ('self', 0.5, 5.0, 4.0),       # 7 셀프 온육수, 안내문
        ('room', 0.0, 4.4, 3.5),       # 8 매장
        ('rib_bowl', 0.0, 3.9, 3.0)]   # 9 마무리
parts = []; starts = []; t = 0
for i, (k, ss, src, dur) in enumerate(PLAN):
    out = S + f'seg/{i}.mp4'; n = clip(k, ss, src, dur, out); parts.append(out); starts.append(t); t += n
TOTF = t
open(S + 'cat.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', S + 'cat.txt', '-c', 'copy', S + 'base.mp4'])
sec = lambda f: f / FPS

# ---------------- 글자 ----------------
TITLE = ['갈비 크기 실화?!']
STORE = '유원옥'
# (시작초, 끝초, 1줄, 2줄)
SUBS = [(sec(starts[0]) + 2.6, sec(starts[1]), '큼직한 갈비가', '통째로 들어 있고'),
        (sec(starts[1]), sec(starts[2]), '가위로 슥슥 잘라서', '먹으면 끝'),
        (sec(starts[2]), sec(starts[3]), '지단이랑 파 듬뿍 올라간', '뜨끈한 국물'),
        (sec(starts[3]), sec(starts[4]), '고기 가득 담긴 국물도', '한 그릇 더'),
        (sec(starts[4]), sec(starts[5]), '한 숟갈 뜨면', '고기가 이만큼'),
        (sec(starts[5]), sec(starts[6]), '고기는 소스에', '콕 찍어서'),
        (sec(starts[6]), sec(starts[7]), '김치랑 깍두기까지', '반찬도 든든'),
        (sec(starts[7]), sec(starts[8]), '온육수랑 따뜻한 물은 셀프!', '소금, 후추도 준비돼 있어요'),
        (sec(starts[8]), sec(starts[9]), '테이블도 넓어서', '여럿이 오기 좋아요'),
        (sec(starts[9]), sec(TOTF), '든든한 한 끼 생각나면', '유원옥!')]

def text_block(lines, size, maxw=960, stroke_div=9, font=FONT, lh_mul=1.3):
    while True:
        f = ImageFont.truetype(font, size)
        if max(f.getlength(l) for l in lines) <= maxw: break
        size -= 4
    lh = int(size * lh_mul); st = max(6, size // stroke_div)
    img = Image.new('RGBA', (W, lh * len(lines) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        d.text((W / 2, 20 + i * lh + lh / 2), l, font=f, fill='white', stroke_width=st, stroke_fill='black', anchor='mm')
    return img
def title_block():
    big = text_block(TITLE, 130, maxw=980, stroke_div=8)
    small = text_block([STORE], 72, font=FONT)
    img = Image.new('RGBA', (W, big.height + small.height), (0, 0, 0, 0))
    img.alpha_composite(big, (0, 0)); img.alpha_composite(small, (0, big.height - 10))
    return img
TITLE_IMG = title_block()
SUB_IMGS = [(round(a * FPS), round(b * FPS), text_block([l1, l2], 70)) for a, b, l1, l2 in SUBS]
TITLE_F = (0, round(2.6 * FPS))
CY = 1380

def fade(i, n=4): return min(1.0, (i + 1) / n)
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
        a = fade(fi - TITLE_F[0]); im = TITLE_IMG
        if a < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
        fr.alpha_composite(im, (0, int(H * 0.42 - im.height / 2)))
    for f0, f1, img in SUB_IMGS:
        if f0 <= fi < f1:
            a = fade(fi - f0); im = img
            if a < 1: im = img.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
            fr.alpha_composite(im, (0, int(CY - im.height / 2)))
    enc.stdin.write(fr.convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()

# ---------------- 썸네일 (영상 첫 장면 문구와 동일) ----------------
bg = ImageEnhance.Brightness(thumb_bg.convert('RGB')).enhance(1.02).convert('RGBA')
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
for y in range(H):
    a = int(120 * max(0, 1 - abs(y - H * 0.42) / 520))
    d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
bg = Image.alpha_composite(bg, ov)
bg.alpha_composite(TITLE_IMG, (0, int(H * 0.42 - TITLE_IMG.height / 2)))
bg.convert('RGB').save(THUMB, quality=93)
print('total', TOTF / FPS)
