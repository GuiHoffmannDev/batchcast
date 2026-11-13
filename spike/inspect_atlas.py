"""Fase 1: inventario do Bioprocess Atlas. Quantas corridas, canais e pontos por organismo."""
import sys
import pandas as pd

rel = sys.argv[1]
runs = pd.read_csv(f"{rel}/runs.csv")
obs = pd.read_csv(f"{rel}/observations.csv.gz")
ds = pd.read_csv(f"{rel}/datasets.csv")

print("=== datasets.csv ===")
print(ds.to_string(max_colwidth=40))
print(f"\n=== runs.csv: {len(runs)} corridas, colunas: {list(runs.columns)} ===")
print(runs.groupby(["dataset_id", "organism"]).size().to_string())

print(f"\n=== observations: {len(obs):,} linhas, colunas: {list(obs.columns)} ===")

m = obs.merge(runs[["run_id", "dataset_id", "organism"]], on="run_id", how="left")

print("\n=== pontos por dataset, e densidade temporal ===")
g = m.groupby("dataset_id").agg(
    corridas=("run_id", "nunique"),
    canais=("variable", "nunique"),
    pontos=("value", "size"),
    t_max_h=("time_h", "max"),
)
g["pontos_por_corrida"] = (g.pontos / g.corridas).round(0).astype(int)
# pontos por corrida por canal = densidade do eixo tempo
g["pontos_por_corrida_canal"] = (g.pontos / g.corridas / g.canais).round(1)
print(g.sort_values("pontos", ascending=False).to_string())

for tgt in ("uhlendorff2026", "uhlendorff2026_cho"):
    sub = m[m.dataset_id == tgt]
    if sub.empty:
        print(f"\n!!! {tgt} ausente")
        continue
    print(f"\n=== {tgt}: canais e contagem de pontos por canal ===")
    print(sub.variable.value_counts().to_string())
    n_t = sub.groupby("run_id").time_h.nunique()
    print(f"  instantes distintos por corrida: min={n_t.min()} mediana={int(n_t.median())} max={n_t.max()}")
