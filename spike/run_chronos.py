"""Braco C: Chronos-2 (Apache-2.0, 119M) nas MESMAS janelas do run_eval.

Tres variantes: multivariado conjunto, univariado por canal, e com covariaveis
passado-futuro nos setpoints de receita.
"""
import argparse, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, "spike")
from chronos import Chronos2Pipeline
from data_yeast import load
from metrics import coverage, mase, wql
from run_eval import HORIZON, windows, N_ORIGINS

KNOWN = ["temperature_C", "pH"]   # setpoints de receita, conhecidos a frente

ap = argparse.ArgumentParser()
ap.add_argument("release"); ap.add_argument("--out", required=True)
ap.add_argument("--contexts", default="32,64,96,128,192")
a = ap.parse_args()
contexts = [int(x) for x in a.contexts.split(",")]

runs = load(a.release)
p = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
print(f"Chronos-2 carregado; {len(runs)} corridas; contextos={contexts}", flush=True)

rows = []


def rec(arm, run, cut, C, y, point, q, ctx, dt, chans):
    m, w, c = mase(y, point, ctx), wql(y, q, ctx), coverage(y, q)
    for v, ch in enumerate(chans):
        rows.append(dict(arm=arm, run_id=run["run_id"], cut=cut, context=C, channel=ch,
                         mase=m[v], wql=w[v], coverage=c[v], seconds=dt / len(chans)))


for i, k in enumerate(sorted(runs)):
    run = runs[k]; X = run["X"]; dense = run["dense"]; T = X.shape[1]
    ki = [dense.index(c) for c in KNOWN]
    for C in contexts:
        for cut in windows(T, C, HORIZON, N_ORIGINS):
            ctx = X[:, cut - C:cut]; y = X[:, cut:cut + HORIZON]
            if not (np.isfinite(ctx).all() and np.isfinite(y).all()):
                continue

            t0 = time.time()
            q, mu = p.predict_quantiles(ctx[None, ...], prediction_length=HORIZON)
            rec("C_chronos2_multivar", run, cut, C, y,
                mu[0].numpy(), q[0].numpy(), ctx, time.time() - t0, dense)

            t0 = time.time()
            q, mu = p.predict_quantiles([ctx[v] for v in range(ctx.shape[0])],
                                        prediction_length=HORIZON)
            pt = np.concatenate([m.numpy().reshape(1, -1) for m in mu], 0)
            qq = np.concatenate([x.numpy().reshape(1, HORIZON, -1) for x in q], 0)
            rec("C_chronos2_univar", run, cut, C, y, pt, qq, ctx, time.time() - t0, dense)

            # covariaveis: alvo = permittivity, setpoints conhecidos a frente
            ti = dense.index("permittivity_pF_cm")
            d = [{"target": ctx[ti],
                  "past_covariates": {c: ctx[dense.index(c)] for c in KNOWN},
                  "future_covariates": {c: X[dense.index(c), cut:cut + HORIZON] for c in KNOWN}}]
            t0 = time.time()
            q, mu = p.predict_quantiles(d, prediction_length=HORIZON)
            rec("C_chronos2_covariates", run, cut, C, y[ti:ti + 1],
                mu[0].numpy().reshape(1, -1), q[0].numpy().reshape(1, HORIZON, -1),
                ctx[ti:ti + 1], time.time() - t0, ["permittivity_pF_cm"])
    if (i + 1) % 10 == 0:
        print(f"  [{i+1}/{len(runs)}] {len(rows)} linhas", flush=True)

d = pd.DataFrame(rows); d.to_csv(a.out, index=False)
print(f"\nescrito {a.out}: {len(d)} linhas\n")
print(d.groupby("arm")[["mase", "wql", "coverage"]].median().round(3).to_string())
print()
print(d.pivot_table(index="arm", columns="context", values="mase", aggfunc="median").round(3).to_string())
