"""Deteccao de desvio por faixa de quantis, sem treinar detector.

Linha de base publicada no IndPenSim (PCA, 20 divisoes, 10 bateladas de falha):
  percentil 99.5, k=8 -> falso positivo 16.4%, deteccao 100%, atraso mediano 1.60 h
  percentil 99.9, k=5 -> falso positivo  3.6%, deteccao  94%, atraso mediano 1.45 h

Aqui o sinal de anomalia sai de graca do modelo: conta quantos canais caem fora da
faixa [q0.1, q0.9] prevista. Nenhum ajuste em dado de falha.
"""
import argparse, sys, time
import numpy as np, pandas as pd

sys.path.insert(0, "spike")
from metrics import QUANTILES


def rolling_scores(model_fn, X, context, horizon, stride):
    """Para cada origem, preve e mede a fracao de canais-passos fora da faixa.

    Retorna lista de (indice_do_fim_do_horizonte, score).
    """
    out = []
    T = X.shape[1]
    cut = context
    while cut + horizon <= T:
        ctx = X[:, cut - context:cut]
        y = X[:, cut:cut + horizon]
        if np.isfinite(ctx).all() and np.isfinite(y).all():
            q = model_fn(ctx, horizon)                      # (V, H, Q)
            lo, hi = q[:, :, 0], q[:, :, -1]
            lo, hi = np.minimum(lo, hi), np.maximum(lo, hi)
            outside = (y < lo) | (y > hi)
            # distancia relativa para fora da faixa, mais informativa que so contar
            width = np.maximum(hi - lo, 1e-9)
            excess = np.maximum(np.maximum(lo - y, y - hi), 0.0) / width
            out.append((cut + horizon, float(outside.mean()), float(excess.mean())))
        cut += stride
    return out


def evaluate(scores_by_run, labels, onset_h, dt_h, quantile_grid=(90, 95, 97.5, 99, 99.5, 99.9)):
    """Calibra limiar SO em corridas normais, depois mede em todas. Sem vazamento."""
    normal = [s for rid, ss in scores_by_run.items() if not labels[rid] for _, _, s in ss]
    normal = np.asarray(normal)
    rows = []
    for pct in quantile_grid:
        thr = np.percentile(normal, pct)
        fp_runs, det, delays = 0, 0, []
        n_norm = n_fault = 0
        for rid, ss in scores_by_run.items():
            alarm = [(idx, s) for idx, _, s in ss if s > thr]
            if labels[rid]:
                n_fault += 1
                on = onset_h[rid]
                after = [idx for idx, _ in alarm if idx * dt_h >= on]
                if after:
                    det += 1
                    delays.append(min(after) * dt_h - on)
            else:
                n_norm += 1
                if alarm:
                    fp_runs += 1
        rows.append(dict(percentil=pct, limiar=round(thr, 5),
                         falso_positivo_pct=round(100 * fp_runs / max(n_norm, 1), 1),
                         deteccao_pct=round(100 * det / max(n_fault, 1), 1),
                         atraso_mediano_h=round(float(np.median(delays)), 2) if delays else np.nan,
                         n_normal=n_norm, n_falha=n_fault))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print(__doc__)
    print("Use via import. Precisa do IndPenSim carregado para rodar.")
