"""은행동 용가훠궈 릴스 — 캡컷 TTS에 맞춘 짧은 컷 + 컷마다 한 줄 자막(음식 안 가리는 자리).

확인한 사실 (촬영본 속 안내문): 이용시간 총 90분, 1인 1팟 주문 필수, 회전 레일 위 집게는 공용, QR 주문,
생맥주 무제한 포스터, 쟁반 이름표 '꿔바로우'. 치즈 분모자·소고기볶음밥은 성렬 님이 알려 준 메뉴.
2027(넓은 홀)은 다른 손님 얼굴이 보여서 아래쪽을 흐리게 함.
결과 2개: yongga_reel.mp4 (목소리만 → 인스타에서 음악 추가용), yongga_reel_bgm.mp4 (GONTITI 곡을 목소리 아래 깔음)
필요한 것: 업로드 폴더의 IMG_2012~2027.mov (4K HDR, 2017 없음), 캡컷 TTS copy_97BF79EA-...mov,
         인스타 오디오 화면 녹화 _talkv_dJMcboxmZIb_*.mp4 (GONTITI - Mijikame No Choushoku)
실행: /usr/bin/python3 -I tools/yongga_build.py   (REUSE_BASE=1 이면 이미 만든 컷 재사용)
"""
import os, sys, glob, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reelkit as rk
from reelkit import W, H, FPS

S = '/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/m25/'
U = '/root/.claude/uploads/56b70c86-dc21-539d-984f-e6a7533bf099/'
FONT = S + '../fonts_dl/x_pretendard/package/dist/public/static/Pretendard-Black.otf'
OUT = '/home/user/LURLUR/yongga_reel.mp4'
OUT_BGM = '/home/user/LURLUR/yongga_reel_bgm.mp4'
THUMB = '/home/user/LURLUR/yongga_thumb.jpg'
os.makedirs(S + 'seg2', exist_ok=True)
up = lambda p: sorted(glob.glob(U + p), key=os.path.getmtime)[-1]
V = {n: up(f'*-IMG_{n}.mov') for n in (2012, 2013, 2014, 2015, 2016, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027)}
TTS = up('*-copy_97BF79EA-EA61-42AB-B679-EDE9A472D8EC.mov')
SONG = up('*_talkv_dJMcboxmZIb_*.mp4')
RANK_IMG = up('*-image.jpg')        # 앱 '전국 웨이팅 맛집 TOP 100' 캡처 (1위 강남점, 2위 건대점)
RANK = 2.4                          # 순위 컷 길이 (목소리 없이 자막만)
LOOK = ('zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,'
        'zscale=p=bt709,tonemap=tonemap=mobius:param=0.5:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,',
        'eq=saturation=1.08:contrast=1.06')
BLUR_HALL = 'split[a][b];[b]crop=1080:920:0:1000,gblur=sigma=26[c];[a][c]overlay=0:1000'   # 2027: 손님 얼굴 흐리게
Y = (255, 226, 74)
SR = 48000

# ---------------- 목소리: 문장 15개 (캡컷 클립 경계 9.9/19.33/29.2초 + 쉬는 자리로 찾음) ----------------
PHR = [(0.02, 2.32), (2.45, 4.96), (5.10, 7.47), (7.63, 9.68),
       (9.90, 11.45), (11.82, 13.95), (14.29, 15.65), (15.82, 16.86), (17.27, 18.97),
       (19.45, 20.66), (21.39, 22.24), (22.73, 23.36), (24.30, 26.28), (27.04, 28.80),
       (29.38, 31.87)]
END_SPLIT = 30.525          # 마지막 문장: '은행동 용가훠궈,' | '저장해두고 가보세요!'
PAD, GAP, TAIL = 0.04, 0.3, 0.5
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', TTS, '-vn', '-ac', '2', '-ar', str(SR), '-c:a', 'pcm_s16le', S + 'tts.wav'])
_w = wave.open(S + 'tts.wav'); X = np.frombuffer(_w.readframes(_w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32)
pos = []; t = 0.0
for k, (a0, b0) in enumerate(PHR):
    pos.append(t); t += (b0 - a0) + 2 * PAD
    if k + 1 < len(PHR):
        t += min(max(PHR[k + 1][0] - b0 - 2 * PAD, 0.0), GAP)
# 첫 문장 뒤에 순위 컷만큼 목소리를 쉬게 함 (TTS 다시 녹음 없이)
POS1_OLD = pos[1]
for k in range(1, len(pos)): pos[k] += RANK
t += RANK
TOTAL = t + TAIL
buf = np.zeros((int(TOTAL * SR) + SR, 2), np.float32)
for (a0, b0), t0 in zip(PHR, pos):
    seg = X[int(max(0, a0 - PAD) * SR):int((b0 + PAD) * SR)].copy(); f = int(0.008 * SR)
    seg[:f] *= np.linspace(0, 1, f)[:, None]; seg[-f:] *= np.linspace(1, 0, f)[:, None]
    i0 = int(round(t0 * SR)); buf[i0:i0 + len(seg)] += seg
buf = buf[:int(round(TOTAL * SR))]
_o = wave.open(S + 'voice.wav', 'wb'); _o.setnchannels(2); _o.setsampwidth(2); _o.setframerate(SR)
_o.writeframes(np.clip(buf, -32768, 32767).astype(np.int16).tobytes()); _o.close()
HOOK_END = min(POS1_OLD - 0.05, 2.25)   # 첫 컷(생맥주 포스터) 원본이 2.33초뿐
CUTT = [0.0, HOOK_END] + [p - 0.05 for p in pos[1:]] + [TOTAL]
CF = [round(x * FPS) for x in CUTT]
LINE2_F = round((pos[14] + (END_SPLIT - PHR[14][0]) + PAD - 0.05) * FPS)   # pos는 이미 순위 컷만큼 밀려 있음
for k in range(len(CF) - 1): print(f'컷 {k+1:2d}: {CF[k]/FPS:5.2f}~{CF[k+1]/FPS:5.2f} ({(CF[k+1]-CF[k])/FPS:.2f}s)')

# (촬영본, 시작, 자막(줄 또는 줄 묶음), 노란 강조, 특수, 자막 가운데 y, 글자 크기) — 길이는 목소리로 정해짐, 원본 속도
# 자막 y: 화면 맨 위 300px 안과 1480px 아래는 릴스 화면의 버튼·글자와 겹쳐서 쓰지 않음
CUTS = [(2016, 0.0, ('생맥주가 무한인 곳', '아시나요?'), None, 'hook', 1300, 112),          # 생맥주 무제한 포스터 (썸네일 문구)
        ('rank', 0.0, ('전국 웨이팅 맛집 1위 2위가', '다 용가회전훠궈'), None, 'rank', 1330, 86),  # 순위 캡처 (목소리 없음)
        (2025, 0.3, ('회전초밥 아니고', '회전 훠궈?'), None, None, 440, 96),           # 레일 위로 다가오는 그릇
        (2022, 0.0, '레일 따라 재료가 계속 돌아와요', None, None, 420, 80),             # 위쪽 흰 조명 갓
        (2027, 0.3, '매장 규모부터 압도적', None, 'hall', 1150, 84),                   # 흐리게 한 홀 위
        (2020, 3.1, '이용시간은 90분', '90분', None, 620, 84),                         # 90분 안내판 바로 위
        (2014, 1.8, '1인 1팟이라 냄비도 각자', None, None, 330, 84),                   # 냄비 테두리
        (2018, 0.0, '가리비도 레일 타고 오고', None, None, 560, 84),                  # 그릇 뒤 레일
        (2012, 0.0, '꿔바로우도 가득', None, None, 330, 84),                           # 쟁반 위 거치대 (이름표 '꿔바로우')
        (2013, 0.8, '한 접시 가득 담아서', None, None, 330, 84),
        (2015, 0.0, '이게 진짜 존맛', None, None, 330, 84),                            # 꼬치
        (2023, 0.1, '겉은 바삭', None, None, 480, 84),
        (2024, 0.0, '속은 꽉', None, None, 480, 84),
        (2019, 0.0, '국물에 빠진 치즈 분모자까지', None, None, 330, 84),
        (2021, 0.5, '마무리는 소고기볶음밥', None, None, 380, 84),                      # 밥솥 안쪽 검은 벽
        (2026, 0.0, ('은행동 용가훠궈', '저장해두고 가보세요!'), None, 'end', 450, 80)]
assert len(CUTS) == len(CF) - 1
SHOTS = []
for k, (n, ss, txt, emph, sp, sy, size) in enumerate(CUTS):
    d = (CF[k + 1] - CF[k]) / FPS
    if n != 'rank':
        assert ss + d + 2 / FPS <= rk.probe_dur(V[n]) + 1e-3, f'컷 {k+1}: 원본 {n} 길이 부족 ({ss:.2f}+{d:.2f})'
    SHOTS.append((n, ss, d, txt, emph, sp, sy, size))

def rank_clip(d, out):
    """순위 캡처 컷: 흐린 매장 화면 위에 캡처 카드(제목 + 1·2위), 1·2위에 빨간 테두리, 천천히 살짝 확대."""
    rk.run(['ffmpeg', '-y', '-v', 'error', '-ss', '0.6', '-i', V[2018], '-frames:v', '1', '-vf',
            LOOK[0] + 'scale=1080:1920:flags=lanczos,' + LOOK[1], S + 'rank_bg.png'])
    bg = Image.open(S + 'rank_bg.png').convert('RGB').filter(ImageFilter.GaussianBlur(30))
    bg = Image.blend(bg, Image.new('RGB', (W, H), (0, 0, 0)), 0.45).convert('RGBA')
    sc = Image.open(RANK_IMG).convert('RGB')                      # 1206 x 2454
    head = sc.crop((0, 0, 1206, 125)); ents = sc.crop((0, 655, 1206, 1455))
    cw = 980; k = cw / 1206
    head = head.resize((cw, int(125 * k)), Image.LANCZOS); ents = ents.resize((cw, int(800 * k)), Image.LANCZOS)
    card = Image.new('RGBA', (cw + 40, head.height + ents.height + 60), (255, 255, 255, 255))
    card.paste(head, (20, 20)); card.paste(ents, (20, 40 + head.height))
    m = Image.new('L', card.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, card.width - 1, card.height - 1), 36, fill=255)
    card.putalpha(m)
    cx0, cy0 = (W - card.width) // 2, 300
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((cx0, cy0 + 14, cx0 + card.width, cy0 + card.height + 14), 36, fill=(0, 0, 0, 140))
    bg = Image.alpha_composite(bg, sh.filter(ImageFilter.GaussianBlur(18)))
    bg.alpha_composite(card, (cx0, cy0))
    base = bg.convert('RGB')
    oy = cy0 + 40 + head.height                                     # 순위 영역이 시작하는 화면 y
    boxes = [(cx0 + 20 + int(325 * k), oy + int((735 - 655) * k), cx0 + 20 + int(800 * k), oy + int((895 - 655) * k)),
             (cx0 + 20 + int(325 * k), oy + int((1185 - 655) * k), cx0 + 20 + int(800 * k), oy + int((1345 - 655) * k))]
    n = round(d * FPS)
    enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30',
                            '-i', '-', '-frames:v', str(n)] + rk.MID + [out], stdin=subprocess.PIPE)
    for f in range(n):
        z = 1 + 0.035 * f / max(1, n - 1)
        fr = base.resize((int(W * z), int(H * z)), Image.LANCZOS)
        ox, oy2 = (fr.width - W) // 2, int((fr.height - H) * 0.35)
        fr = fr.crop((ox, oy2, ox + W, oy2 + H)).convert('RGBA')
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
        for j, (x0, y0, x1, y1) in enumerate(boxes):
            a = min(1.0, max(0.0, (f - 4 - 6 * j) / 5))
            if a > 0:
                X0 = W / 2 + (x0 - W / 2) * z; X1 = W / 2 + (x1 - W / 2) * z
                Y0 = (y0 * z) - oy2; Y1 = (y1 * z) - oy2
                dd.rounded_rectangle((X0, Y0, X1, Y1), 18, outline=(255, 48, 48, int(255 * a)), width=8)
        fr = Image.alpha_composite(fr, lay).convert('RGB')
        enc.stdin.write(fr.tobytes())
        if f == n - 1: fr.resize((270, 480)).save(S + 'rank_chk.png')
    enc.stdin.close(); enc.wait()

parts = []
for i, (n, ss, d, *_r) in enumerate(SHOTS):
    out = S + f'seg2/{i}.mp4'
    if n == 'rank':
        rank_clip(d, out); parts.append(out); continue
    if not (os.environ.get('REUSE_BASE') and os.path.exists(out) and abs(rk.probe_dur(out) - d) < 0.02):
        rk.clip(V[n], ss, d, d, out, hdr=True, crop=BLUR_HALL if _r[2] == 'hall' else None, look=LOOK)
    parts.append(out)
starts = CF[:]; TOTF = CF[-1]
rk.concat(parts, S + 'cat2.txt', S + 'base2.mp4')
print('total', TOTF / FPS)

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
    SUBS.append((starts[i], starts[i + 1], imgs, sy, LINE2_F if sp == 'end' else None))

CHK = {starts[i] + 12 for i in range(len(SHOTS))} | {TOTF - 5}
dec, enc = rk.open_io(S + 'base2.mp4', S + 'comp2.mp4', TOTF)
last = None
for fi in range(TOTF):
    raw = dec.stdout.read(W * H * 3)
    if len(raw) < W * H * 3: raw = last
    last = raw
    fr = Image.frombytes('RGB', (W, H), raw).convert('RGBA')
    for f0, f1, imgs, sy, l2 in SUBS:
        if f0 <= fi < f1:
            y = sy - sum(im.height for im in imgs) // 2 + 20 * (len(imgs) - 1)
            for li, im in enumerate(imgs):
                s0 = l2 if (li == 1 and l2) else f0          # 끝 컷 둘째 줄은 그 말을 할 때 나타남
                al = min(1.0, (fi - s0 + 1) / 3)              # 튀어나오는 효과 없이 살짝 나타나기만
                if al > 0:
                    if al < 1:
                        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * al)))
                    fr.alpha_composite(im, ((W - im.width) // 2, y))
                y += imgs[li].height - 40
    if fi in CHK:
        fr.convert('RGB').resize((270, 480)).save(S + f'chk2_{fi:04d}.png')
    enc.stdin.write(fr.convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()

# ---------------- 소리 ----------------
tot = TOTF / FPS
def norm(src, dst, target=-14):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', src, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = float(r.split('Summary:')[1].split('I:')[1].split('LUFS')[0])
    rk.run(['ffmpeg', '-y', '-v', 'error', '-i', src, '-af', f'volume={target - I:.2f}dB,alimiter=limit=0.89:level=false',
            '-ar', '48000', '-c:a', 'pcm_s16le', dst])
# 1) 목소리만 (인스타에서 음악을 붙일 파일)
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', S + 'voice.wav', '-af', f'apad,atrim=0:{tot:.3f}', '-ar', '48000',
        '-c:a', 'pcm_s16le', S + 'voice_t.wav'])
norm(S + 'voice_t.wav', S + 'voice_n.wav')
vk = rk.final(S + 'comp2.mp4', OUT, TOTF, S, audio=S + 'voice_n.wav')
# 2) GONTITI 곡을 목소리 아래 깔기 (녹화 0.9초부터 곡이 나옴)
rk.run(['ffmpeg', '-y', '-v', 'error', '-ss', '0.9', '-i', SONG, '-vn', '-ac', '2', '-ar', '48000', '-c:a', 'pcm_s16le', S + 'song.wav'])
rk.mix_bgm(S + 'voice.wav', S + 'song.wav', tot, S + 'mix_raw.wav')
norm(S + 'mix_raw.wav', S + 'mix.wav')
rk.run(['ffmpeg', '-y', '-v', 'error', '-i', OUT, '-i', S + 'mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT_BGM])

# ---------------- 썸네일: 레일 위 가리비 그릇(용가 로고) + 첫 문장 ----------------
rk.run(['ffmpeg', '-y', '-v', 'error', '-ss', '0.6', '-i', V[2018], '-frames:v', '1', '-vf',
        LOOK[0] + 'scale=1080:1920:flags=lanczos,' + LOOK[1], S + 'thumb_bg.png'])
bg = Image.open(S + 'thumb_bg.png').convert('RGBA')
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
for y in range(H):
    d.line([(0, y), (W, y)], fill=(0, 0, 0, int(70 * max(0, 1 - abs(y - 400) / 320))))
bg = Image.alpha_composite(bg, ov)
for k, txt in enumerate(('생맥주가 무한인 곳', '아시나요?')):
    im = line_img(txt, None, 120)
    bg.alpha_composite(im, ((W - im.width) // 2, 330 + k * 150 - im.height // 2))
bg.convert('RGB').save(THUMB, quality=95)
print('total', round(tot, 2), 'kbps', vk, 'MB', round(os.path.getsize(OUT) / 1e6, 1), round(os.path.getsize(OUT_BGM) / 1e6, 1))
