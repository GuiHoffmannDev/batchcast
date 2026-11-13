"""Verificacao final: confere todo numero citado no RESULTS.md contra os CSVs.

Regra de ouro: cada confronto usa o conjunto NATURAL de pares daqueles dois bracos,
nunca a intersecao global, que exclui contextos e distorce.
"""
import glob, sys
import numpy as np, pandas as pd
sys.path.insert(0, "spike")

ok = []
def check(n, c, d=""):
    ok.append(bool(c)); print(f"  [{'PASSA' if c else 'FALHA'}] {n}  {d}")

d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("results/yeast_*.csv"))], ignore_index=True)
dd = d[np.isfinite(d.mase)]


def paired(a, b, channel=None, context=None, metric="mase"):
    s = dd if channel is None else dd[dd.channel == channel]
    s = s if context is None else s[s.context == context]
    p = s[s.arm.isin([a, b])].pivot_table(
        index=["run_id", "cut", "context", "channel"], columns="arm", values=metric).dropna()
    if a not in p or b not in p or p.empty:
        return np.nan, np.nan, 0
    return ((p[b] - p[a]) / p[b] * 100).median(), (p[a] < p[b]).mean() * 100, len(p)


def cov(a, channel=None):
    s = dd if channel is None else dd[dd.channel == channel]
    s = s[s.arm == a]
    return s.coverage.median(), len(s)


print("=== integridade do dado ===")
from data_yeast import load
runs = load("data/atlas/release")
check("52 corridas de levedura", len(runs) == 52)
check("5 canais densos em toda corrida", all(v["X"].shape[0] == 5 for v in runs.values()))
check("grade regular de 0,25 h", all(abs(np.median(np.diff(v["t"])) - 0.25) < 1e-9 for v in runs.values()))
check("zero corrida com mais de 2% faltante", all(v["nan_frac"] <= 0.02 for v in runs.values()))

print("\n=== unicidade e janelas canonicas ===")
g = d.groupby(["arm", "run_id", "cut", "context", "channel"]).size()
check("sem duplicata de (braco, corrida, origem, contexto, canal)", (g == 1).all(), f"max={g.max()}")
sw = set(map(tuple, pd.read_csv("results/yeast_sweep.csv")[["run_id","cut","context"]].drop_duplicates().values))
ch = set(map(tuple, pd.read_csv("results/yeast_chronos.csv")[["run_id","cut","context"]].drop_duplicates().values))
check("sweep e chronos: as mesmas 780 janelas", sw == ch and len(sw) == 780, f"n={len(sw)}")
for f in ("results/yeast_tfm25.csv", "results/yeast_cov_tfm3.csv"):
    k = set(map(tuple, pd.read_csv(f)[["run_id","cut","context"]].drop_duplicates().values))
    check(f"{f.split('/')[-1]}: subconjunto das canonicas", k <= sw, f"n={len(k)}")

print("\n=== numeros do Resultado 1 e 2 ===")
BIO = "permittivity_pF_cm"
for lbl, a, b, c_, ctx, lo, hi, wlo, whi in [
    ("Chronos multivar vs trivial, biomassa, ctx192 = +33,3% / 76%", "C_chronos2_multivar", "E_last_value", BIO, 192, 32, 35, 74, 78),
    ("idem todos os contextos = +19,9% / 67%", "C_chronos2_multivar", "E_last_value", BIO, None, 19, 21, 65, 69),
    ("Chronos multivar vs univar, biomassa, ctx192 = +10,0%", "C_chronos2_multivar", "C_chronos2_univar", BIO, 192, 9, 11, 0, 101),
    ("TimesFM2.5 vs trivial, 5 canais, ctx192 = +14,6% / 66%", "Bp_tfm25_univar", "E_last_value", None, 192, 13, 16, 64, 68),
    ("TimesFM2.5 empata com Chronos univar, ctx192", "Bp_tfm25_univar", "C_chronos2_univar", None, 192, -3, 3, 45, 52),
    ("TimesFM3 univar vs trivial, 5 canais, todos ctx = +0,0% / 50%", "B_tfm3_univar", "E_last_value", None, None, -1.5, 1.5, 48, 52),
    ("Chronos univar vs TimesFM3 univar, todos ctx = +11,4% / 63%", "C_chronos2_univar", "B_tfm3_univar", None, None, 10, 13, 61, 65),
]:
    v, w, n = paired(a, b, c_, ctx)
    check(lbl, lo <= v <= hi and wlo <= w <= whi, f"{v:+.1f}% / {w:.0f}% n={n}")

print("\n=== numeros das covariaveis ===")
for lbl, a, b, lo, hi in [
    ("so setpoints vs univar(sym) = +3,6%", "A2b_tfm3_setpoints_only", "B_tfm3_univar_sym", 3.0, 4.2),
    ("Chronos covar vs univar = +3,2%", "C_chronos2_covariates", "C_chronos2_univar", 2.6, 3.8),
    ("TimesFM covar vs univar(sym) = +2,7%", "A2_tfm3_covariates", "B_tfm3_univar_sym", 2.1, 3.3),
    ("Chronos covar empata com multivar = +0,0%", "C_chronos2_covariates", "C_chronos2_multivar", -1.0, 1.0),
    ("TimesFM multivar vs univar(sym) = -0,7%", "A_tfm3_multivar_sym", "B_tfm3_univar_sym", -1.5, 0.0),
]:
    v, w, n = paired(a, b, BIO)
    check(lbl, lo <= v <= hi, f"{v:+.1f}% / {w:.0f}% n={n}")

print("\n=== calibracao citada (nominal 0,80) ===")
for a, exp in [("A2b_tfm3_setpoints_only", 0.797), ("A2_tfm3_covariates", 0.812),
               ("C_chronos2_covariates", 0.844), ("C_chronos2_univar", 0.891),
               ("C_chronos2_multivar", 0.938), ("B_tfm3_univar_sym", 0.703)]:
    v, n = cov(a, BIO)
    check(f"{a} = {exp}", abs(v - exp) < 0.005, f"medido {v:.3f} n={n}")

print("\n=== licenca ===")
lic = open("docs/timesfm-3.0-LICENSE.txt").read()
check("clausula de decisao comercial", "not used in commercial decision-making" in lic)
check("clausula de destilacao comercial", "distill other models for commercial use" in lic)

print(f"\n{'=' * 64}")
print(f"{sum(ok)}/{len(ok)} verificacoes passaram")
sys.exit(0 if all(ok) else 1)
