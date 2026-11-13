"""Produz a tabela de decisao do spike a partir do CSV longo do run_eval."""
import sys
import numpy as np
import pandas as pd

d = pd.read_csv(sys.argv[1])
d = d[np.isfinite(d.mase) & np.isfinite(d.wql)]

print(f"linhas={len(d)}  corridas={d.run_id.nunique()}  bracos={d.arm.nunique()}")
print(f"contextos={sorted(d.context.unique())}  canais={sorted(d.channel.unique())}\n")

print("=" * 78)
print("TABELA 1 - desempenho global por braco (mediana sobre corrida x origem x contexto x canal)")
print("=" * 78)
t1 = d.groupby("arm").agg(
    MASE_med=("mase", "median"), MASE_media=("mase", "mean"),
    WQL_med=("wql", "median"), cobertura=("coverage", "median"), n=("mase", "size"))
print(t1.sort_values("MASE_med").round(3).to_string())

print("\n" + "=" * 78)
print("TABELA 2 - MASE mediano por braco x canal")
print("=" * 78)
t2 = d.pivot_table(index="arm", columns="channel", values="mase", aggfunc="median")
t2["_media_canais"] = t2.mean(axis=1)
print(t2.sort_values("_media_canais").round(3).to_string())

print("\n" + "=" * 78)
print("TABELA 3 - MASE mediano por braco x tamanho de contexto  (risco de contexto curto)")
print("=" * 78)
t3 = d.pivot_table(index="arm", columns="context", values="mase", aggfunc="median")
print(t3.round(3).to_string())

print("\n" + "=" * 78)
print("TABELA 4 - quantas vezes cada braco e o melhor, por janela (corrida x origem x contexto x canal)")
print("=" * 78)
key = ["run_id", "cut", "context", "channel"]
idx = d.loc[d.groupby(key).mase.idxmin(), "arm"]
w = idx.value_counts()
print((w / w.sum() * 100).round(1).to_string(header=False), "\n(% de janelas em que o braco vence)")

print("\n" + "=" * 78)
print("TABELA 5 - calibracao: cobertura da faixa 0.1-0.9  (nominal 0.80)")
print("=" * 78)
t5 = d.groupby("arm").coverage.agg(["median", "mean", "min", "max"])
t5["desvio_do_nominal"] = (t5["median"] - 0.80).round(3)
print(t5.round(3).to_string())

print("\n" + "=" * 78)
print("TABELA 6 - custo: segundos por canal previsto")
print("=" * 78)
print(d.groupby("arm").seconds.agg(["median", "mean", "sum"]).round(4).to_string())

print("\n" + "=" * 78)
print("VEREDITO")
print("=" * 78)
best_tfm = t1.loc[[a for a in t1.index if a.startswith(("A_", "B_"))], "MASE_med"].min()
best_triv = t1.loc[[a for a in t1.index if a.startswith("E_")], "MASE_med"].min()
name_tfm = t1.loc[[a for a in t1.index if a.startswith(("A_", "B_"))], "MASE_med"].idxmin()
name_triv = t1.loc[[a for a in t1.index if a.startswith("E_")], "MASE_med"].idxmin()
print(f"melhor TimesFM : {name_tfm:20s} MASE {best_tfm:.3f}")
print(f"melhor trivial : {name_triv:20s} MASE {best_triv:.3f}")
delta = (best_triv - best_tfm) / best_triv * 100
print(f"ganho do modelo de fundacao sobre a linha trivial: {delta:+.1f}%")
print("CRITERIO DA FASE 2: se o ganho nao for claramente positivo, o zero-shot nao se sustenta.")

a = t1.loc["A_tfm3_multivar", "MASE_med"] if "A_tfm3_multivar" in t1.index else np.nan
b = t1.loc["B_tfm3_univar", "MASE_med"] if "B_tfm3_univar" in t1.index else np.nan
if np.isfinite(a) and np.isfinite(b):
    print(f"\nvalor da atencao entre variaveis: multivar {a:.3f} vs univar {b:.3f} "
          f"-> {'multivar ajuda' if a < b else 'multivar NAO ajuda'} ({(b-a)/b*100:+.1f}%)")
