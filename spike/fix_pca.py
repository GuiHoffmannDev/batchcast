"""Linha de base PCA correta: k < numero de canais, senao a reconstrucao e perfeita.

Com 4 canais, k=4 zera o residuo por construcao. Usa k=1,2,3.
"""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "spike")
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from data_yeast import load

BIO = ["pH", "DO_percent", "dCO2_percent", "permittivity_pF_cm"]
DT = 0.25

runs = load(sys.argv[1])
meta = pd.read_csv(sys.argv[1] + "/runs.csv").set_index("run_id")
pos = [k for k in runs if meta.loc[k, "temperature_C"] == 37.0]
neg = [k for k in runs if meta.loc[k, "temperature_C"] == 22.0
       and "12 °P" in str(meta.loc[k, "condition"])]
matched = [k for k in neg if k.split(":")[1].split("_")[0] in ("EXP007", "EXP008")]
assert len(pos) == 4 and len(matched) == 4

def chans(r):
    return runs[r]["X"][[runs[r]["dense"].index(c) for c in BIO]]

L = min(min(chans(k).shape[1] for k in pos + neg), 240)
train = np.concatenate([chans(k)[:, :L].T for k in neg], 0)
ss = StandardScaler().fit(train)

for k_ in (1, 2, 3):
    pca = PCA(n_components=k_).fit(ss.transform(train))
    var = pca.explained_variance_ratio_.sum()
    sc = {}
    for r in pos + neg:
        Z = ss.transform(chans(r)[:, :L].T)
        R = Z - pca.inverse_transform(pca.transform(Z))
        e = (R ** 2).sum(1)
        sc[r] = [((i + 1) * DT, float(e[i])) for i in range(len(e))]
    allneg = np.array([s for r in neg for _, s in sc[r]])
    rows = []
    for pct in (95, 99, 99.5, 99.9):
        thr = np.percentile(allneg, pct)
        fp = sum(any(s > thr for _, s in sc[r]) for r in neg)
        fpm = sum(any(s > thr for _, s in sc[r]) for r in matched)
        det, first = 0, []
        for r in pos:
            a = [h for h, s in sc[r] if s > thr]
            if a:
                det += 1; first.append(min(a))
        rows.append(dict(percentil=pct, limiar=round(thr, 4),
                         FP_amplo_pct=round(100 * fp / len(neg), 1),
                         FP_pareado_pct=round(100 * fpm / len(matched), 1),
                         deteccao_pct=round(100 * det / len(pos), 1),
                         alarme_1o_h=round(float(np.median(first)), 2) if first else np.nan))
    print(f"\n--- PCA SPE, k={k_} de {len(BIO)} canais (variancia explicada {var:.1%}) ---")
    print(pd.DataFrame(rows).to_string(index=False))

print("\n--- separacao bruta do escore, sem limiar ---")
pca = PCA(n_components=2).fit(ss.transform(train))
for grupo, ks in [("negativos 22 C", neg), ("pareados 22 C", matched), ("positivos 37 C", pos)]:
    v = []
    for r in ks:
        Z = ss.transform(chans(r)[:, :L].T)
        R = Z - pca.inverse_transform(pca.transform(Z))
        v.append(float(np.median((R ** 2).sum(1))))
    print(f"  {grupo:16s} SPE mediano por corrida: min={min(v):.3f} med={np.median(v):.3f} max={max(v):.3f}")
