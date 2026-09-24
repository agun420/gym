import statistics as st, sys, random
from collections import defaultdict
sys.path.insert(0,'.')
import backtest_v2 as bt   # re-runs loaders; we reuse its functions
from engine import gates
random.seed(5)
def collect(S,bench,theme):
    B=S[bench]; bi={d:i for i,d in enumerate(B["d"])}; bo=[]; allobs=[]
    for sym,s in S.items():
        if sym==bench: continue
        R=bt.rsi(s["c"])
        for i in range(21,len(s["c"])-5):
            if s["d"][i] not in bi: continue
            pct=s["c"][i]/s["c"][i-1]-1; av=sum(s["v"][i-20:i])/20
            w=max(0,i-251); lows=s["l"][w:i+1]; j=lows.index(min(lows))+w
            t=bt.trade(s,i)
            if not t: continue
            r,k=t; bk=bi.get(s["d"][k])
            if bk is None: continue
            c=dict(sym=sym,theme=theme.get(sym,sym),price=s["c"][i],pct=pct,rsi=R[i],
                   paced_relvol=s["v"][i]/av if av>0 else None,off_high=(s["h"][i]-s["c"][i])/s["h"][i],
                   low52_age_days=i-j,alpha=r-(B["c"][bk]/B["c"][bi[s["d"][i]]]-1))
            allobs.append(c)
            if pct>0.05: bo.append(c)
    return bo,allobs
def G(c):
    return {g.split()[0] for g in gates(c)}
def m(sel): return (st.mean(c["alpha"] for c in sel)*100, len(sel)) if sel else (float('nan'),0)
for name,S,bench,th in [("SMALL",bt.load(bt.SMALL),"IWM",bt.tsm),("LARGE",bt.L,"SPY",{}),("CRYPTO",bt.C,"SPY",{})]:
    bo,allobs=collect(S,bench,th)
    print(f"\n### {name}  breakouts n={len(bo)}   all-breakout alpha {m(bo)[0]:+.2f}%")
    for g in ["R11","R4","R9","R27"]:
        ok=[c for c in bo if g not in G(c)]; bad=[c for c in bo if g in G(c)]
        a1,n1=m(ok); a2,n2=m(bad)
        print(f"  {g:<4} PASS {a1:+6.2f}% (n={n1:<4})  FAIL {a2:+6.2f}% (n={n2:<4})  spread {a1-a2:+6.2f}")
    if name=="SMALL":
        print("  -- small caps by sector (all breakouts) --")
        by=defaultdict(list)
        for c in bo: by[c["theme"]].append(c)
        for t,cs in sorted(by.items(),key=lambda kv:-len(kv[1])):
            print(f"    {t:<11} n={len(cs):<4} alpha {m(cs)[0]:+6.2f}%")
        nb=[c for c in bo if c["theme"]!="biotech"]; b=[c for c in bo if c["theme"]=="biotech"]
        print(f"    >> biotech {m(b)[0]:+.2f}% (n={len(b)})   ex-biotech {m(nb)[0]:+.2f}% (n={len(nb)})")
        nbg=[c for c in nb if not gates(c)]
        print(f"    >> ex-biotech, passing v2 gates: {m(nbg)[0]:+.2f}% (n={len(nbg)})")
