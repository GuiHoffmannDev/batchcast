"""Braco B': TimesFM 2.5 (Apache-2.0, 200M) nas MESMAS janelas.

Importa porque a licenca do 3.0 proibe usar resultados em decisao comercial.
O 2.5 e Apache-2.0, logo seus numeros podem sustentar decisao de negocio.
Univariado por construcao.
"""
import argparse, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, "spike")
import timesfm
from data_yeast import load
from metrics import coverage, mase, wql
from run_eval import HORIZON, windows, N_ORIGINS

ap = argparse.ArgumentParser()
ap.add_argument("release"); ap.add_argument("--out", required=True)
ap.add_argument("--contexts", default="32,64,96,128,192")
a = ap.parse_args()
contexts = [int(x) for x in a.contexts.split(",")]
maxctx = max(contexts)

runs = load(a.release)
m = timesfm.TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
# torch.compile na CPU travou por mais de 20 min neste modelo; desligado de proposito.
m.torch_compile = False
print("pesos carregados, compilando config...", flush=True)
m.compile(timesfm.ForecastConfig(max_context=maxctx, max_horizon=HORIZON,
                                 normalize_inputs=True, use_continuous_quantile_head=True,
                                 fix_quantile_crossing=True, per_core_batch_size=8))
print(f"TimesFM 2.5 compilado; {len(runs)} corridas", flush=True)

rows = []
for i, k in enumerate(sorted(runs)):
    run = runs[k]; X = run["X"]; dense = run["dense"]; T = X.shape[1]
    for C in contexts:
        for cut in windows(T, C, HORIZON, N_ORIGINS):
            ctx = X[:, cut - C:cut]; y = X[:, cut:cut + HORIZON]
            if not (np.isfinite(ctx).all() and np.isfinite(y).all()):
                continue
            t0 = time.time()
            pt, q = m.forecast(horizon=HORIZON, inputs=[ctx[v] for v in range(ctx.shape[0])])
            dt = time.time() - t0
            pt = np.asarray(pt)                       # (V, H)
            q = np.asarray(q)                         # (V, H, Q+?) -> descarta col. media se houver
            if q.shape[-1] == 10:
                q = q[..., 1:]
            mm, ww, cc = mase(y, pt, ctx), wql(y, q, ctx), coverage(y, q)
            for v, ch in enumerate(dense):
                rows.append(dict(arm="Bp_tfm25_univar", run_id=k, cut=cut, context=C,
                                 channel=ch, mase=mm[v], wql=ww[v], coverage=cc[v],
                                 seconds=dt / len(dense)))
    if (i + 1) % 10 == 0:
        print(f"  [{i+1}/{len(runs)}] {len(rows)} linhas", flush=True)

d = pd.DataFrame(rows); d.to_csv(a.out, index=False)
print(f"\nescrito {a.out}: {len(d)} linhas\n")
print(d.groupby("arm")[["mase", "wql", "coverage"]].median().round(3).to_string())
print()
print(d.pivot_table(index="arm", columns="context", values="mase", aggfunc="median").round(3).to_string())
