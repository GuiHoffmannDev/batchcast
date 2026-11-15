"""Predicao conformal sobre o Chronos-2 zero-shot, sem treinar nada.

Se isto igualar a calibracao obtida por ajuste fino, o ganho de calibracao do
"modelo vertical" e apenas uma correcao estatistica de manual, e portanto trivial
de copiar. Esse teste precisa existir antes de qualquer argumento de produto.

Metodo: CQR (Romano, Patterson, Candes 2019). No conjunto de calibracao calcula
  E_i = max(q_lo - y, y - q_hi)
e toma o quantil empirico ajustado. Depois aplica [q_lo - Q, q_hi + Q] no teste.
Intervalo largo demais da Q negativo, o que encolhe a faixa. E o nosso caso.

Mesmas dobras por campanha do braco em distribuicao, para comparacao direta.
"""
import argparse, sys
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, "spike")
from chronos import Chronos2Pipeline
from data_bioprocess import SHARED, load
from metrics import QUANTILES, coverage, mase, wql
from run_eval import HORIZON, N_ORIGINS, windows
from run_indist import campaign

ALPHA = 0.20                      # faixa nominal de 80%, igual a 0.1-0.9
LO, HI = 0, len(QUANTILES) - 1    # indices de q0.1 e q0.9


def predict_all(pipe, runs, contexts):
    """Cacheia previsao zero-shot de toda janela: (quantis, alvo, contexto)."""
    cache = {}
    with torch.no_grad():
        for k in sorted(runs):
            X = runs[k]["X"]; T = X.shape[1]
            for C in contexts:
                for cut in windows(T, C, HORIZON, N_ORIGINS):
                    ctx, y = X[:, cut - C:cut], X[:, cut:cut + HORIZON]
                    if not (np.isfinite(ctx).all() and np.isfinite(y).all()):
                        continue
                    q, _ = pipe.predict_quantiles(ctx[None, ...].astype(np.float32),
                                                  prediction_length=HORIZON)
                    cache[(k, cut, C)] = (q[0].numpy(), y.copy(), ctx.copy())
    return cache


def conformity(qq, y):
    """E = max(q_lo - y, y - q_hi) por canal e passo."""
    lo = np.minimum(qq[:, :, LO], qq[:, :, HI])
    hi = np.maximum(qq[:, :, LO], qq[:, :, HI])
    return np.maximum(lo - y, y - hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("release")
    ap.add_argument("--out", required=True)
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--contexts", default="32,64,96,128,192")
    a = ap.parse_args()

    y = load(a.release, "uhlendorff2026", SHARED)
    assert len(y) == 52
    ctxs = [int(x) for x in a.contexts.split(",")]
    camps = sorted({campaign(k) for k in y})
    rng = np.random.default_rng(a.seed)
    sh = list(np.array(camps)[rng.permutation(len(camps))])
    folds = [list(sh[i::a.folds]) for i in range(a.folds)]

    pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
    print("prevendo zero-shot em todas as janelas (cache)...", flush=True)
    cache = predict_all(pipe, y, ctxs)
    print(f"  {len(cache)} janelas em cache", flush=True)

    rows = []
    for i, test_camps in enumerate(folds):
        test_runs = [k for k in y if campaign(k) in test_camps]
        cal_runs = [k for k in y if campaign(k) not in test_camps]
        assert not (set(test_runs) & set(cal_runs))

        # Q por CANAL, calibrado so no conjunto de calibracao
        Qs = {}
        for C in ctxs:
            E = [conformity(*cache[(k, cut, C)][:2])
                 for k in cal_runs
                 for cut in windows(y[k]["X"].shape[1], C, HORIZON, N_ORIGINS)
                 if (k, cut, C) in cache]
            if not E:
                continue
            Eall = np.concatenate([e.reshape(e.shape[0], -1) for e in E], axis=1)  # (V, n)
            n = Eall.shape[1]
            lvl = min(1.0, (1 - ALPHA) * (1 + 1.0 / n))
            Qs[C] = np.quantile(Eall, lvl, axis=1)        # (V,)

        for k in test_runs:
            for C in ctxs:
                if C not in Qs:
                    continue
                for cut in windows(y[k]["X"].shape[1], C, HORIZON, N_ORIGINS):
                    if (k, cut, C) not in cache:
                        continue
                    qq, tgt, ctx = cache[(k, cut, C)]
                    Q = Qs[C][:, None, None]
                    adj = qq.copy()
                    lo = np.minimum(qq[:, :, LO], qq[:, :, HI])
                    hi = np.maximum(qq[:, :, LO], qq[:, :, HI])
                    adj[:, :, LO] = lo - Q[:, :, 0]
                    adj[:, :, HI] = hi + Q[:, :, 0]
                    # reinterpola os quantis internos entre a nova faixa
                    frac = (QUANTILES - QUANTILES[LO]) / (QUANTILES[HI] - QUANTILES[LO])
                    adj = (adj[:, :, LO][:, :, None]
                           + (adj[:, :, HI] - adj[:, :, LO])[:, :, None] * frac[None, None, :])
                    pt = adj[:, :, len(QUANTILES) // 2]
                    mm, ww, cc = mase(tgt, pt, ctx), wql(tgt, adj, ctx), coverage(tgt, adj)
                    for v, chn in enumerate(y[k]["dense"]):
                        rows.append(dict(arm="K_chronos2_conformal", run_id=k, cut=cut,
                                         context=C, channel=chn, mase=mm[v], wql=ww[v],
                                         coverage=cc[v], seconds=np.nan, fold=i))
        print(f"  dobra {i}: {len(cal_runs)} calibracao / {len(test_runs)} teste, "
              f"Q por contexto = { {c: np.round(Qs[c], 3).tolist() for c in sorted(Qs)} }",
              flush=True)

    d = pd.DataFrame(rows)
    d.to_csv(a.out, index=False)
    print(f"\nescrito {a.out}: {len(d)} linhas, {d.run_id.nunique()} corridas (esperado 52)")
    print(d.groupby("arm")[["mase", "wql", "coverage"]].median().round(4).to_string())
    print("\ncobertura por contexto (nominal 0,80):")
    print(d.groupby("context").coverage.median().round(3).to_string())


if __name__ == "__main__":
    main()
