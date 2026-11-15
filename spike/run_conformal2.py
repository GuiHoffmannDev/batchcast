"""Conformal MULTIPLICATIVO: escala a faixa em torno da mediana do modelo.

A primeira tentativa usou CQR, que aplica deslocamento aditivo. Falhou porque a
faixa do Chronos-2 esta larga de forma multiplicativa, cerca de 3 vezes, e um
deslocamento constante nao corrige isso. A reinterpolacao linear dos quantis
internos tambem destruiu a mediana e piorou o MASE.

Aqui: para cada ponto de calibracao, razao
    r = |y - mediana| / meia_largura
O quantil (1-alpha) de r por canal da o fator de escala s. A faixa nova e
    mediana +/- s * meia_largura
A MEDIANA NAO MUDA, logo o MASE fica identico ao zero-shot por construcao, e todo
o efeito aparece na calibracao e na perda quantilica. Esse e o teste honesto.
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

ALPHA = 0.20
MED = len(QUANTILES) // 2          # indice de q0.5


def scale_quantiles(qq, s):
    """Escala todos os quantis em torno de q0.5 pelo fator s (por canal)."""
    med = qq[:, :, MED][:, :, None]
    return med + (qq - med) * s[:, None, None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("release"); ap.add_argument("--out", required=True)
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--contexts", default="32,64,96,128,192")
    a = ap.parse_args()

    y = load(a.release, "uhlendorff2026", SHARED)
    ctxs = [int(x) for x in a.contexts.split(",")]
    camps = sorted({campaign(k) for k in y})
    rng = np.random.default_rng(a.seed)
    sh = list(np.array(camps)[rng.permutation(len(camps))])
    folds = [list(sh[i::a.folds]) for i in range(a.folds)]

    pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
    cache = {}
    with torch.no_grad():
        for k in sorted(y):
            X = y[k]["X"]; T = X.shape[1]
            for C in ctxs:
                for cut in windows(T, C, HORIZON, N_ORIGINS):
                    ctx, tgt = X[:, cut - C:cut], X[:, cut:cut + HORIZON]
                    if not (np.isfinite(ctx).all() and np.isfinite(tgt).all()):
                        continue
                    q, _ = pipe.predict_quantiles(ctx[None, ...].astype(np.float32),
                                                  prediction_length=HORIZON)
                    cache[(k, cut, C)] = (q[0].numpy(), tgt.copy(), ctx.copy())
    print(f"{len(cache)} janelas em cache", flush=True)

    rows = []
    for i, test_camps in enumerate(folds):
        test_runs = [k for k in y if campaign(k) in test_camps]
        cal_runs = [k for k in y if campaign(k) not in test_camps]
        assert not (set(test_runs) & set(cal_runs))

        S = {}
        for C in ctxs:
            rs = []
            for k in cal_runs:
                for cut in windows(y[k]["X"].shape[1], C, HORIZON, N_ORIGINS):
                    if (k, cut, C) not in cache:
                        continue
                    qq, tgt, _ = cache[(k, cut, C)]
                    med = qq[:, :, MED]
                    half = np.maximum(np.abs(qq[:, :, -1] - qq[:, :, 0]) / 2.0, 1e-12)
                    rs.append(np.abs(tgt - med) / half)
            if not rs:
                continue
            R = np.concatenate([r.reshape(r.shape[0], -1) for r in rs], axis=1)
            n = R.shape[1]
            lvl = min(1.0, (1 - ALPHA) * (1 + 1.0 / n))
            S[C] = np.quantile(R, lvl, axis=1)

        for k in test_runs:
            for C in ctxs:
                if C not in S:
                    continue
                for cut in windows(y[k]["X"].shape[1], C, HORIZON, N_ORIGINS):
                    if (k, cut, C) not in cache:
                        continue
                    qq, tgt, ctx = cache[(k, cut, C)]
                    adj = scale_quantiles(qq, S[C])
                    pt = adj[:, :, MED]
                    mm, ww, cc = mase(tgt, pt, ctx), wql(tgt, adj, ctx), coverage(tgt, adj)
                    for v, chn in enumerate(y[k]["dense"]):
                        rows.append(dict(arm="K_chronos2_conformal_mult", run_id=k, cut=cut,
                                         context=C, channel=chn, mase=mm[v], wql=ww[v],
                                         coverage=cc[v], seconds=np.nan, fold=i))
        print(f"  dobra {i}: fator de escala por contexto = "
              f"{ {c: np.round(S[c], 3).tolist() for c in sorted(S)} }", flush=True)

    d = pd.DataFrame(rows)
    d.to_csv(a.out, index=False)
    print(f"\nescrito {a.out}: {len(d)} linhas, {d.run_id.nunique()} corridas")
    print(d.groupby("arm")[["mase", "wql", "coverage"]].median().round(4).to_string())
    print("\ncobertura por contexto (nominal 0,80):")
    print(d.groupby("context").coverage.median().round(3).to_string())


if __name__ == "__main__":
    main()
