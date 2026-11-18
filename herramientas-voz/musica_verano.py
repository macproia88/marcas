import sys, wave, numpy as np
SAL, DUR = sys.argv[1], float(sys.argv[2])
SR=44100; N=int(SR*DUR); rng=np.random.default_rng(7)
L=np.zeros(N); R=np.zeros(N)
hz=lambda m:440*2**((m-69)/12)
def poner(s,t0,pan=0.0,g=1.0):
    i=int(t0*SR)
    if i>=N: return
    s=s[:N-i]*g; L[i:i+len(s)]+=s*(1-pan); R[i:i+len(s)]+=s*(1+pan)
def marimba(f,d=0.45):
    t=np.arange(int(d*SR))/SR
    return (np.sin(2*np.pi*f*t)+0.35*np.sin(2*np.pi*f*4*t)*np.exp(-t*30))*np.exp(-t*7)*np.minimum(1,t/0.003)
def steel(f,d=0.6):
    t=np.arange(int(d*SR))/SR
    return (np.sin(2*np.pi*f*t)+0.5*np.sin(2*np.pi*f*2.01*t)+0.25*np.sin(2*np.pi*f*3.02*t))*np.exp(-t*5)*np.minimum(1,t/0.004)
def pad(ns,d):
    t=np.arange(int(d*SR))/SR; s=np.zeros_like(t)
    for n in ns:
        for det in (0.997,1.003): s+=np.sign(np.sin(2*np.pi*hz(n)*det*t))*0.15+np.sin(2*np.pi*hz(n)*det*t)*0.5
    a=np.minimum(1,t/0.02)*np.exp(-t*3.5)
    # lowpass simple
    out=np.convolve(s*a,np.ones(24)/24,mode='same'); return out/len(ns)
def bombo():
    t=np.arange(int(0.25*SR))/SR; f=110*np.exp(-t*35)+50
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*12)
def shaker():
    n=int(0.07*SR); x=rng.normal(0,1,n); x=np.diff(x,prepend=0)
    return x*np.exp(-np.arange(n)/SR*60)
def clap():
    n=int(0.15*SR); x=rng.normal(0,1,n); return np.convolve(x,np.ones(6)/6,'same')*np.exp(-np.arange(n)/SR*25)
def bajo(f,d):
    t=np.arange(int(d*SR))/SR; return np.sin(2*np.pi*f*t)*np.minimum(1,t/0.01)*np.exp(-t*4)
BPM=104; b=60/BPM
prog=[(57,[57,60,64]),(53,[53,57,60]),(48,[55,60,64]),(55,[55,59,62])]  # Am F C G
mel=[76,74,72,74,76,79,76,74, 72,69,72,74,72,69,67,69]
t=0; bar=0
while t<DUR:
    raiz,ac=prog[bar%4]
    for k in range(4):
        tb=t+k*b
        poner(bombo(),tb,0,0.9)
        if k in(1,3): poner(clap(),tb,0.1,0.25)
        for h in range(4): poner(shaker(),tb+h*b/4,0.4,0.12 if h%2 else 0.06)
        poner(pad(ac,b*0.5),tb+b/2,-0.2,0.35)       # acorde a contratiempo
        poner(bajo(hz(raiz-12),b*0.45),tb,0,0.5); poner(bajo(hz(raiz-12),b*0.3),tb+b*0.75,0,0.35)
    if bar>=1:
        for j,n in enumerate(mel[(bar%2)*8:(bar%2)*8+8]):
            poner(marimba(hz(n)),t+j*b/2,0.25,0.30)
            if j%4==0: poner(steel(hz(n-12)),t+j*b/2,-0.3,0.12)
    t+=4*b; bar+=1
fade=np.ones(N); nf=int(1.5*SR); fade[-nf:]=np.linspace(1,0,nf); fi=int(0.3*SR); fade[:fi]=np.linspace(0,1,fi)
st=np.stack([L,R],1)*fade[:,None]; st/=np.max(np.abs(st))+1e-9; st*=0.85
w=wave.open(SAL,'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes()); w.close()
