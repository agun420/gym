import json, random, statistics as st, sys
from collections import defaultdict, Counter
sys.path.insert(0,'.')
from engine import gates, levels, select
random.seed(3)
TR="/root/.claude/projects/-home-user-gym/028ab24c-7c8c-59f7-a6a9-d4ed6476c177/tool-results/"

def load(files):
    S={}
    for f in files:
        for e in json.load(open(TR+f))["data"]["results"]:
            b=[x for x in e["bars"] if x.get("session")=="reg"]
            if len(b)<60: continue
            S[e["symbol"]]=dict(d=[x["begins_at"][:10] for x in b],o=[float(x["open_price"]) for x in b],
                c=[float(x["close_price"]) for x in b],h=[float(x["high_price"]) for x in b],
                l=[float(x["low_price"]) for x in b],v=[float(x["volume"]) for x in b])
    return S

def rsi(c,p=14):
    out=[None]*len(c)
    if len(c)<=p: return out
    g=[max(c[i]-c[i-1],0) for i in range(1,len(c))]; l=[max(c[i-1]-c[i],0) for i in range(1,len(c))]
    ag=sum(g[:p])/p; al=sum(l[:p])/p
    f=lambda a,b: 100.0 if b==0 else 100-100/(1+a/b)
    out[p]=f(ag,al)
    for i in range(p,len(g)):
        ag=(ag*(p-1)+g[i])/p; al=(al*(p-1)+l[i])/p; out[i+1]=f(ag,al)
    return out

def trade(s,i,entry_mode="close"):
    if entry_mode=="close": e=s["c"][i]
    else:
        if i+1>=len(s["c"]): return None
        e=s["o"][i+1]
    stop,tgt=levels(e,s["l"][i])
    last=min(i+5,len(s["c"])-1)
    if last<=i: return None
    for k in range(i+1,last+1):
        if s["l"][k]<=stop: return (stop/e-1,k)
        if s["h"][k]>=tgt:  return (tgt/e-1,k)
    return (s["c"][last]/e-1,last)

def run(name,S,bench,theme):
    B=S[bench]; bi={d:i for i,d in enumerate(B["d"])}
    obs=[]; bydate=defaultdict(list)
    for sym,s in S.items():
        if sym==bench: continue
        R=rsi(s["c"])
        for i in range(21,len(s["c"])-5):
            if s["d"][i] not in bi: continue
            pct=s["c"][i]/s["c"][i-1]-1
            av=sum(s["v"][i-20:i])/20
            w=max(0,i-251); lows=s["l"][w:i+1]; j=lows.index(min(lows))+w
            c=dict(sym=sym,theme=theme.get(sym,sym),price=s["c"][i],pct=pct,rsi=R[i],
                   paced_relvol=(s["v"][i]/av if av>0 else None),
                   off_high=(s["h"][i]-s["c"][i])/s["h"][i] if s["h"][i]>0 else None,
                   low52_age_days=i-j)
            t=trade(s,i)
            if t is None: continue
            r,k=t; b0=bi[s["d"][i]]; bk=bi.get(s["d"][k])
            if bk is None: continue
            c["ret"]=r; c["alpha"]=r-(B["c"][bk]/B["c"][b0]-1)
            t2=trade(s,i,"open"); c["ret_open"]=None if t2 is None else t2[0]
            obs.append(c)
            if pct>0.05: bydate[s["d"][i]].append(c)
    picks=[]; gated=[]
    for d,cs in bydate.items():
        p,_=select(cs,3); picks+=[c for _,c,_ in p]
        gated+=[c for c in cs if not gates(c)]
    allbo=[c for cs in bydate.values() for c in cs]
    pool=defaultdict(list)
    for c in obs: pool[c["sym"]].append(c["alpha"])
    def perm(sel,n=4000):
        m=st.mean(c["alpha"] for c in sel); need=Counter(c["sym"] for c in sel); hit=0
        for _ in range(n):
            dr=[]
            for s_,k in need.items(): dr+=random.choices(pool[s_],k=k)
            if st.mean(dr)>=m: hit+=1
        return hit/n
    def row(lab,sel):
        if not sel: print(f"  {lab:<34} n=0"); return
        a=st.mean(c["alpha"] for c in sel); r=st.mean(c["ret"] for c in sel)
        hit=sum(c["alpha"]>0 for c in sel)/len(sel)
        ro=[c["ret_open"] for c in sel if c["ret_open"] is not None]
        print(f"  {lab:<34} n={len(sel):<5} alpha {a*100:+6.2f}%  hit {hit*100:4.0f}%  ret {r*100:+6.2f}%"
              f"  next-open {st.mean(ro)*100:+6.2f}%  p={perm(sel):.3f}  names={len(set(c['sym'] for c in sel))}")
    print(f"\n=== {name}: {len(S)-1} names, {len(obs)} obs, {len(bydate)} breakout-days ===")
    row("BASELINE (every day, same exits)",obs)
    row("all breakouts >5% (old engine)",allbo)
    row("breakouts passing v2 gates",gated)
    row("ENGINE v2 TOP-3 PICKS",picks)
    if len(gated)>=15:
        from rank import score
        gs=sorted(gated,key=lambda c:score(c)["score"]); t=len(gs)//3
        row("  gated, bottom-third score",gs[:t]); row("  gated, top-third score",gs[-t:])
    fails=Counter()
    for c in allbo:
        for w in gates(c): fails[w.split()[0]]+=1
    print("  gate rejections among breakouts:",dict(fails))

SMALL=["mcp-robinhood-get_equity_historicals-1790099452294.txt","mcp-robinhood-get_equity_historicals-1790099454235.txt","mcp-robinhood-get_equity_historicals-1790099455813.txt"]
LARGE=["mcp-robinhood-get_equity_historicals-1789769733454.txt","mcp-robinhood-get_equity_historicals-1789769734988.txt","mcp-robinhood-get_equity_historicals-1789769739229.txt","mcp-robinhood-get_equity_historicals-1789769740763.txt"]
CRYPTO=["mcp-robinhood-get_equity_historicals-1789769301255.txt"]
tsm={"THM":"gold","DNN":"uranium","ABSI":"biotech","OMER":"biotech","MNOV":"biotech","NNVC":"biotech","ACAD":"biotech",
     "XENE":"biotech","GERN":"biotech","GLUE":"biotech","ARVN":"biotech","CRVS":"biotech","TRVI":"biotech","ANNX":"biotech","AUTL":"biotech",
     "PACB":"biotech","CLOV":"health_ins","AESI":"energy","TALO":"energy","FRO":"energy","HOS":"energy","STLN":"energy","CE":"chemicals",
     "WU":"fintech","MGNI":"adtech","FOSL":"consumer","SFIX":"consumer","SNDL":"cannabis","EH":"aero"}
L=load(LARGE); C=load(CRYPTO); C["SPY"]=L["SPY"]
if __name__=="__main__":
    run("SMALL/MID CAPS -- out-of-sample, the engine's real universe",load(SMALL),"IWM",tsm)
    run("LARGE CAPS (study #2) -- IN-SAMPLE for the ranking function",L,"SPY",{})
    run("CRYPTO PROXIES (study #1) -- out-of-sample",C,"SPY",{})
    