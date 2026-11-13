"""Transferencia: o desempenho zero-shot se mantem entre cepa, escala e condicao?

Zero-shot nao treina, logo nao ha vazamento possivel. A pergunta e se a acuracia
se degrada em grupos que um modelo por planta teria que reajustar.
"""
import sys
import numpy as np, pandas as pd

d = pd.read_csv(sys.argv[1])
runs = pd.read_csv(sys.argv[2] + "/runs.csv")
d = d[np.isfinite(d.mase)]
m = d.merge(runs[["run_id", "strain", "working_volume_L", "perturbation_type",
                  "temperature_C", "campaign"]], on="run_id", how="left")
assert m.strain.notna().all(), "metadados faltando para alguma corrida"

LONG = m[m.context == m.context.max()]
print(f"usando contexto={m.context.max()} (o unico em que o zero-shot vence), n={len(LONG)}\n")

for col, label in [("strain", "CEPA"), ("working_volume_L", "ESCALA (L)"),
                   ("perturbation_type", "PERTURBACAO")]:
    print("=" * 74)
    print(f"{label}: MASE mediano por braco x grupo")
    print("=" * 74)
    t = LONG.pivot_table(index="arm", columns=col, values="mase", aggfunc="median")
    cols = list(t.columns)
    if len(cols) == 2:
        t["razao"] = (t[cols[1]] / t[cols[0]]).round(2)
    print(t.round(3).to_string())
    n = LONG.groupby(col).run_id.nunique()
    print(f"  corridas por grupo: {dict(n)}\n")

print("=" * 74)
print("DEGRADACAO NA MUDANCA DE ESCALA (0.7 L -> 10 L), por braco")
print("=" * 74)
sc = LONG.pivot_table(index="arm", columns="working_volume_L", values="mase", aggfunc="median")
if sc.shape[1] == 2:
    small, big = sorted(sc.columns)
    sc["piora_pct"] = ((sc[big] - sc[small]) / sc[small] * 100).round(1)
    print(sc.round(3).sort_values("piora_pct").to_string())
    print("\nLeitura: piora_pct baixo = o modelo transfere de escala de bancada para 10 L.")
    print("E exatamente o que quebra um soft sensor ajustado por reator.")

print("\n" + "=" * 74)
print("VARIANCIA ENTRE CAMPANHAS (proxy de robustez entre lotes)")
print("=" * 74)
cv = LONG.groupby(["arm", "campaign"]).mase.median().unstack()
res = pd.DataFrame({"mediana": cv.median(axis=1).round(3),
                    "pior_campanha": cv.max(axis=1).round(3),
                    "melhor_campanha": cv.min(axis=1).round(3)})
res["amplitude"] = (res.pior_campanha - res.melhor_campanha).round(3)
print(res.sort_values("mediana").to_string())
