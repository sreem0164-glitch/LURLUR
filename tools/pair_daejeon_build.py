"""페어미션(대전 자취생 편) 편집 스크립트.

필요한 것: 업로드 폴더의 매장 촬영본(IMG_1695~1705), 음식 사진, AI탭 화면 녹화(r1, r3, r4), 캡컷 TTS(r7).
작업 공간이 초기화돼도 같은 파일을 다시 받으면 이 스크립트로 그대로 다시 만들 수 있다.
실행: /usr/bin/python3 tools/pair_daejeon_build.py
"""
import subprocess, wave, random, os, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont

S = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/m15/'
U = '/root/.claude/uploads/56b70c86-dc21-539d-984f-e6a7533bf099/'
REC = S + 'rec/'
FONT = S + '../fonts_dl/x_pretendard/package/dist/public/static/Pretendard-Black.otf'
FONT_B = S + '../fonts_dl/x_pretendard/package/dist/public/static/Pretendard-Bold.otf'
OUT = '/home/user/LURLUR/pair_daejeon.mp4'

def up(name):  # 업로드 파일 찾기 (앞의 해시는 매번 달라짐)
    c = sorted(glob.glob(U + '*-' + name), key=os.path.getmtime)
    assert c, name
    return c[-1]
C = {k: up(f'IMG_{k}.mov') for k in ['1695', '1696', '1699', '1700', '1701', '1702', '1703', '1704', '1705']}
PHOTO = up('image.jpg')
TTS = REC + 'r7.mov'

TM = ('zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=100,format=gbrpf32le,'
      'zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p')
EQ = 'eq=saturation=1.12:contrast=1.05:brightness=0.03'
AIVF = 'scale=1080:-2,crop=1080:1920:0:180'
W, H, FPS, SR = 1080, 1920, 30, 48000
VENC = ['-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30',
        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']
G = S + 'seg/'; F = S + 'fr/'
os.makedirs(G, exist_ok=True); os.makedirs(F, exist_ok=True)

def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        print(' '.join(c)[:300]); print(r.stderr[-1500:]); raise SystemExit(1)

# ---------------- 음성 ----------------
run(['ffmpeg', '-y', '-v', 'error', '-i', TTS, '-vn', '-ac', '2', '-ar', '48000', S + 'tts48.wav'])
w = wave.open(S + 'tts48.wav'); X = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32)
mono = X.mean(axis=1) / 32768
db = np.array([20 * np.log10(np.sqrt(np.mean(mono[i:i + 480] ** 2)) + 1e-9) for i in range(0, len(mono) - 480, 480)])
runs = []; s = None
for i, a in enumerate(db > -38):
    if a and s is None: s = i
    if not a and s is not None: runs.append([s * 0.01, i * 0.01]); s = None
if s is not None: runs.append([s * 0.01, len(db) * 0.01])
m = []
for r in runs:
    if m and r[0] - m[-1][1] < 0.10: m[-1][1] = r[1]
    else: m.append(r)
runs = [r for r in m if r[1] - r[0] > 0.05]
# 캡컷 TTS 클립 이음새(디지털 무음) = 장면 경계
BOUND = [0.0, 5.02, 11.12, 16.31, 21.05, 24.80, 32.30, 35.22, 39.62, 44.0]
LINES = [("대전 노잼도시 인식 바꿔 주려고", "친구 데려갔다가 진짜 눈 뒤집어진 코스!"),
         ("첫 코스는 대전역 근처 보문산 호랭이!", "삼겹살 김치 필라프에다가 파스타까지 찐맛도리임"),
         ("디저트는 땡큐베리머치로 이동!", "비주얼 대박인 헤이즐넛 초코 케이크에"),
         ("시원한 아아 두 잔 시키고", "귀여운 카드랑 생일 초까지 구경하기!"),
         ("지하 좌석도 완전 넓어서", "눈치 안 보고 수다 떨기 딱인데요"),
         ("오늘 간 맛집이랑 카페, 네이버 AI탭에 물어보니까", "리뷰랑 분위기까지 한 번에 정리!"),
         ("두 곳 사이 길찾기도", "네이버 지도로 바로 연결!"),
         ("대전 처음 오는 대학생들,", "이 조합 하나면 코스 실패할 일 절대 없음!"),
         ("댓글에 '대전' 남기시면", "제가 쓴 프롬프트 보내드려요!")]
Y = (255, 226, 74); GR = (3, 199, 90)
EMPH = [{0: [("노잼도시", Y)], 1: [("눈 뒤집어진", Y)]},
        {0: [("보문산 호랭이!", Y)], 1: [("찐맛도리임", Y)]},
        {0: [("땡큐베리머치", Y)], 1: [("비주얼 대박", Y)]},
        {0: [("아아 두 잔", Y)], 1: [("생일 초", Y)]},
        {0: [("완전 넓어서", Y)], 1: [("수다 떨기 딱", Y)]},
        {0: [("네이버 AI탭", GR)], 1: [("한 번에 정리!", Y)]},
        {0: [("길찾기", Y)], 1: [("네이버 지도", GR)]},
        {0: [("대학생들,", Y)], 1: [("절대 없음!", Y)]},
        {0: [("'대전'", Y)]}]
SHAKE = {(0, 1), (7, 1)}
NS = len(LINES)

def syl(t): return sum(1 for ch in t if '가' <= ch <= '힣' or ch.isalnum())
GAP_SCENE = 0.12; GMAX = 0.18; PAD = 0.04
pieces = []; scenes = []; tcur = 0.0
for k in range(NS):
    sr_ = [[max(r[0], BOUND[k]), min(r[1], BOUND[k + 1])] for r in runs if r[1] > BOUND[k] + 0.03 and r[0] < BOUND[k + 1] - 0.03]
    a0 = max(0, sr_[0][0] - PAD); b0 = sr_[-1][1] + PAD
    segs = [[max(a0, r[0] - PAD), min(b0, r[1] + PAD)] for r in sr_]
    mm = []
    for sg in segs:
        if mm and sg[0] <= mm[-1][1]: mm[-1][1] = max(mm[-1][1], sg[1])
        else: mm.append(sg)
    mp = []; t = tcur
    for i, (a, b) in enumerate(mm):
        if i: t += min(GMAX, a - mm[i - 1][1])
        mp.append((a, b, t)); pieces.append((a, b, t)); t += b - a
    act = sum(b - a for a, b in sr_)
    target = act * syl(LINES[k][0]) / (syl(LINES[k][0]) + syl(LINES[k][1]))
    cum = 0; best = None
    for i in range(1, len(sr_)):
        cum += sr_[i - 1][1] - sr_[i - 1][0]; gap = sr_[i][0] - sr_[i - 1][1]
        sc = abs(cum - target) - 0.6 * min(gap, 0.6)
        if gap >= 0.10 and (best is None or sc < best[0]): best = (sc, sr_[i][0])
    def m2n(x):
        for a, b, tt in mp:
            if a - 0.001 <= x <= b + 0.001: return tt + (x - a)
        for a, b, tt in mp:
            if x < a: return tt
        a, b, tt = mp[-1]; return tt + (b - a)
    split = m2n(best[1]) if best else tcur + (t - tcur) * target / act
    scenes.append((tcur, t, split)); tcur = t + GAP_SCENE
TOTAL = scenes[-1][1] + 0.7
buf = np.zeros((int(TOTAL * SR) + SR, 2), np.float32)
for a, b, t in pieces:
    seg = X[int(a * SR):int(b * SR)].copy(); f = int(0.008 * SR)
    seg[:f] *= np.linspace(0, 1, f)[:, None]; seg[-f:] *= np.linspace(1, 0, f)[:, None]
    i = int(round(t * SR)); buf[i:i + len(seg)] += seg
buf = buf[:int(round(TOTAL * SR))]
o = wave.open(S + 'audio_raw.wav', 'wb'); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
o.writeframes(np.clip(buf, -32768, 32767).astype(np.int16).tobytes()); o.close()
SPEED = 1.1
run(['ffmpeg', '-y', '-v', 'error', '-i', S + 'audio_raw.wav', '-af', f'atempo={SPEED}', S + 'audio.wav'])
scenes = [(a / SPEED, b / SPEED, c / SPEED) for a, b, c in scenes]; TOTAL /= SPEED
VW = [(scenes[k][0], scenes[k + 1][0] if k < NS - 1 else TOTAL) for k in range(NS)]
NF = [round(b * FPS) - round(a * FPS) for a, b in VW]
for k in range(NS): print(f'scene {k+1}: {VW[k][0]:6.2f}~{VW[k][1]:6.2f} ({NF[k]/FPS:.2f}s)')

# ---------------- 영상 ----------------
def cam(key, ss, src, n, out, eq=EQ, blur=None):
    sp = src / (n / FPS)
    chain = f'{TM},scale={W}:{H},{eq},setsar=1'
    if abs(sp - 1) > 0.01: chain += f',setpts=PTS/{sp:.4f}'
    chain += ',fps=30,tpad=stop_mode=clone:stop_duration=2'
    if blur:  # 다른 손님 얼굴 가리기: 띠 영역만 흐리게
        y0, y1 = blur; hh = y1 - y0
        fc = f'[0:v]{chain},split[a][b];[b]crop={W}:{hh}:0:{y0},boxblur=28:4[bb];[a][bb]overlay=0:{y0},format=yuv420p[v]'
        run(['ffmpeg', '-y', '-v', 'error', '-ss', str(ss), '-t', str(src), '-i', C[key], '-filter_complex', fc,
             '-map', '[v]', '-frames:v', str(n)] + VENC + [out])
    else:
        run(['ffmpeg', '-y', '-v', 'error', '-ss', str(ss), '-t', str(src), '-i', C[key], '-vf', chain,
             '-frames:v', str(n)] + VENC + [out])
    return sp
def scr(path, ss, src, n, out):
    sp = src / (n / FPS); vf = AIVF + ',setsar=1'
    if abs(sp - 1) > 0.01: vf += f',setpts=PTS/{sp:.4f}'
    vf += ',fps=30,tpad=stop_mode=clone:stop_duration=2'
    run(['ffmpeg', '-y', '-v', 'error', '-ss', str(ss), '-t', str(src), '-i', path, '-vf', vf,
         '-frames:v', str(n)] + VENC + [out]); return sp
def still(path, t, name, boxes=(), circles=()):
    raw = F + name + '_raw.png'
    run(['ffmpeg', '-y', '-v', 'error', '-ss', str(t), '-i', path, '-frames:v', '1', '-vf', AIVF, raw])
    im = Image.open(raw).convert('RGBA'); ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for x, y, w_, h_ in boxes:
        d.rectangle([x, y, x + w_, y + h_], fill=(255, 230, 0, 80), outline=(255, 59, 48, 255), width=5)
    for x, y, r in circles:
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 59, 48, 255), width=8)
    im.alpha_composite(ov); out = F + name + '.png'; im.convert('RGB').save(out); return out
def push(png, n, start, end, out, move=0.85):
    im = Image.open(png).convert('RGB')
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30',
                          '-i', '-', '-frames:v', str(n)] + VENC + [out], stdin=subprocess.PIPE)
    for i in range(n):
        e = min(1, i / max(1, n * move)); e = e * e * (3 - 2 * e)
        b = tuple(s_ + (t_ - s_) * e for s_, t_ in zip(start, end))
        p.stdin.write(np.asarray(im.resize((W, H), Image.LANCZOS, box=b)).tobytes())
    p.stdin.close(); p.wait(); assert p.returncode == 0; return 1.0
def cat(parts, out):
    open(S + 'cat.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
    run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', S + 'cat.txt', '-c', 'copy', out])

R1, R3, R4 = REC + 'r1.mp4', REC + 'r3.mp4', REC + 'r4.mp4'
hor = still(R1, 52, 'hor', boxes=[(30, 505, 560, 300), (30, 935, 1020, 140)])
mapi = still(R1, 56, 'map', circles=[(218, 708, 70), (864, 380, 70)])
tbm = still(R3, 20, 'tbm', boxes=[(430, 322, 232, 48), (30, 1160, 700, 290)])
place = still(R3, 23, 'place', boxes=[(40, 1055, 220, 90), (100, 1472, 560, 64)])
brief = still(R3, 26, 'brief', boxes=[(40, 1125, 1010, 110)])
# 가격이 보이는 메뉴 사진 줄(y 240~770)을 잘라내고 AI 브리핑만 남기기
_b = Image.open(brief).convert('RGB'); _c = Image.new('RGB', (W, H), (255, 255, 255))
_c.paste(_b.crop((0, 0, W, 240)), (0, 0)); _c.paste(_b.crop((0, 770, W, H)), (0, 240))
brief = F + 'brief_noprice.png'; _c.save(brief)
FULL = (0, 0, 1080, 1920)
PH = Image.open(PHOTO); pw, ph = PH.size; cw = ph * W / H
PSTART = ((pw - cw) / 2, 0, (pw + cw) / 2, ph)
PEND = (pw * 0.2, ph * 0.15, pw * 0.2 + cw * 0.72, ph * 0.15 + ph * 0.72)

# 장면별 컷: (초 또는 None=남은 시간, 종류, 인자, 가격 배지)
PLAN = [
    [(1.7, 'push', dict(png=PHOTO, start=PSTART, end=PEND), None),
     (None, 'cam', dict(key='1695', ss=1.5, src=2.8), None)],
    [(1.3, 'cam', dict(key='1699', ss=2.9, src=1.4), None),
     (1.1, 'cam', dict(key='1696', ss=1.5, src=1.2), None),
     (None, 'cam', dict(key='1695', ss=0.9, src=3.0), None)],
    [(1.6, 'cam', dict(key='1701', ss=0.4, src=1.7), None),
     (None, 'cam', dict(key='1702', ss=3.4, src=3.1), None)],
    [(1.9, 'cam', dict(key='1703', ss=0.3, src=2.0), None),
     (1.0, 'cam', dict(key='1700', ss=3.4, src=1.1), None),
     (None, 'cam', dict(key='1704', ss=6.2, src=1.6), None)],
    [(1.5, 'cam', dict(key='1705', ss=1.1, src=1.45, blur=(960, 1290)), None),
     (None, 'cam', dict(key='1703', ss=2.4, src=1.8), None)],
    [(1.3, 'scr', dict(path=R1, ss=7.8, src=1.4), None),
     (1.7, 'push', dict(png=hor, start=FULL, end=(90, 320, 990, 1920)), None),
     (1.7, 'push', dict(png=tbm, start=FULL, end=(54, 96, 1026, 1824)), None),
     (None, 'push', dict(png=brief, start=FULL, end=(90, 0, 990, 1600)), None)],
    [(1.2, 'push', dict(png=mapi, start=FULL, end=(90, 100, 990, 1700)), None),
     (None, 'push', dict(png=place, start=FULL, end=(90, 320, 990, 1920)), None)],
    [(1.3, 'cam', dict(key='1695', ss=3.0, src=1.3), None),
     (1.1, 'cam', dict(key='1701', ss=2.1, src=1.1), None),
     (None, 'cam', dict(key='1696', ss=3.0, src=1.3), None)],
    [(1.6, 'cam', dict(key='1703', ss=4.2, src=1.65), None),
     (None, 'cam', dict(key='1699', ss=2.6, src=2.65), None)],
]
BADGES = []  # (f0, f1, text)
fstart = 0
for k, shots in enumerate(PLAN):
    fixed = sum(round(d * FPS) for d, _, _, _ in shots if d is not None)
    parts = []; fcur = sum(NF[:k])
    for j, (d, kind, a, badge) in enumerate(shots):
        n = round(d * FPS) if d is not None else NF[k] - fixed
        out = G + f'{k+1}_{j}.mp4'
        sp = {'cam': cam, 'scr': scr, 'push': push}[kind](n=n, out=out, **a)
        print(f'  scene {k+1} shot {j}: {n/FPS:.2f}s {kind} speed {sp:.2f}')
        if badge: BADGES.append((fcur + 4, fcur + n, badge))
        parts.append(out); fcur += n
    cat(parts, G + f'{k+1}.mp4')
cat([G + f'{i}.mp4' for i in range(1, NS + 1)], S + 'base.mp4')

# ---------------- 자막 ----------------
def tokens(line, em):
    marks = sorted([(line.find(p), p, c) for p, c in em if line.find(p) >= 0])
    spans = []; pos = 0
    for st, p, c in marks:
        if st > pos: spans.append((line[pos:st], None))
        spans.append((p, c)); pos = st + len(p)
    if pos < len(line): spans.append((line[pos:], None))
    out = []; prev_sp = True
    for txt, c in spans:
        if c: out.append([txt, c, not prev_sp]); prev_sp = False
        else:
            ps = txt.split(' ')
            for i, wd in enumerate(ps):
                if wd == '': prev_sp = True; continue
                out.append([wd, None, i == 0 and not txt.startswith(' ') and not prev_sp]); prev_sp = False
            prev_sp = txt.endswith(' ')
    units = []
    for t in out:
        if t[2] and units: units[-1].append((t[0], t[1]))
        else: units.append([(t[0], t[1])])
    return units
def render(line, em, size, maxw=960):
    units = tokens(line, em)
    while True:
        fn = ImageFont.truetype(FONT, size); fe = ImageFont.truetype(FONT, int(size * 1.12)); sp = fn.getlength(' ')
        uw = lambda u: sum((fe if c else fn).getlength(t) for t, c in u)
        rows = [[]]; cw_ = 0
        for u in units:
            wd = uw(u)
            if rows[-1] and cw_ + sp + wd > maxw: rows.append([]); cw_ = 0
            cw_ += (sp if rows[-1] else 0) + wd; rows[-1].append(u)
        if len(rows) <= 2 and max(sum(uw(u) for u in r) + sp * (len(r) - 1) for r in rows) <= maxw: break
        size -= 4
    lh = int(size * 1.32); stroke = max(6, size // 9)
    img = Image.new('RGBA', (W, lh * len(rows) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for ri, r in enumerate(rows):
        rw = sum(uw(u) for u in r) + sp * (len(r) - 1); x = (W - rw) / 2; yc = 20 + ri * lh + lh / 2
        for u in r:
            for t, c in u:
                fnt = fe if c else fn
                d.text((x, yc), t, font=fnt, fill=c or (255, 255, 255), stroke_width=stroke + (2 if c else 0), stroke_fill=(0, 0, 0), anchor='lm')
                x += fnt.getlength(t)
            x += sp
    return img
def badge_img(text):
    f = ImageFont.truetype(FONT_B, 46); tw = f.getlength(text); bw = int(tw + 90); bh = 86
    img = Image.new('RGBA', (bw, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=43, fill=(255, 255, 255, 240), outline=(3, 199, 90, 255), width=5)
    d.text((bw / 2, bh / 2), text, font=f, fill=(26, 26, 26), anchor='mm')
    return img
CY = 1360
SUBS = []
for k in range(NS):
    s0, s1, sp_ = scenes[k]; end = VW[k][1]
    for li in (0, 1):
        t0 = VW[k][0] if li == 0 else sp_ - 0.05; t1 = sp_ - 0.05 if li == 0 else end
        SUBS.append((round(t0 * FPS), round(t1 * FPS), render(LINES[k][li], EMPH[k].get(li, []), 84 if k == 0 else 74), (k, li) in SHAKE,
                     1700 if k in (5, 6) else CY))  # AI탭 화면 장면은 자막을 아래로
BIMG = [(f0, f1, badge_img(t)) for f0, f1, t in BADGES]
CY = 1360
def pop(i):
    if i >= 6: return 1.0
    x = i / 6; c = 1.9; return 0.55 + 0.45 * (1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2)
TOTF = sum(NF)
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', S + 'base.mp4', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                        '-i', S + 'audio.wav', '-map', '0:v', '-map', '1:a', '-frames:v', str(TOTF), '-c:v', 'libx264', '-preset', 'slow',
                        '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '30', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                        '-color_trc', 'bt709', '-color_range', 'tv', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT],
                       stdin=subprocess.PIPE)
random.seed(3); last = None
for fi in range(TOTF):
    raw = dec.stdout.read(W * H * 3)
    if len(raw) < W * H * 3: raw = last
    last = raw
    fr = Image.frombytes('RGB', (W, H), raw).convert('RGBA')
    for f0, f1, bi in BIMG:
        if f0 <= fi < f1:
            sc = pop(fi - f0); im = bi if sc == 1.0 else bi.resize((max(1, int(bi.width * sc)), max(1, int(bi.height * sc))))
            fr.alpha_composite(im, (int((W - im.width) / 2), int(300 - im.height / 2)))
    for f0, f1, img, sh, cy in SUBS:
        if f0 <= fi < f1:
            sc = pop(fi - f0); im = img if sc == 1.0 else img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BILINEAR)
            dx = random.randint(-7, 7) if (sh and 6 <= fi - f0 < 16) else 0
            fr.alpha_composite(im, (int((W - im.width) / 2 + dx), int(cy - im.height / 2)))
    enc.stdin.write(fr.convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()
print('total', TOTF / FPS)
