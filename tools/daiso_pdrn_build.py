# 대화 기록에서 복구한 다이소 PDRN(4차 개인미션) 편집 스크립트 — 2026-11-01 작업 환경 초기화로 원본 파일이 지워져서 다시 받아야 실행 가능.
# 필요한 파일: 다이소 촬영본 IMG_1662·1663·1664·1669·1670, 라벨 사진, 화면녹화 3개(AI탭 2분28초, AI탭 35초, 스마트렌즈 43초), 캡컷 TTS(40초)
"""4차 개인미션: 다이소 VT PDRN 토너 — TTS 기준 편집 + 효과 자막"""
import subprocess, wave, random, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
D='/tmp/claude-0/-home-user-LURLUR/56b70c86-dc21-539d-984f-e6a7533bf099/scratchpad/m14/'
U='/root/.claude/uploads/56b70c86-dc21-539d-984f-e6a7533bf099/'
FONT=D+'../fonts_dl/x_pretendard/package/dist/public/static/Pretendard-Black.otf'
C={'1662':'48692d46-IMG_1662','1663':'9b167948-IMG_1663','1664':'e49df111-IMG_1664','1667':'412fab14-IMG_1667',
   '1668':'2d1e0b68-IMG_1668','1669':'c2e0c73e-IMG_1669','1670':'d7fb6358-IMG_1670'}
LABEL=U+'deaf6696-image.jpg'; LENS=U+'a1507929-image.png'
REC=D+'rec.mp4'; REC2=D+'rec2.mp4'
TM='zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p'
EQ='eq=saturation=1.12:contrast=1.05:brightness=0.03'
AIVF='scale=1080:-2,crop=1080:1920:0:180'
W,H,FPS,SR=1080,1920,30,48000
VENC=['-an','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r','30',
      '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv']
def run(c):
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode: print(' '.join(c)[:300]); print(r.stderr[-1500:]); raise SystemExit(1)

# ---------------- audio ----------------
w=wave.open(D+'tts/tts48.wav'); X=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(np.float32)
mono=X.mean(axis=1)/32768; hop=480
db=np.array([20*np.log10(np.sqrt(np.mean(mono[i:i+hop]**2))+1e-9) for i in range(0,len(mono)-hop,hop)])
act=db>-38; runs=[]; s=None
for i,a in enumerate(act):
    if a and s is None: s=i
    if not a and s is not None: runs.append([s*0.01,i*0.01]); s=None
if s is not None: runs.append([s*0.01,len(act)*0.01])
m=[]
for r in runs:
    if m and r[0]-m[-1][1]<0.10: m[-1][1]=r[1]
    else: m.append(r)
runs=[r for r in m if r[1]-r[0]>0.05]
# scene boundaries = CapCut clip joins (digital silence) = subtitle-track changes
BOUND=[0.0,5.46,11.61,16.62,21.49,25.76,31.10,35.05,40.17]
LINES=[("올리브영에서 난리난 PDRN 토너","다이소에선 단돈 5천 원?!"),
       ("피부 관리 처음인 대학생이","진짜 괜찮은지 AI탭으로 털어봤어요!"),
       ("스마트렌즈로 찍으니까","제품 정보에 쇼핑까지 바로!"),
       ("네이버 AI탭으로 더 깊게,","진짜 가성비인지 털어봄!"),
       ("기존 제품이랑 뭐가 다른지","딱 핵심만 정리해 주는데"),
       ("가격은 ml당 25원 vs 75원,","다이소가 3배나 저렴함!"),
       ("피부 관리 처음이면","다이소 걸로도 완전 충분!"),
       ("댓글에 '토너' 남기시면","프롬프트랑 토너 정보 다 보내드려요!")]
Y=(255,226,74); G=(3,199,90)
EMPH=[{0:[("난리난",Y)],1:[("단돈 5천 원?!",Y)]},
      {0:[("대학생",Y)],1:[("AI탭",G)]},
      {0:[("스마트렌즈",G)],1:[("쇼핑까지 바로!",Y)]},
      {0:[("네이버 AI탭",G)],1:[("진짜 가성비",Y)]},
      {1:[("딱 핵심만",Y)]},
      {0:[("25원 vs 75원,",Y)],1:[("3배나 저렴함!",Y)]},
      {1:[("완전 충분!",Y)]},
      {0:[("'토너'",Y)]}]
SHAKE={(0,1),(5,1)}
NS=len(LINES)
def syl(t): return sum(1 for ch in t if '가'<=ch<='힣' or ch.isdigit() or ch.isalpha())
GAP_SCENE=0.12; GMAX=0.18; PAD=0.04
pieces=[]; scenes=[]; tcur=0.0
for k in range(NS):
    sr_=[[max(r[0],BOUND[k]),min(r[1],BOUND[k+1])] for r in runs if r[1]>BOUND[k]+0.03 and r[0]<BOUND[k+1]-0.03]
    a0=max(0,sr_[0][0]-PAD); b0=sr_[-1][1]+PAD
    segs=[[max(a0,r[0]-PAD),min(b0,r[1]+PAD)] for r in sr_]
    mm=[]
    for sg in segs:
        if mm and sg[0]<=mm[-1][1]: mm[-1][1]=max(mm[-1][1],sg[1])
        else: mm.append(sg)
    mp=[]; t=tcur
    for i,(a,b) in enumerate(mm):
        if i: t+=min(GMAX,a-mm[i-1][1])
        mp.append((a,b,t)); pieces.append((a,b,t)); t+=b-a
    act_tot=sum(b-a for a,b in sr_); target=act_tot*syl(LINES[k][0])/(syl(LINES[k][0])+syl(LINES[k][1]))
    cum=0; best=None
    for i in range(1,len(sr_)):
        cum+=sr_[i-1][1]-sr_[i-1][0]; gap=sr_[i][0]-sr_[i-1][1]
        score=abs(cum-target)-0.6*min(gap,0.6)
        if gap>=0.10 and (best is None or score<best[0]): best=(score,sr_[i][0])
    def m2n(x):
        for a,b,tt in mp:
            if a-0.001<=x<=b+0.001: return tt+(x-a)
        for a,b,tt in mp:
            if x<a: return tt
        a,b,tt=mp[-1]; return tt+(b-a)
    split=m2n(best[1]) if best else tcur+(t-tcur)*target/act_tot
    scenes.append((tcur,t,split)); tcur=t+GAP_SCENE
TOTAL=scenes[-1][1]+0.7
buf=np.zeros((int(TOTAL*SR)+SR,2),np.float32)
for a,b,t in pieces:
    seg=X[int(a*SR):int(b*SR)].copy(); f=int(0.008*SR)
    seg[:f]*=np.linspace(0,1,f)[:,None]; seg[-f:]*=np.linspace(1,0,f)[:,None]
    i=int(round(t*SR)); buf[i:i+len(seg)]+=seg
buf=buf[:int(round(TOTAL*SR))]
o=wave.open(D+'audio_raw.wav','wb'); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes(np.clip(buf,-32768,32767).astype(np.int16).tobytes()); o.close()
SPEED=1.1
run(['ffmpeg','-y','-v','error','-i',D+'audio_raw.wav','-af',f'atempo={SPEED}',D+'audio.wav'])
scenes=[(a/SPEED,b/SPEED,c/SPEED) for a,b,c in scenes]; TOTAL=TOTAL/SPEED
VW=[(scenes[k][0], scenes[k+1][0] if k<NS-1 else TOTAL) for k in range(NS)]
NF=[round(b*FPS)-round(a*FPS) for a,b in VW]
for k in range(NS): print(f'scene {k+1}: {VW[k][0]:6.2f}~{VW[k][1]:6.2f} ({NF[k]/FPS:.2f}s) line2@{scenes[k][2]:.2f}')

# ---------------- video helpers ----------------
G_=D+'seg/'; os.makedirs(G_,exist_ok=True)
def cam(key,ss,src,n,out,eq=EQ):
    sp=src/(n/FPS); vf=f'{TM},scale={W}:{H},{eq},setsar=1'
    if abs(sp-1)>0.01: vf+=f',setpts=PTS/{sp:.4f}'
    vf+=',fps=30'+(',tpad=stop_mode=clone:stop_duration=2' if sp<0.999 else '')
    run(['ffmpeg','-y','-v','error','-ss',str(ss),'-t',str(src),'-i',U+C[key]+'.mov','-vf',vf,'-frames:v',str(n)]+VENC+[out]); return sp
def scr(path,ss,src,n,out):
    sp=src/(n/FPS); vf=AIVF+',setsar=1'
    if abs(sp-1)>0.01: vf+=f',setpts=PTS/{sp:.4f}'
    vf+=',fps=30'+(',tpad=stop_mode=clone:stop_duration=2' if sp<0.999 else '')
    run(['ffmpeg','-y','-v','error','-ss',str(ss),'-t',str(src),'-i',path,'-vf',vf,'-frames:v',str(n)]+VENC+[out]); return sp
def frame(path,t,out):
    if not os.path.exists(out): run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',path,'-frames:v','1',out])
    return out
def hl(png,boxes,out):
    im=Image.open(png).convert('RGBA'); ov=Image.new('RGBA',im.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
    for x,y,w,h in boxes: d.rectangle([x,y,x+w,y+h],fill=(255,230,0,85),outline=(255,59,48,255),width=4)
    im.alpha_composite(ov); im.convert('RGB').save(out); return out
def push(png,n,start,end,out,move=0.85):
    im=Image.open(png).convert('RGB')
    p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-frames:v',str(n)]+VENC+[out],stdin=subprocess.PIPE)
    for i in range(n):
        e=min(1,i/max(1,n*move)); e=e*e*(3-2*e)
        b=tuple(s+(t-s)*e for s,t in zip(start,end))
        p.stdin.write(np.asarray(im.resize((W,H),Image.LANCZOS,box=b)).tobytes())
    p.stdin.close(); p.wait(); assert p.returncode==0; return 1.0
def card(png,box,out,y=300,bg=(250,250,252),hboxes=()):
    im=Image.open(png).convert('RGBA'); ov=Image.new('RGBA',im.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
    for x,yy,w_,h_ in hboxes: d.rectangle([x,yy,x+w_,yy+h_],fill=(255,230,0,85),outline=(255,59,48,255),width=4)
    im.alpha_composite(ov); c=im.crop(box); s=W/c.width; c=c.resize((W,int(c.height*s)),Image.LANCZOS)
    o=Image.new('RGB',(W,H),bg); o.paste(c.convert('RGB'),(0,y)); o.save(out); return out
def cat(parts,out):
    open(D+'cat.txt','w').write(''.join(f"file '{p}'\n" for p in parts))
    run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',D+'cat.txt','-c','copy',out])

# stills
F=D+'fr/'
lens_png=LENS
a58=hl(frame(REC,58.0,F+'a_58.0.png'),[(30,760,790,62),(460,818,212,58),(30,930,730,60)],F+'h_a58.png')
lab=hl(LABEL,[(840,1050,172,40),(835,1234,170,40)],F+'h_label.png')
b20=hl(frame(REC2,20.0,F+'b_20.0.png'),[(28,548,820,228)],F+'h_b20.png')
tbl=card(frame(REC2,26.0,F+'b_26.0.png'),(20,840,860,1300),F+'h_tbl.png',y=330,hboxes=[(650,1066,140,60),(650,1204,140,60)])
a130=hl(frame(REC,130.0,F+'a_130.0.png'),[(30,552,810,58),(30,608,300,58)],F+'h_a130.png')

# shot plan per scene: (seconds or None=rest, kind, args)
PLAN=[
 [(2.30,'cam',dict(key='1662',ss=0.6,src=2.6)), (None,'cam',dict(key='1663',ss=0.8,src=2.6))],
 [(2.40,'cam',dict(key='1669',ss=0.3,src=2.6)), (None,'cam',dict(key='1664',ss=0.0,src=3.2))],
 [(0.50,'scr',dict(path=D+'lens.mp4',ss=0.3,src=1.0)),
  (0.80,'scr',dict(path=D+'lens.mp4',ss=1.9,src=1.4)),
  (0.80,'scr',dict(path=D+'lens.mp4',ss=5.15,src=1.45)),
  (None,'scr',dict(path=D+'lens.mp4',ss=12.3,src=2.4))],
 [(None,'scr',dict(path=REC,ss=29.8,src=4.6))],
 [(1.70,'push',dict(png=a58,start=(0,300,880,1864),end=(40,560,800,1911))),
  (None,'push',dict(png=lab,start=(300,300,1212,1921),end=(657,652,1217,1648)))],
 [(2.40,'push',dict(png=b20,start=(10,300,870,1829),end=(20,420,840,1878))),
  (None,'push',dict(png=tbl,start=(0,0,1080,1920),end=(40,140,1040,1918)))],
 [(None,'push',dict(png=a130,start=(10,300,870,1829),end=(40,330,800,1681)))],
 [(2.50,'cam',dict(key='1670',ss=0.2,src=2.7)), (None,'cam',dict(key='1664',ss=1.0,src=2.4))],
]
for k,shots in enumerate(PLAN):
    fixed=sum(round(d*FPS) for d,_,_ in shots if d is not None)
    parts=[]
    for j,(d,kind,a) in enumerate(shots):
        n=round(d*FPS) if d is not None else NF[k]-fixed
        out=G_+f'{k+1}_{j}.mp4'
        sp={'cam':cam,'scr':scr,'push':push}[kind](n=n,out=out,**a)
        print(f'  scene {k+1} shot {j}: {n/FPS:.2f}s {kind} speed {sp:.2f}')
        parts.append(out)
    cat(parts,G_+f'{k+1}.mp4')
cat([G_+f'{i}.mp4' for i in range(1,NS+1)],D+'base.mp4')

# ---------------- subtitles ----------------
def tokens(line,em):
    marks=sorted([(line.find(p),p,c) for p,c in em if line.find(p)>=0])
    spans=[]; pos=0
    for st,p,c in marks:
        if st>pos: spans.append((line[pos:st],None))
        spans.append((p,c)); pos=st+len(p)
    if pos<len(line): spans.append((line[pos:],None))
    out=[]; prev_end_space=True
    for txt,c in spans:
        if c: out.append([txt,c,not prev_end_space]); prev_end_space=False
        else:
            parts=txt.split(' ')
            for i,wd in enumerate(parts):
                if wd=='': prev_end_space=True; continue
                glue=(i==0 and not txt.startswith(' ') and not prev_end_space)
                out.append([wd,None,glue]); prev_end_space=False
            prev_end_space=txt.endswith(' ')
    units=[]
    for t in out:
        if t[2] and units: units[-1].append((t[0],t[1]))
        else: units.append([(t[0],t[1])])
    return units
def render(line,em,size,maxw=960):
    units=tokens(line,em)
    while True:
        fn=ImageFont.truetype(FONT,size); fe=ImageFont.truetype(FONT,int(size*1.12)); sp=fn.getlength(' ')
        uw=lambda u:sum((fe if c else fn).getlength(t) for t,c in u)
        rows=[[]]; cw=0
        for u in units:
            wdt=uw(u)
            if rows[-1] and cw+sp+wdt>maxw: rows.append([]); cw=0
            cw+=(sp if rows[-1] else 0)+wdt; rows[-1].append(u)
        if len(rows)<=2 and max(sum(uw(u) for u in r)+sp*(len(r)-1) for r in rows)<=maxw: break
        size-=4
    lh=int(size*1.32); stroke=max(6,size//9)
    img=Image.new('RGBA',(W,lh*len(rows)+40),(0,0,0,0)); d=ImageDraw.Draw(img)
    for ri,r in enumerate(rows):
        rw=sum(uw(u) for u in r)+sp*(len(r)-1); x=(W-rw)/2; ycen=20+ri*lh+lh/2
        for u in r:
            for t,c in u:
                fnt=fe if c else fn
                d.text((x,ycen),t,font=fnt,fill=c or (255,255,255),stroke_width=stroke+(2 if c else 0),stroke_fill=(0,0,0),anchor='lm')
                x+=fnt.getlength(t)
            x+=sp
    return img
SUBS=[]
for k in range(NS):
    s0,s1,sp_=scenes[k]; end=VW[k][1]
    for li in (0,1):
        t0=(VW[k][0] if li==0 else sp_-0.05); t1=(sp_-0.05 if li==0 else end)
        size=84 if k==0 else 74
        img=render(LINES[k][li],EMPH[k].get(li,[]),size)
        SUBS.append((round(t0*FPS),round(t1*FPS),img,(k,li) in SHAKE))
CY=1360
def pop(i):
    if i>=6: return 1.0
    x=i/6; c=1.9; return 0.55+0.45*(1+(c+1)*(x-1)**3+c*(x-1)**2)
TOTF=sum(NF)
dec=subprocess.Popen(['ffmpeg','-v','error','-i',D+'base.mp4','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-i',D+'audio.wav',
     '-map','0:v','-map','1:a','-frames:v',str(TOTF),'-c:v','libx264','-preset','slow','-crf','20','-pix_fmt','yuv420p','-r','30',
     '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',
     '/home/user/LURLUR/m4_daiso_pdrn.mp4'],stdin=subprocess.PIPE)
random.seed(3); last=None
for fi in range(TOTF):
    raw=dec.stdout.read(W*H*3)
    if len(raw)<W*H*3: raw=last
    last=raw
    fr=Image.frombytes('RGB',(W,H),raw).convert('RGBA')
    for f0,f1,img,sh in SUBS:
        if f0<=fi<f1:
            sc=pop(fi-f0); im=img if sc==1.0 else img.resize((max(1,int(img.width*sc)),max(1,int(img.height*sc))),Image.BILINEAR)
            dx=random.randint(-7,7) if (sh and 6<=fi-f0<16) else 0
            fr.alpha_composite(im,(int((W-im.width)/2+dx),int(CY-im.height/2)))
    enc.stdin.write(fr.convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()
print('total',TOTF/FPS)
