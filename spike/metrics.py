"""Metricas de previsao. Convencoes da GIFT-Eval: MASE por canal e perda quantilica ponderada."""
import numpy as np

QUANTILES = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])


def mase(y_true, y_pred, context, seasonality=1):
    """MASE por canal. Escala = MAE do naive sazonal dentro do contexto.

    y_true, y_pred: (V, H). context: (V, C).
    Retorna (V,) com nan onde a escala degenera.
    """
    scale = np.mean(np.abs(context[:, seasonality:] - context[:, :-seasonality]), axis=1)
    scale = np.where(scale < 1e-12, np.nan, scale)
    return np.mean(np.abs(y_true - y_pred), axis=1) / scale


def wql(y_true, q_pred, context, quantiles=QUANTILES, seasonality=1):
    """Perda quantilica ponderada por canal, normalizada pela mesma escala do MASE.

    y_true: (V, H). q_pred: (V, H, Q).
    """
    y = y_true[:, :, None]
    diff = y - q_pred
    qs = quantiles[None, None, :]
    pin = np.maximum(qs * diff, (qs - 1.0) * diff)          # perda pinball
    loss = 2.0 * pin.mean(axis=(1, 2))                      # media sobre H e Q
    scale = np.mean(np.abs(context[:, seasonality:] - context[:, :-seasonality]), axis=1)
    scale = np.where(scale < 1e-12, np.nan, scale)
    return loss / scale


def coverage(y_true, q_pred, lo=0, hi=8):
    """Cobertura empirica da faixa [q_lo, q_hi] por canal. Esperado 0.8 para 0.1-0.9."""
    low, high = q_pred[:, :, lo], q_pred[:, :, hi]
    inside = (y_true >= np.minimum(low, high)) & (y_true <= np.maximum(low, high))
    return inside.mean(axis=1)


def smape(y_true, y_pred):
    d = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    d = np.where(d < 1e-12, np.nan, d)
    return np.nanmean(np.abs(y_true - y_pred) / d, axis=1)
