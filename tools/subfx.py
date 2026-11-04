"""릴스 자막 효과 (공통).

- 본문 자막: 흰 글자 + 얇은 검정 테두리 + 부드러운 그림자, 단어가 하나씩 아래에서 올라오며 나타남
- 첫 장면 문구(썸네일 문구): 흰 라벨 위 검정 글자 + 검정 라벨 위 흰 매장명, 살짝 커지며 등장
색 강조, 흔들림, 튀어나오는 효과는 쓰지 않는다.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W = 1080
FONTDIR = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/fonts_dl/x_pretendard/package/dist/public/static/'
FONT = FONTDIR + 'Pretendard-Black.otf'
FONT_EB = FONTDIR + 'Pretendard-ExtraBold.otf'

STAGGER = 2      # 다음 단어가 나오기까지 프레임
RISE = 5         # 단어 하나가 다 나타나는 데 걸리는 프레임
RISE_PX = 18     # 아래에서 올라오는 거리

def _word_img(word, font, stroke):
    pad = 24
    w = int(font.getlength(word)) + 2 * pad
    asc, desc = font.getmetrics(); h = asc + desc + 2 * pad
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((pad, pad + 5), word, font=font, fill=(0, 0, 0, 170), stroke_width=stroke + 2, stroke_fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    img.alpha_composite(sh)
    ImageDraw.Draw(img).text((pad, pad), word, font=font, fill=(255, 255, 255, 255), stroke_width=stroke, stroke_fill=(15, 15, 15, 255))
    return img, pad

def make_sub(lines, size=70, maxw=960):
    """두 줄 자막을 단어 조각으로 나눠 위치와 함께 돌려준다."""
    while True:
        f = ImageFont.truetype(FONT, size)
        if max(f.getlength(l) for l in lines) <= maxw: break
        size -= 4
    stroke = max(3, size // 16); lh = int(size * 1.32); sp = f.getlength(' ')
    words = []; order = 0
    for li, line in enumerate(lines):
        x = (W - f.getlength(line)) / 2; y = li * lh
        for wd in line.split(' '):
            img, pad = _word_img(wd, f, stroke)
            words.append((img, int(x - pad), int(y - pad), order)); order += 1
            x += f.getlength(wd) + sp
    return {'words': words, 'h': lh * len(lines)}

def _ease(t):  # ease-out cubic
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def draw_sub(frame, sub, local, cy):
    top = int(cy - sub['h'] / 2)
    for img, x, y, k in sub['words']:
        t = (local - k * STAGGER) / RISE
        if t <= 0: continue
        e = _ease(t)
        im = img
        if e < 1:
            im = img.copy(); a = im.getchannel('A').point(lambda v: int(v * e)); im.putalpha(a)
        frame.alpha_composite(im, (x, top + y + int((1 - e) * RISE_PX)))

def make_title(lines, store, size=104):
    """흰 라벨(검정 글자) 여러 줄 + 검정 라벨(흰 매장명)."""
    rows = []
    for t in lines:
        s = size
        while ImageFont.truetype(FONT, s).getlength(t) > 900: s -= 4
        rows.append((t, ImageFont.truetype(FONT, s), (255, 255, 255, 250), (17, 17, 17)))
    rows.append((store, ImageFont.truetype(FONT_EB, int(size * 0.5)), (17, 17, 17, 235), (255, 255, 255)))
    padx, pady, gap = 34, 16, 14
    sizes = []
    for t, f, bg, fg in rows:
        asc, desc = f.getmetrics(); sizes.append((int(f.getlength(t)) + 2 * padx, asc + desc + 2 * pady))
    H = sum(h for _, h in sizes) + gap * (len(rows) - 1) + 30
    img = Image.new('RGBA', (W, H + 20), (0, 0, 0, 0))
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    y = 10
    boxes = []
    for (t, f, bg, fg), (bw, bh) in zip(rows, sizes):
        x = (W - bw) // 2; boxes.append((x, y, bw, bh)); ds.rounded_rectangle((x, y + 8, x + bw, y + bh + 8), radius=18, fill=(0, 0, 0, 110)); y += bh + gap
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    for (t, f, bg, fg), (x, y, bw, bh) in zip(rows, boxes):
        d.rounded_rectangle((x, y, x + bw, y + bh), radius=18, fill=bg)
        d.text((x + bw / 2, y + bh / 2), t, font=f, fill=fg, anchor='mm')
    return img

def draw_title(frame, title, local, cy, n_in=7):
    e = _ease(local / n_in)
    sc = 0.86 + 0.14 * e
    im = title if sc >= 0.999 else title.resize((int(title.width * sc), int(title.height * sc)), Image.BILINEAR)
    if e < 1:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * e)))
    frame.alpha_composite(im, (int((W - im.width) / 2), int(cy - im.height / 2)))
