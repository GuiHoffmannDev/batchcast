"""Deteccao de desvio em dado REAL, sem vazamento de rotulo.

Desenho: nas campanhas EXP007 e EXP008 os reatores R01/R02 rodaram a 22 C e R03/R04
a 37 C, com cepa, pre-cultura, densidade de mosto, aeracao e volume identicos.
Positivos = 4 corridas a 37 C. A temperatura e REMOVIDA da entrada do modelo, logo a
deteccao tem que vir do efeito biologico em pH, oxigenio, CO2 e permissividade.

Limiar calibrado SO nos negativos. Compara Chronos-2, TimesFM 3.0 e PCA, que e o
metodo da linha de base publicada.
"""
import sys, time
import numpy as np, pandas as pd
sys.path.insert(0, "spike")
from data_yeast import load

BIO = ["pH", "DO_percent", "dCO2_percent", "permittivity_pF_cm"]   # sem temperatura
CONTEXT, HORIZON, STRIDE = 64, 32, 16      # 16 h de contexto, 8 h a frente, passo de 4 h
DT = 0.25

runs = load(sys.argv[1])
meta = pd.read_csv(sys.argv[1] + "/runs.csv").set_index("run_id")

pos = [k for k in runs if meta.loc[k, "temperature_C"] == 37.0]
neg = [k for k in runs if meta.loc[k, "temperature_C"] == 22.0
       and "12 °P" in str(meta.loc[k, "condition"])]
matched = [k for k in neg if k.split(":")[1].split("_")[0] in ("EXP007", "EXP008")]
print(f"positivos (37 C): {len(pos)}")
print(f"negativos (22 C, 12 P): {len(neg)}  dos quais pareados na mesma campanha: {len(matched)}")
assert len(pos) == 4 and len(matched) == 4, "desenho pareado quebrou"


def chans(run):
    idx = [run["dense"].index(c) for c in BIO]
    return run["X"][idx]


def score_run(predict_q, X):
    """Lista de (hora_do_fim, score). Score = excesso relativo fora da faixa 0.1-0.9."""
    out, T, cut = [], X.shape[1], CONTEXT
    while cut + HORIZON <= T:
        ctx, y = X[:, cut - CONTEXT:cut], X[:, cut:cut + HORIZON]
        if np.isfinite(ctx).all() and np.isfinite(y).all():
            q = predict_q(ctx)
            lo, hi = np.minimum(q[:, :, 0], q[:, :, -1]), np.maximum(q[:, :, 0], q[:, :, -1])
            width = np.maximum(hi - lo, 1e-9)
            excess = np.maximum(np.maximum(lo - y, y - hi), 0.0) / width
            out.append(((cut + HORIZON) * DT, float(excess.mean())))
        cut += STRIDE
    return out


def report(name, scores):
    rows = []
    allneg = np.array([s for k in neg for _, s in scores[k]])
    for pct in (90, 95, 97.5, 99, 99.5):
        thr = np.percentile(allneg, pct)
        fp = sum(any(s > thr for _, s in scores[k]) for k in neg)
        fpm = sum(any(s > thr for _, s in scores[k]) for k in matched)
        det, first = 0, []
        for k in pos:
            a = [h for h, s in scores[k] if s > thr]
            if a:
                det += 1
                first.append(min(a))
        rows.append(dict(percentil=pct, limiar=round(thr, 4),
                         FP_amplo_pct=round(100 * fp / len(neg), 1),
                         FP_pareado_pct=round(100 * fpm / len(matched), 1),
                         deteccao_pct=round(100 * det / len(pos), 1),
                         **{"alarme_1o_h": round(float(np.median(first)), 2) if first else np.nan}))
    d = pd.DataFrame(rows)
    print(f"\n--- {name} ---")
    print(d.to_string(index=False))
    return d


results = {}

# --- Chronos-2 (Apache-2.0, 119M) ---
from chronos import Chronos2Pipeline
cp = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
f = lambda ctx: cp.predict_quantiles(ctx[None, ...], prediction_length=HORIZON)[0][0].numpy()
t0 = time.time()
sc = {k: score_run(f, chans(runs[k])) for k in pos + neg}
print(f"Chronos-2: {time.time()-t0:.0f}s, {sum(len(v) for v in sc.values())} janelas")
results["chronos2"] = report("Chronos-2 multivariado, faixa 0.1-0.9", sc)

# --- TimesFM 3.0 (nao comercial, 330M) ---
import timesfm
tf = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", device="cpu")
g = lambda ctx: np.asarray(tf.predict(context=ctx, horizon=HORIZON, return_quantiles=True,
                                      use_symmetric_averaging=True).quantiles)
t0 = time.time()
sc2 = {k: score_run(g, chans(runs[k])) for k in pos + neg}
print(f"TimesFM 3.0: {time.time()-t0:.0f}s")
results["tfm3"] = report("TimesFM 3.0 multivariado, faixa 0.1-0.9", sc2)

# --- PCA, o metodo da linha de base publicada ---
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
L = min(min(chans(runs[k]).shape[1] for k in pos + neg), 240)
train = np.concatenate([chans(runs[k])[:, :L].T for k in neg], 0)
ss = StandardScaler().fit(train)
for nk in (5, 8):
    k_ = min(nk, len(BIO))
    pca = PCA(n_components=k_).fit(ss.transform(train))

    def spe(ctx_unused, X=None):
        raise RuntimeError
    scp = {}
    for k in pos + neg:
        Z = ss.transform(chans(runs[k])[:, :L].T)
        R = Z - pca.inverse_transform(pca.transform(Z))
        e = (R ** 2).sum(1)
        scp[k] = [((i + 1) * DT, float(e[i])) for i in range(len(e))]
    results[f"pca_k{k_}"] = report(f"PCA SPE, k={k_} componentes (metodo da linha de base)", scp)

print("\n" + "=" * 78)
print("LINHA DE BASE PUBLICADA NO IndPenSim, para referencia de ordem de grandeza")
print("=" * 78)
print("  PCA percentil 99.5, k=8 -> falso positivo 16.4%, deteccao 100%, atraso 1.60 h")
print("  PCA percentil 99.9, k=5 -> falso positivo  3.6%, deteccao  94%, atraso 1.45 h")
print("Atencao: processo e falha diferentes, logo comparacao e de ordem de grandeza, nao direta.")
