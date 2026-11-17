"""은행동 용가훠궈 릴스 — 짧은 컷 + 컷마다 한 줄 자막(음식 안 가리는 자리) + BGM. (TTS는 받으면 레커버거처럼 맞춤)

확인한 사실 (촬영본 속 안내문): 이용시간 총 90분, 1인 1팟 주문 필수, 회전 레일 위 집게는 공용, QR 주문, 생맥주 무제한 포스터.
메뉴 이름·가격은 자막에 넣지 않음. 2027(넓은 홀)은 다른 손님 얼굴이 보여서 아래쪽을 흐리게 함.
필요한 것: 업로드 폴더의 IMG_2012~2027.mov (4K HDR, 2017 없음), BGM copy_E934EEC6-...mov
실행: /usr/bin/python3 -I tools/yongga_build.py   (REUSE_BASE=1 이면 이미 만든 컷 재사용)
"""
import os, sys, glob, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reelkit as rk
from reelkit import W, H, FPS

S = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/m25/'
U = '/root/.claude/uploads/56b70c86-dc21-539d-984f-e6a7533bf099/'
FONT = S + '../fonts_dl/x_pretendard/package/dist/public/static/Pretendard-Black.otf'
OUT = '/home/user/LURLUR/yongga_reel.mp4'
THUMB = '/home/user/LURLUR/yongga_thumb.jpg'
os.makedirs(S + 'seg', exist_ok=True)
up = lambda p: sorted(glob.glob(U + p), key=os.path.getmtime)[-1]
V = {n: up(f'*-IMG_{n}.mov') for n in (2012, 2013, 2014, 2015, 2016, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027)}
BGM = up('*-copy_E934EEC6-76BD-467A-8B83-6741C39297DE.mov')
LOOK = ('zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,'
        'zscale=p=bt709,tonemap=tonemap=mobius:param=0.5:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,',
        'eq=saturation=1.08:contrast=1.06')
# 2027: 다른 손님 얼굴이 보이는 아래쪽(1000px 아래)을 흐리게
BLUR_HALL = 'split[a][b];[b]crop=1080:920:0:1000,gblur=sigma=26[c];[a][c]overlay=0:1000'
Y = (255, 226, 74)

# (촬영본, 시작, 길이, 자막, 노란 강조, 특수, 자막 가운데 y, 글자 크기)
# 자막 y: 화면 맨 위 300px 안과 1480px 아래는 릴스 화면의 버튼·글자와 겹쳐서 쓰지 않음
SHOTS = [(2025, 0.3, 2.2, ('회전초밥 아니고', '회전 훠궈?'), None, 'hook', 440, 112),
         (2022, 0.0, 2.6, '레일 따라 재료가 계속 돌아와요', None, None, 420, 80),          # 위쪽 흰 조명 갓
         (2027, 0.3, 2.0, '매장 규모부터 압도적', None, 'hall', 1150, 84),                # 흐리게 한 홀 위
         (2020, 3.2, 2.0, '이용시간은 90분', '90분', None, 620, 84),                      # 90분 안내판 바로 위
         (2014, 1.8, 2.6, '1인 1팟이라 냄비도 각자', None, None, 330, 84),                # 냄비 테두리
         (2018, 0.0, 2.2, '가리비도 레일 타고 오고', None, None, 560, 84),               # 그릇 뒤 레일
         (2012, 0.0, 1.5, '꿔바로우도 가득', None, None, 330, 84),                       # 쟁반 위 거치대 (이름표 '꿔바로우' 확인)
         (2013, 0.8, 1.6, '한 접시 가득 담아서', None, None, 330, 84),                    # 테이블 위쪽
         (2015, 0.0, 1.8, '꼬치까지 있음', None, None, 330, 84),
         (2023, 0.1, 1.5, '겉은 바삭', None, None, 480, 84),                              # 위쪽 흰 테이블
         (2024, 0.0, 1.7, '속은 꽉', None, None, 480, 84),
         (2019, 0.4, 1.8, '국물에 빠진 계란까지', None, None, 330, 84),
         (2021, 0.5, 2.2, '마무리는 볶음밥', None, None, 380, 84),                        # 밥솥 안쪽 검은 벽
         (2016, 0.25, 2.0, '생맥주도 무제한', '무제한', None, 1250, 84),
         (2026, 0.15, 3.0, ('은행동 용가훠궈', '저장해두고 가보세요!'), None, 'end', 450, 80)]   # 위쪽 조명 갓 아래

parts = []; starts = []; t = 0
for i, (n, ss, d, *_r) in enumerate(SHOTS):
    out = S + f'seg/{i}.mp4'
    assert ss + d + 2 / FPS <= rk.probe_dur(V[n]) + 1e-3, f'컷 {i+1}: 원본 {n} 길이 부족'
    if not (os.environ.get('REUSE_BASE') and os.path.exists(out)):
        rk.clip(V[n], ss, d, d, out, hdr=True, crop=BLUR_HALL if _r[2] == 'hall' else None, look=LOOK)
    parts.append(out); starts.append(t); t += round(d * FPS)
TOTF = t; starts.append(TOTF)
rk.concat(parts, S + 'cat.txt', S + 'base.mp4')
print('total', TOTF / FPS)
if os.environ.get('BASE_ONLY'): raise SystemExit(0)

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

CHK = {starts[i] + 15 for i in range(len(SHOTS))}
dec, enc = rk.open_io(S + 'base.mp4', S + 'comp.mp4', TOTF)
last = None
for fi in range(TOTF):
    raw = dec.stdout.read(W * H * 3)
    if len(raw) < W * H * 3: raw = last
    last = raw
    fr = Image.frombytes('RGB', (W, H), raw).convert('RGBA')
    for f0, f1, imgs, sy in SUBS:
        if f0 <= fi < f1:
            al = min(1.0, (fi - f0 + 1) / 3)     # 튀어나오는 효과 없이 살짝 나타나기만
            y = sy - sum(im.height for im in imgs) // 2 + 20 * (len(imgs) - 1)
            for im in imgs:
                if al < 1:
                    im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * al)))
                fr.alpha_composite(im, ((W - im.width) // 2, y)); y += im.height - 40
    if fi in CHK:
        fr.convert('RGB').resize((270, 480)).save(S + f'chk_{fi:04d}.png')
    enc.stdin.write(fr.convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()

# ---------------- BGM ----------------
tot = TOTF / FPS
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', BGM, '-vn', '-t', f'{tot:.3f}', '-af',
        f'aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.3,afade=t=out:st={tot - 1.5:.3f}:d=1.5',
        '-ar', '48000', '-c:a', 'pcm_s16le', S + 'bgm_raw.wav'])
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', S + 'bgm_raw.wav', '-af', 'ebur128', '-f', 'null', '-'],
                   capture_output=True, text=True).stderr
I = float(r.split('Summary:')[1].split('I:')[1].split('LUFS')[0])
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', S + 'bgm_raw.wav', '-af', f'volume={-14 - I:.2f}dB,alimiter=limit=0.89:level=false',
        '-ar', '48000', '-c:a', 'pcm_s16le', S + 'bgm.wav'])
vk = rk.final(S + 'comp.mp4', OUT, TOTF, S, audio=S + 'bgm.wav')

# ---------------- 썸네일: 레일 위 가리비 그릇(용가 로고) + 첫 컷 문구 ----------------
rk.run(['ffmpeg', '-y', '-v', 'error', '-ss', '0.6', '-i', V[2018], '-frames:v', '1', '-vf',
        LOOK[0] + 'scale=1080:1920:flags=lanczos,' + LOOK[1], S + 'thumb_bg.png'])
bg = Image.open(S + 'thumb_bg.png').convert('RGBA')
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
for y in range(H):
    d.line([(0, y), (W, y)], fill=(0, 0, 0, int(70 * max(0, 1 - abs(y - 400) / 320))))
bg = Image.alpha_composite(bg, ov)
for k, txt in enumerate(('회전초밥 아니고', '회전 훠궈?')):
    im = line_img(txt, None, 120)
    bg.alpha_composite(im, ((W - im.width) // 2, 330 + k * 150 - im.height // 2))
bg.convert('RGB').save(THUMB, quality=95)
print('total', round(tot, 2), 'kbps', vk, 'MB', round(os.path.getsize(OUT) / 1e6, 1))
