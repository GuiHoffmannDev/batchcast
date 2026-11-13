"""Junta todos os CSVs de resultado e compara canal a canal, like-for-like.

Comparar medianas entre bracos que cobrem conjuntos diferentes de canais e erro.
Aqui todo confronto e restrito ao mesmo canal e as mesmas janelas.
"""
import glob, sys
import numpy as np, pandas as pd

MODEL_INFO = {
    "A_tfm3_multivar":        ("TimesFM 3.0", 330, "nao-comercial", "multivariado"),
    "A2_tfm3_covariates":     ("TimesFM 3.0", 330, "nao-comercial", "alvo+covariaveis"),
    "A2b_tfm3_setpoints_only":("TimesFM 3.0", 330, "nao-comercial", "alvo+setpoints"),
    "B_tfm3_univar":          ("TimesFM 3.0", 330, "nao-comercial", "univariado"),
    "Bp_tfm25_univar":        ("TimesFM 2.5", 200, "Apache-2.0", "univariado"),
    "C_chronos2_multivar":    ("Chronos-2", 119, "Apache-2.0", "multivariado"),
    "C_chronos2_univar":      ("Chronos-2", 119, "Apache-2.0", "univariado"),
    "C_chronos2_covariates":  ("Chronos-2", 119, "Apache-2.0", "alvo+setpoints"),
}

frames = [pd.read_csv(f) for f in sorted(glob.glob(sys.argv[1] + "/yeast_*.csv"))]
d = pd.concat(frames, ignore_index=True)
d = d[np.isfinite(d.mase) & np.isfinite(d.wql)]
print(f"{len(d)} linhas de {len(frames)} arquivos; bracos: {d.arm.nunique()}")
print(f"janelas unicas: {d.groupby(['run_id','cut','context']).ngroups}\n")

TGT = "permittivity_pF_cm"
print("=" * 92)
print(f"TABELA PRINCIPAL - canal unico '{TGT}' (proxy de biomassa), todos os bracos comparaveis")
print("=" * 92)
t = d[d.channel == TGT]
g = t.groupby("arm").agg(MASE=("mase", "median"), WQL=("wql", "median"),
                         cob=("coverage", "median"), s_canal=("seconds", "median"),
                         n=("mase", "size"))
g["modelo"] = [MODEL_INFO.get(a, ("?", 0, "?", "?"))[0] for a in g.index]
g["M_par"] = [MODEL_INFO.get(a, ("?", 0, "?", "?"))[1] for a in g.index]
g["licenca"] = [MODEL_INFO.get(a, ("?", 0, "?", "?"))[2] for a in g.index]
g["modo"] = [MODEL_INFO.get(a, ("?", 0, "?", "?"))[3] for a in g.index]
cols = ["modelo", "M_par", "licenca", "modo", "MASE", "WQL", "cob", "s_canal", "n"]
print(g[cols].sort_values("MASE").round(3).to_string())

print("\n" + "=" * 92)
print(f"'{TGT}' - MASE mediano por tamanho de contexto (risco de contexto curto)")
print("=" * 92)
p = t.pivot_table(index="arm", columns="context", values="mase", aggfunc="median")
p["plano_32_a_192"] = (p[32] / p[192]).round(2)
print(p.round(3).sort_values(192).to_string())
print("\nplano_32_a_192 perto de 1 = pouco dependente de historico longo.")

print("\n" + "=" * 92)
print("TODOS OS CANAIS - bracos que cobrem os 5 canais densos")
print("=" * 92)
full = d[d.arm.isin(d.groupby("arm").channel.nunique()[lambda s: s == 5].index)]
gf = full.groupby("arm").agg(MASE=("mase", "median"), WQL=("wql", "median"),
                             cob=("coverage", "median"), s_canal=("seconds", "median"))
gf["modelo"] = [MODEL_INFO.get(a, ("linha trivial", 0, "-", "-"))[0] for a in gf.index]
gf["licenca"] = [MODEL_INFO.get(a, ("linha trivial", 0, "-", "-"))[2] for a in gf.index]
print(gf.sort_values("MASE").round(3).to_string())

print("\n" + "=" * 92)
print("TAXA DE VITORIA por janela, entre os bracos de 5 canais (scale-free, confirma o MASE)")
print("=" * 92)
key = ["run_id", "cut", "context", "channel"]
wins = full.loc[full.groupby(key).mase.idxmin(), "arm"].value_counts()
print((wins / wins.sum() * 100).round(1).to_string(header=False))

print("\n" + "=" * 92)
print("CALIBRACAO - cobertura da faixa 0.1-0.9, nominal 0.80")
print("=" * 92)
cal = d.groupby("arm").coverage.median().sort_values()
for a, v in cal.items():
    flag = "OK" if abs(v - 0.80) <= 0.06 else ("largo demais" if v > 0.86 else "estreito demais")
    print(f"  {a:26s} {v:.3f}  {flag}")
