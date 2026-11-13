"""Braco E: linhas de base triviais. Se o modelo de fundacao nao bate isto, nada mais importa."""
import numpy as np

from metrics import QUANTILES


def _quantiles_from_residuals(point, resid_std):
    """Faixa gaussiana em torno do ponto, com desvio estimado do contexto."""
    from scipy.stats import norm
    z = norm.ppf(QUANTILES)[None, None, :]
    return point[:, :, None] + resid_std[:, None, None] * z


def last_value(context, horizon):
    """Repete o ultimo valor observado."""
    point = np.repeat(context[:, -1:], horizon, axis=1)
    resid = np.abs(np.diff(context, axis=1)).std(axis=1) * np.sqrt(np.arange(1, horizon + 1)).mean()
    return point, _quantiles_from_residuals(point, resid)


def seasonal_naive(context, horizon, period):
    """Repete o ultimo ciclo de tamanho `period`."""
    if period <= 0 or period > context.shape[1]:
        return last_value(context, horizon)
    tail = context[:, -period:]
    reps = int(np.ceil(horizon / period))
    point = np.tile(tail, (1, reps))[:, :horizon]
    resid = np.abs(context[:, period:] - context[:, :-period]).std(axis=1)
    return point, _quantiles_from_residuals(point, np.maximum(resid, 1e-9))


def linear_extrap(context, horizon, fit_len=48):
    """Ajusta reta na cauda do contexto e extrapola."""
    V, C = context.shape
    n = min(fit_len, C)
    x = np.arange(n, dtype=float)
    xf = np.arange(C, C + horizon, dtype=float) - (C - n)
    point = np.empty((V, horizon))
    resid = np.empty(V)
    for v in range(V):
        y = context[v, -n:]
        a, b = np.polyfit(x, y, 1)
        point[v] = a * xf + b
        resid[v] = np.std(y - (a * x + b))
    resid = resid * np.sqrt(np.arange(1, horizon + 1)).mean()
    return point, _quantiles_from_residuals(point, np.maximum(resid, 1e-9))


def drift(context, horizon):
    """Ultimo valor mais tendencia media global do contexto (Hyndman drift)."""
    V, C = context.shape
    slope = (context[:, -1] - context[:, 0]) / max(C - 1, 1)
    steps = np.arange(1, horizon + 1)[None, :]
    point = context[:, -1:] + slope[:, None] * steps
    resid = np.abs(np.diff(context, axis=1)).std(axis=1) * np.sqrt(steps).mean()
    return point, _quantiles_from_residuals(point, np.maximum(resid, 1e-9))
