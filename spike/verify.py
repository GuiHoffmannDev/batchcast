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
print(f"{sum(ok)}/{len(ok)} verificacoes do Experimento 1 passaram")


# ---------------------------------------------------------------------------
# Experimento 2: transferencia entre organismos, teto, controles e conformal.
# Calibracao e medida pela cobertura MARGINAL (media), nunca pela mediana.
# ---------------------------------------------------------------------------
print("\n=== Experimento 2: numeros do RESULTS_TRANSFER.md ===")
ok2 = []
def check2(n, c, dd=""):
    ok2.append(bool(c)); print(f"  [{'PASSA' if c else 'FALHA'}] {n}  {dd}")

BASE2 = "C_chronos2_multivar"
have = set(dd.arm)

for lbl, a, lo, hi, wlo, whi in [
    ("transferencia CHO N=6  = +0,5% / 52%", "T_chronos2_cho6", 0.0, 1.2, 50, 54),
    ("transferencia CHO N=12 = +1,7% / 53%", "T_chronos2_cho12", 1.2, 2.3, 51, 55),
    ("transferencia CHO N=18 = +2,0% / 53%", "T_chronos2_cho18", 1.5, 2.6, 51, 55),
    ("transferencia CHO N=24 = +0,7% / 51%", "T_chronos2_cho24", 0.2, 1.3, 49, 53),
    ("treino forte = -8,7% / 42%  (esquecimento)", "T_chronos2_cho24_hard", -9.5, -8.0, 40, 44),
    ("controle embaralhado = -2,8% / 44%", "T_chronos2_cho24_shuf", -3.4, -2.3, 42, 46),
    ("teto em distribuicao = +3,6% / 58%", "I_chronos2_yeast_indist", 3.0, 4.2, 56, 60),
]:
    if a not in have:
        check2(lbl, False, "braco ausente"); continue
    v, w, n = paired(a, BASE2)
    check2(lbl, lo <= v <= hi and wlo <= w <= whi, f"{v:+.1f}% / {w:.0f}% n={n}")

if "I_chronos2_yeast_indist" in have:
    p_ = dd[dd.arm.isin(["I_chronos2_yeast_indist", BASE2])].pivot_table(
        index=["run_id", "cut", "context", "channel"], columns="arm", values="wql").dropna()
    v = ((p_[BASE2] - p_["I_chronos2_yeast_indist"]) / p_[BASE2] * 100).median()
    check2("teto: ganho de WQL = +9,5%", 8.8 <= v <= 10.2, f"{v:+.1f}%")

print("\n  -- calibracao: cobertura MARGINAL, nominal 0,80 --")
for a, exp in [(BASE2, 0.792), ("C_chronos2_univar", 0.751), ("Bp_tfm25_univar", 0.848),
               ("C_chronos2_covariates", 0.704), ("A2b_tfm3_setpoints_only", 0.663),
               ("B_tfm3_univar", 0.633), ("E_last_value", 0.557),
               ("I_chronos2_yeast_indist", 0.670), ("K_chronos2_conformal_mult", 0.793)]:
    if a not in have:
        check2(f"marginal {a} = {exp}", False, "ausente"); continue
    v = dd[dd.arm == a].coverage.mean()
    check2(f"marginal {a} = {exp}", abs(v - exp) < 0.004, f"medido {v:.3f}")

if "K_chronos2_conformal_mult" in have:
    b = dd[dd.arm == BASE2].coverage.mean()
    c = dd[dd.arm == "K_chronos2_conformal_mult"].coverage.mean()
    check2("conformal nao muda a calibracao (nada a corrigir)", abs(c - b) < 0.01,
           f"zero-shot {b:.3f} -> conformal {c:.3f}")

print(f"\n{'=' * 64}")
print(f"Experimento 1: {sum(ok)}/{len(ok)} | Experimento 2: {sum(ok2)}/{len(ok2)}")

sys.exit(0 if (all(ok) and all(ok2)) else 1)
