"""Analisa o teste de transferencia entre organismos.

Linha de base correta: C_chronos2_multivar, porque a avaliacao do run_transfer
usa o caminho multivariado (entrada 3D), igual ao braco zero-shot.
"""
import glob, sys
import numpy as np
import pandas as pd

BASE = "C_chronos2_multivar"
KEY = ["run_id", "cut", "context", "channel"]

res = sys.argv[1]
d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{res}/yeast_*.csv"))],
              ignore_index=True)
d = d[np.isfinite(d.mase)]
arms = sorted(a for a in d.arm.unique() if a.startswith("T_"))
indist = sorted(a for a in d.arm.unique() if a.startswith("I_"))
assert arms, "nenhum braco de transferencia encontrado"
assert BASE in set(d.arm), "linha de base zero-shot ausente"


def paired(a, b=BASE, context=None, channel=None, metric="mase"):
    s = d if context is None else d[d.context == context]
    s = s if channel is None else s[s.channel == channel]
    p = s[s.arm.isin([a, b])].pivot_table(index=KEY, columns="arm", values=metric).dropna()
    if a not in p or b not in p or p.empty:
        return np.nan, np.nan, 0
    return ((p[b] - p[a]) / p[b] * 100).median(), (p[a] < p[b]).mean() * 100, len(p)


meta = {}
for f in glob.glob(f"{res}/*_meta.csv"):
    t = pd.read_csv(f)
    if "arm" not in t.columns:      # o meta do braco em distribuicao e por dobra
        continue
    for r in t.to_dict("records"):
        meta[r["arm"]] = r

print("=" * 86)
print("CURVA DE ESCALA: ajustar em CHO-K1 e prever LEVEDURA, organismo nunca treinado")
print("=" * 86)
print("Ganho positivo = melhor que o Chronos-2 zero-shot nas mesmas janelas.\n")
rows = []
for a in arms:
    m = meta.get(a, {})
    v, w, n = paired(a)
    rows.append(dict(braco=a, corridas_CHO=m.get("n_runs"), pontos_treino=m.get("n_points"),
                     passos=m.get("steps"),
                     perda=f"{m.get('loss_inicial', float('nan')):.2f}->{m.get('loss_final', float('nan')):.2f}",
                     ganho_pct=round(v, 1), vence_pct=round(w, 0), n=n))
t = pd.DataFrame(rows).sort_values("corridas_CHO", na_position="last")
print(t.to_string(index=False))

print("\n" + "=" * 86)
print("GANHO POR TAMANHO DE CONTEXTO  (o dinheiro esta no contexto curto)")
print("=" * 86)
cols = sorted(d.context.unique())
out = []
for a in arms:
    r = {"braco": a}
    for c in cols:
        v, w, n = paired(a, context=c)
        r[f"ctx{c}"] = None if n == 0 else round(v, 1)
    out.append(r)
print(pd.DataFrame(out).to_string(index=False))

print("\n" + "=" * 86)
print("GANHO POR CANAL, melhor braco")
print("=" * 86)
best = max(arms, key=lambda a: (paired(a)[0] if np.isfinite(paired(a)[0]) else -1e9))
print(f"melhor braco: {best}")
for ch in sorted(d.channel.unique()):
    v, w, n = paired(best, channel=ch)
    print(f"  {ch:22s} {v:+6.1f}%  vence {w:3.0f}%  n={n}")

print("\n" + "=" * 86)
print("CONTROLE NEGATIVO: tempo embaralhado no treino")
print("=" * 86)
shuf = [a for a in arms if a.endswith("_shuf")]
real = [a for a in arms if not a.endswith("_shuf")]
if not shuf:
    print("  (ainda nao rodou)")
else:
    for a in shuf:
        base_arm = a.replace("_shuf", "")
        v, w, n = paired(a)
        print(f"  {a:26s} vs zero-shot: {v:+6.1f}%  vence {w:3.0f}%")
        if base_arm in real:
            v2, w2, _ = paired(base_arm)
            print(f"  {base_arm:26s} vs zero-shot: {v2:+6.1f}%  vence {w2:3.0f}%")
            print(f"\n  Ganho atribuivel a DINAMICA de bioprocesso: {v2 - v:+.1f} pontos percentuais")
            if v > 0 and v2 - v < 2:
                print("  LEITURA: o controle ganha quase igual. O ganho e adaptacao a escala e taxa")
                print("           de amostragem, NAO conhecimento de bioprocesso. Premissa fraca.")
            elif v2 - v >= 5:
                print("  LEITURA: o dado real ganha bem do embaralhado. A dinamica de bioprocesso")
                print("           transfere entre organismos. Premissa SUSTENTADA.")

print("\n" + "=" * 86)
print("TETO EM DISTRIBUICAO: ajustado na propria levedura, validado por campanha")
print("=" * 86)
if not indist:
    print("  (ainda nao rodou)")
else:
    for a in indist:
        v, w, n = paired(a)
        print(f"  {a:26s} vs zero-shot: {v:+6.1f}%  vence {w:3.0f}%  n={n}")
    bt = max(indist, key=lambda a: paired(a)[0])
    gb = paired(bt)[0]
    real_ = [a for a in arms if not a.endswith("_shuf")]
    if real_:
        bestT = max(real_, key=lambda a: paired(a)[0])
        gt = paired(bestT)[0]
        print(f"\n  teto em distribuicao   : {gb:+.1f}%  ({bt})")
        print(f"  melhor transferencia   : {gt:+.1f}%  ({bestT})")
        if gb > 0:
            frac = gt / gb * 100
            print(f"  a transferencia captura {frac:.0f}% do teto")
            if frac >= 70:
                print("  LEITURA: dado de outro organismo entrega quase o mesmo que dado do proprio")
                print("           processo. Corpus de terceiros serve. Isso e PRODUTO.")
            elif frac <= 30:
                print("  LEITURA: so dado do proprio processo entrega o ganho. Cada cliente precisa")
                print("           dos seus dados. Isso tende a CONSULTORIA, nao a produto.")
            else:
                print("  LEITURA: zona intermediaria. Corpus de terceiros ajuda mas nao substitui")
                print("           dado do cliente. Modelo base mais ajuste por cliente.")

print("\n" + "=" * 86)
print("CALIBRACAO (nominal 0,80)")
print("=" * 86)
for a in [BASE] + arms + indist:
    s = d[d.arm == a]
    print(f"  {a:26s} {s.coverage.median():.3f}  desvio {s.coverage.median()-0.80:+.3f}")

print("\n" + "=" * 86)
print("VEREDITO DO CRITERIO")
print("=" * 86)
gains = {a: paired(a)[0] for a in real}
if gains:
    bst = max(gains, key=lambda k: gains[k])
    g = gains[bst]
    ns = [meta.get(a, {}).get("n_runs") for a in real]
    ordered = [gains[a] for a in sorted(real, key=lambda a: meta.get(a, {}).get("n_runs") or 0)]
    slope = "crescente" if len(ordered) > 1 and ordered[-1] > ordered[0] + 1 else "plana ou decrescente"
    print(f"melhor ganho: {g:+.1f}% em {bst}")
    print(f"curva de escala: {slope}  ({[round(x,1) for x in ordered]})")
    if g >= 10:
        print("PASSA: acima de 10%. Seguir para aquisicao de dado proprietario.")
    elif g >= 5:
        print("PARCIAL: entre 5% e 10%. Decide pela inclinacao da curva.")
    else:
        if slope == "crescente":
            print("INCONCLUSIVO: abaixo de 5% mas a curva sobe. Falta dado, nao sinal.")
        else:
            print("FALHA: abaixo de 5% e curva plana. Tratar como problema de dado antes")
            print("       de qualquer outra linha de codigo de modelagem.")
