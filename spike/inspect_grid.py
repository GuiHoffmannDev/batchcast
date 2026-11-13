"""Fase 1: regularidade do eixo de tempo. TimesFM assume amostragem regular."""
import sys
import numpy as np
import pandas as pd

rel, dsid = sys.argv[1], sys.argv[2]
runs = pd.read_csv(f"{rel}/runs.csv")
obs = pd.read_csv(f"{rel}/observations.csv.gz")
ids = runs.loc[runs.dataset_id == dsid, "run_id"]
m = obs[obs.run_id.isin(ids)]

dense = (m.variable.value_counts()[lambda s: s > s.max() * 0.5]).index.tolist()
sparse = [v for v in m.variable.unique() if v not in dense]
print(f"{dsid}: {m.run_id.nunique()} corridas")
print(f"  densos  ({len(dense)}): {dense}")
print(f"  esparsos({len(sparse)}): {sparse}")

print("\n=== intervalo de amostragem dos canais densos, por corrida ===")
rows = []
for rid, g in m[m.variable.isin(dense)].groupby("run_id"):
    t = np.sort(g.time_h.unique())
    d = np.diff(t)
    rows.append(dict(run_id=rid, n=len(t), dur_h=round(t[-1] - t[0], 2),
                     dt_med_h=round(float(np.median(d)), 4),
                     dt_min=round(float(d.min()), 4), dt_max=round(float(d.max()), 4),
                     cv_dt=round(float(d.std() / d.mean()), 3)))
r = pd.DataFrame(rows)
print(r.head(8).to_string(index=False))
print(f"\n  resumo: n pontos med={int(r.n.median())}, dur_h med={r.dur_h.median():.1f}")
print(f"  dt mediano global={r.dt_med_h.median():.4f} h ({r.dt_med_h.median()*60:.1f} min)")
print(f"  irregularidade: cv_dt mediano={r.cv_dt.median():.3f}, max={r.cv_dt.max():.3f}")
print(f"  corridas com cv_dt>0.5 (grade MUITO irregular): {(r.cv_dt>0.5).sum()}/{len(r)}")

print("\n=== cobertura: fracao de instantes densos com todos os canais presentes ===")
for v in dense:
    sub = m[m.variable == v]
    print(f"  {v:22s} pontos/corrida med={int(sub.groupby('run_id').size().median())}")

print("\n=== canais esparsos: pontos por corrida ===")
for v in sparse:
    sub = m[m.variable == v]
    s = sub.groupby("run_id").size()
    print(f"  {v:22s} med={int(s.median())} min={s.min()} max={s.max()} corridas={len(s)}")
