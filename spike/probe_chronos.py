"""Descobre as formas de saida do Chronos-2 antes de montar o braco C."""
import numpy as np, torch
from chronos import Chronos2Pipeline

p = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
print("carregado")
n = sum(x.numel() for x in p.model.parameters())
print(f"parametros: {n:,}")

rng = np.random.default_rng(0); t = np.arange(192)
ctx = np.stack([np.sin(t / 24) + 0.05 * rng.standard_normal(192),
                np.cos(t / 37), 0.01 * t])

# multivariado: (batch, n_variates, history)
q, m = p.predict_quantiles(np.asarray(ctx)[None, ...], prediction_length=64)
print("multivar -> type(q)", type(q), "len", len(q))
print("  q[0]", tuple(q[0].shape), " m[0]", tuple(m[0].shape))

# com covariaveis via dict
d = [{"target": ctx[0],
      "past_covariates": {"sp1": ctx[1], "sp2": ctx[2]},
      "future_covariates": {"sp1": np.cos(np.arange(192, 256) / 37),
                            "sp2": 0.01 * np.arange(192, 256)}}]
q2, m2 = p.predict_quantiles(d, prediction_length=64)
print("covariates -> q2[0]", tuple(q2[0].shape), " m2[0]", tuple(m2[0].shape))
