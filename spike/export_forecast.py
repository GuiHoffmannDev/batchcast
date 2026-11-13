"""Exporta UMA previsao real do Chronos-2 para o site desenhar.

A janela nao e escolhida a dedo: e a janela de biomassa cujo MASE fica mais perto da MEDIANA
do braco C_chronos2_multivar no contexto pedido, lida do CSV de resultados. Assim o grafico do
site mostra um caso tipico, nem o melhor nem o pior.

Uso: python -I spike/export_forecast.py data/atlas/release results/yeast_chronos.csv site/data/forecast.json
"""
import argparse, json, sys
import numpy as np, pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from chronos import Chronos2Pipeline
from data_yeast import DT_H, load
from metrics import mase

ARM, CHANNEL, HORIZON = "C_chronos2_multivar", "permittivity_pF_cm", 64

ap = argparse.ArgumentParser()
ap.add_argument("release"); ap.add_argument("results"); ap.add_argument("out")
ap.add_argument("--context", type=int, default=32)   # 32 pontos = 8 h
a = ap.parse_args()

d = pd.read_csv(a.results)
d = d[(d.arm == ARM) & (d.context == a.context) & (d.channel == CHANNEL)]
assert len(d) > 0, "nenhuma janela para esse braco/contexto/canal"
median = d.mase.median()
pick = d.loc[(d.mase - median).abs().idxmin()]

run = load(a.release)[pick.run_id]
X, dense, cut, C = run["X"], run["dense"], int(pick.cut), a.context
ti = dense.index(CHANNEL)
ctx, y = X[:, cut - C:cut], X[:, cut:cut + HORIZON]
assert np.isfinite(ctx).all() and np.isfinite(y).all()

p = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
q, mu = p.predict_quantiles(ctx[None, ...], prediction_length=HORIZON)
q, mu = q[0].numpy(), mu[0].numpy()          # (canais, H, 9), (canais, H)

# A previsao refeita tem que reproduzir a metrica gravada, senao o grafico nao e o do teste.
again = float(mase(y, mu, ctx)[ti])
assert abs(again - pick.mase) < 1e-3 * max(1.0, pick.mase), (again, pick.mase)

r = lambda v: [round(float(x), 4) for x in v]
out = dict(
    model="Chronos-2 (multivariate, zero-shot)", channel=CHANNEL, run_id=pick.run_id,
    step_h=DT_H, context_h=C * DT_H, horizon_h=HORIZON * DT_H,
    mase=round(again, 3), median_mase=round(float(median), 3), n_windows=int(len(d)),
    history=r(ctx[ti]), actual=r(y[ti]), point=r(mu[ti]),
    quantiles=[r(q[ti, :, k]) for k in range(q.shape[2])],   # 0.1 ... 0.9
)
__import__("pathlib").Path(a.out).parent.mkdir(parents=True, exist_ok=True)
json.dump(out, open(a.out, "w"))
print(f"{pick.run_id} cut={cut} MASE={again:.3f} (mediana {median:.3f}, n={len(d)}) -> {a.out}")
