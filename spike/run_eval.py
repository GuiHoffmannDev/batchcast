"""Spike: braços A (multivariado), B (univariado por canal) e E (triviais) na levedura.

Origem rolante por corrida, varredura de tamanho de contexto.
Saida: CSV longo com uma linha por (braco, corrida, origem, contexto, canal).
"""
import argparse, itertools, json, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import baselines
from data_yeast import load
from metrics import QUANTILES, coverage, mase, wql

HORIZON = 64            # 16 h a 0.25 h
CONTEXTS = [32, 64, 96, 128, 192]
N_ORIGINS = 3


def windows(T, context, horizon, n_origins):
    """Origens igualmente espacadas que caibam em [context, T-horizon]."""
    lo, hi = context, T - horizon
    if hi < lo:
        return []
    if n_origins == 1 or hi == lo:
        return [hi]
    return sorted({int(round(x)) for x in np.linspace(lo, hi, n_origins)})


def eval_rows(arm, run, cut, context_len, y_true, point, q_pred, ctx, elapsed):
    m = mase(y_true, point, ctx)
    w = wql(y_true, q_pred, ctx)
    c = coverage(y_true, q_pred)
    rows = []
    for v, ch in enumerate(run["dense"]):
        rows.append(dict(arm=arm, run_id=run["run_id"], cut=cut, context=context_len,
                         channel=ch, mase=m[v], wql=w[v], coverage=c[v],
                         seconds=elapsed / len(run["dense"])))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("release")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--limit-runs", type=int, default=0)
    ap.add_argument("--contexts", default=",".join(map(str, CONTEXTS)))
    ap.add_argument("--arms", default="A,B,E")
    args = ap.parse_args()

    contexts = [int(x) for x in args.contexts.split(",")]
    arms = args.arms.split(",")
    runs = load(args.release)
    keys = sorted(runs)
    if args.limit_runs:
        keys = keys[: args.limit_runs]
    print(f"{len(keys)} corridas, contextos={contexts}, horizonte={HORIZON}, braços={arms}", flush=True)

    fc = None
    if {"A", "B"} & set(arms):
        import timesfm
        t0 = time.time()
        fc = timesfm.TimesFM3Forecaster.from_pretrained(
            "google/timesfm-3.0-pytorch", device=args.device)
        print(f"modelo carregado em {time.time()-t0:.1f}s (device={args.device})", flush=True)

    rows = []
    for i, k in enumerate(keys):
        run = runs[k]
        X, T = run["X"], run["X"].shape[1]
        for C in contexts:
            for cut in windows(T, C, HORIZON, N_ORIGINS):
                ctx = X[:, cut - C: cut]
                y = X[:, cut: cut + HORIZON]
                if not np.isfinite(ctx).all() or not np.isfinite(y).all():
                    continue

                if "A" in arms:
                    t0 = time.time()
                    o = fc.predict(context=ctx, horizon=HORIZON, return_quantiles=True)
                    dt = time.time() - t0
                    rows += eval_rows("A_tfm3_multivar", run, cut, C, y,
                                      np.asarray(o.forecast), np.asarray(o.quantiles), ctx, dt)

                if "B" in arms:
                    t0 = time.time()
                    pts, qs = [], []
                    for v in range(ctx.shape[0]):
                        ov = fc.predict(context=ctx[v: v + 1], horizon=HORIZON,
                                        return_quantiles=True)
                        pts.append(np.asarray(ov.forecast)[0])
                        qs.append(np.asarray(ov.quantiles)[0])
                    dt = time.time() - t0
                    rows += eval_rows("B_tfm3_univar", run, cut, C, y,
                                      np.stack(pts), np.stack(qs), ctx, dt)

                if "E" in arms:
                    for name, fn in [
                        ("E_last_value", lambda: baselines.last_value(ctx, HORIZON)),
                        ("E_drift", lambda: baselines.drift(ctx, HORIZON)),
                        ("E_linear_extrap", lambda: baselines.linear_extrap(ctx, HORIZON)),
                        ("E_seasonal_naive", lambda: baselines.seasonal_naive(ctx, HORIZON, 96)),
                    ]:
                        t0 = time.time()
                        p, q = fn()
                        rows += eval_rows(name, run, cut, C, y, p, q, ctx, time.time() - t0)
        print(f"  [{i+1}/{len(keys)}] {k} -> {len(rows)} linhas", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    print(f"\nescrito {args.out}: {len(df)} linhas")
    print(df.groupby("arm")[["mase", "wql", "coverage"]].median().round(4).to_string())


if __name__ == "__main__":
    main()
