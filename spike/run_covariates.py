"""Braco A2: alvo unico com covariaveis passado-futuro.

Cenario realista de bioprocesso: temperatura e pH sao setpoints de receita, logo
conhecidos para todo o horizonte. Testa se a entrada passado-futuro do TimesFM-3
compra algo sobre o multivariado conjunto e sobre o univariado puro.

Alvo: permittivity_pF_cm, que e proxy de biomassa e o canal de interesse real.
"""
import sys, time
import numpy as np, pandas as pd
sys.path.insert(0, "spike")
import timesfm
import baselines
from data_yeast import load
from metrics import coverage, mase, wql

H = 64
CONTEXTS = [64, 128, 192]
TARGET = "permittivity_pF_cm"
# setpoints de receita, conhecidos a frente numa planta real
KNOWN = ["temperature_C", "pH"]
# medidos, nao conhecidos a frente
PAST_ONLY = ["DO_percent", "dCO2_percent"]

runs = load(sys.argv[1])
out_csv = sys.argv[2]
fc = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", device="cpu")
print(f"{len(runs)} corridas; alvo={TARGET}; conhecidos={KNOWN}; so-passado={PAST_ONLY}", flush=True)

rows = []
for i, k in enumerate(sorted(runs)):
    run = runs[k]
    X, dense = run["X"], run["dense"]
    ti = dense.index(TARGET)
    ki = [dense.index(c) for c in KNOWN]
    pi = [dense.index(c) for c in PAST_ONLY]
    T = X.shape[1]
    for C in CONTEXTS:
        for cut in sorted({int(round(x)) for x in np.linspace(C, T - H, 3)}):
            ctx_all = X[:, cut - C:cut]
            y = X[ti:ti + 1, cut:cut + H]
            if not (np.isfinite(ctx_all).all() and np.isfinite(X[:, cut:cut + H]).all()):
                continue
            tgt_ctx = ctx_all[ti:ti + 1]

            def rec(arm, p, q, dt):
                rows.append(dict(arm=arm, run_id=k, cut=cut, context=C, channel=TARGET,
                                 mase=mase(y, p, tgt_ctx)[0], wql=wql(y, q, tgt_ctx)[0],
                                 coverage=coverage(y, q)[0], seconds=dt))

            # A2: alvo + covariaveis passado-futuro (setpoints) + so-passado (medidos)
            pf = X[np.ix_(ki, range(cut - C, cut + H))]
            po = ctx_all[pi]
            t0 = time.time()
            o = fc.predict(context=tgt_ctx, horizon=H, return_quantiles=True,
                           past_future_covariates=pf, past_only_covariates=po,
                           use_symmetric_averaging=True)
            rec("A2_tfm3_covariates", np.asarray(o.forecast), np.asarray(o.quantiles), time.time() - t0)

            # A2b: alvo + so os setpoints conhecidos, sem covariavel so-passado
            t0 = time.time()
            o = fc.predict(context=tgt_ctx, horizon=H, return_quantiles=True,
                           past_future_covariates=pf, use_symmetric_averaging=True)
            rec("A2b_tfm3_setpoints_only", np.asarray(o.forecast), np.asarray(o.quantiles), time.time() - t0)

            # A: multivariado conjunto, recorta o canal alvo
            t0 = time.time()
            o = fc.predict(context=ctx_all, horizon=H, return_quantiles=True,
                           use_symmetric_averaging=True)
            dt = time.time() - t0
            rec("A_tfm3_multivar", np.asarray(o.forecast)[ti:ti + 1],
                np.asarray(o.quantiles)[ti:ti + 1], dt)

            # B: univariado puro no canal alvo
            t0 = time.time()
            o = fc.predict(context=tgt_ctx, horizon=H, return_quantiles=True,
                           use_symmetric_averaging=True)
            rec("B_tfm3_univar", np.asarray(o.forecast), np.asarray(o.quantiles), time.time() - t0)

            # E: triviais no canal alvo
            for nm, fn in [("E_last_value", lambda: baselines.last_value(tgt_ctx, H)),
                           ("E_drift", lambda: baselines.drift(tgt_ctx, H)),
                           ("E_linear_extrap", lambda: baselines.linear_extrap(tgt_ctx, H))]:
                t0 = time.time(); p, q = fn(); rec(nm, p, q, time.time() - t0)
    if (i + 1) % 10 == 0:
        print(f"  [{i+1}/{len(runs)}] {len(rows)} linhas", flush=True)

d = pd.DataFrame(rows)
d.to_csv(out_csv, index=False)
print(f"\nescrito {out_csv}: {len(d)} linhas\n")
t = d.groupby("arm").agg(MASE_med=("mase", "median"), WQL_med=("wql", "median"),
                         cob=("coverage", "median"), n=("mase", "size"))
print(t.sort_values("MASE_med").round(3).to_string())
