"""다이소 PDRN(4차 개인미션) 썸네일 다시 만들기 — 11/1 초기화로 원본 사진이 지워져서 영상 첫 장면(₩5,000 가격표 클로즈업)을 배경으로 씀.

디자인은 처음 제출한 썸네일과 같음: 위 흰 알약(N 로고 + '스마트렌즈 × 네이버 AI탭으로 털어봄'),
'올리브영에서 난리난 / PDRN 토너', 가격표 빨간 테두리, '다이소에선 / 단돈 5천 원?!', '피부 관리 처음인 대학생이 털어봄'.
배경 프레임에 박혀 있는 영상 자막(1250px 아래)은 흐리게 지움.
필요한 것: 업로드 폴더의 m4_daiso_pdrn_send.mp4, _talkv_dJMcbqodkKc_*.mp4 (N 로고)
실행: /usr/bin/python3 -I tools/daiso_thumb.py
"""
import glob, os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

U = '/root/.claude/uploads/56b70c86-dc21-539d-984f-e6a7533bf099/'
S = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/m21/'
FD = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/fonts_dl/x_pretendard/package/dist/public/static/'
FB, FM = FD + 'Pretendard-Black.otf', FD + 'Pretendard-Bold.otf'
OUT = '/home/user/LURLUR/m4_daiso_pdrn_thumb.jpg'
W, H = 1080, 1920
os.makedirs(S, exist_ok=True)
up = lambda p: sorted(glob.glob(U + p), key=os.path.getmtime)[-1]

subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '4.0', '-i', up('*-m4_daiso_pdrn_send.mp4'), '-frames:v', '1', S + 'bg.png'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '10.8', '-i', up('*_talkv_dJMcbqodkKc_*.mp4'), '-frames:v', '1',
                '-vf', 'scale=1080:-2:flags=lanczos,crop=1080:1920:0:180', S + 'home.png'], check=True)

bg = Image.open(S + 'bg.png').convert('RGB')
box = (0, 1250, W, H)                                   # 영상 자막이 박힌 아래쪽은 흐리게
bg.paste(bg.crop(box).filter(ImageFilter.GaussianBlur(40)), box)
bg = bg.convert('RGBA')
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
for y in range(H):
    a = 0
    if y < 780: a = int(175 * min(1, (780 - y) / 260))
    if y > 1210: a = max(a, int(190 * min(1, (y - 1210) / 200)))
    d.line([(0, y), (W, y)], fill=(10, 10, 15, a))
bg = Image.alpha_composite(bg, ov); d = ImageDraw.Draw(bg)

def ctext(y, txt, size, fill, stroke=8, font=FB):
    f = ImageFont.truetype(font, size)
    while f.getlength(txt) > 980: size -= 4; f = ImageFont.truetype(font, size)
    d.text((W / 2, y), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0), anchor='mm')

n = Image.open(S + 'home.png').convert('RGB').crop((110, 262, 190, 342)).resize((60, 60), Image.LANCZOS)
fp = ImageFont.truetype(FM, 44); txt = '스마트렌즈 × 네이버 AI탭으로 털어봄'
tw = fp.getlength(txt); pw = int(tw + 60 + 70); px = (W - pw) // 2; py = 320
d.rounded_rectangle((px, py, px + pw, py + 92), radius=46, fill='white')
bg.paste(n, (px + 26, py + 16)); d.text((px + 26 + 60 + 16, py + 46), txt, font=fp, fill=(26, 26, 26), anchor='lm')
ctext(510, '올리브영에서 난리난', 86, 'white')
ctext(640, 'PDRN 토너', 150, 'white', 10)
d.rounded_rectangle((150, 905, 995, 1240), radius=40, outline=(255, 59, 48), width=12)   # ₩5,000 가격표
ctext(1335, '다이소에선', 92, 'white')
ctext(1470, '단돈 5천 원?!', 165, (255, 226, 74), 12)
ctext(1595, '피부 관리 처음인 대학생이 털어봄', 48, 'white', 6, FM)
bg.convert('RGB').save(OUT, quality=93)
bg.convert('RGB').resize((540, 960)).save(S + 'thumb_prev.png')
print('saved', OUT)
