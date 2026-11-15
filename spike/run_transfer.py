"""Teste de transferencia entre organismos, com curva de escala de dado.

Pergunta: ajustar o Chronos-2 em bateladas de CHO-K1 melhora a previsao em
LEVEDURA, um organismo que o modelo ajustado nunca viu?

Essa e a premissa da empresa. Se ajustar em bioprocesso transfere para processo
novo, o modelo de fundacao vertical faz sentido. Se nao transfere, o projeto
precisa de ordens de magnitude mais dado do que qualquer parceiro unico da.

Disciplina: LEVEDURA NUNCA entra no treino. Avaliacao nas mesmas 780 janelas
canonicas usadas por todos os bracos anteriores. Comparacao emparelhada contra o
Chronos-2 zero-shot ja medido.
"""
import argparse, json, sys, time
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, "spike")
from chronos import Chronos2Pipeline
from data_bioprocess import SHARED, load
from metrics import coverage, mase, wql
from run_eval import HORIZON, N_ORIGINS, windows

CONTEXT_TRAIN = 192
STRIDE_TRAIN = 32
EVAL_CONTEXTS = [32, 64, 96, 128, 192]
PATCH = 16


def train_windows(runs, context, horizon, stride):
    """Janelas de treino: (canais, contexto) e (canais, horizonte)."""
    out = []
    for k in sorted(runs):
        X = runs[k]["X"]
        T = X.shape[1]
        cut = context
        while cut + horizon <= T:
            c, y = X[:, cut - context:cut], X[:, cut:cut + horizon]
            if np.isfinite(c).all() and np.isfinite(y).all():
                out.append((c.astype(np.float32), y.astype(np.float32)))
            cut += stride
    return out


def shuffle_time(wins, rng):
    """Controle negativo: embaralha o tempo dentro de cada canal.

    Preserva a distribuicao marginal de cada canal e destroi toda a dinamica
    temporal. Se ajustar nisso ajudar tanto quanto ajustar no dado real, o ganho
    nao vem de dinamica de bioprocesso, vem de adaptacao a escala e a taxa de
    amostragem. Esse e o controle que torna o resultado interpretavel.
    """
    out = []
    for c, y in wins:
        full = np.concatenate([c, y], axis=1)
        perm = np.stack([rng.permutation(full.shape[1]) for _ in range(full.shape[0])])
        sh = np.take_along_axis(full, perm, axis=1)
        out.append((sh[:, :c.shape[1]].copy(), sh[:, c.shape[1]:].copy()))
    return out


def batches(wins, bs, rng):
    idx = rng.permutation(len(wins))
    for i in range(0, len(idx) - bs + 1, bs):
        sel = [wins[j] for j in idx[i:i + bs]]
        ctx = np.concatenate([c for c, _ in sel], 0)          # (bs*V, C)
        tgt = np.concatenate([y for _, y in sel], 0)          # (bs*V, H)
        V = sel[0][0].shape[0]
        gid = np.repeat(np.arange(len(sel)), V)
        yield (torch.from_numpy(ctx), torch.from_numpy(tgt), torch.from_numpy(gid))


def finetune(pipe, wins, epochs, lr, bs, seed, log_every=25, max_steps=0):
    m = pipe.model
    m.train()
    opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=lr,
                            weight_decay=0.01)
    rng = np.random.default_rng(seed)
    nop = HORIZON // PATCH
    step, losses = 0, []
    t0 = time.time()
    done = False
    for ep in range(epochs if not max_steps else 10_000):
        if done:
            break
        for ctx, tgt, gid in batches(wins, bs, rng):
            out = m(context=ctx, group_ids=gid, future_target=tgt, num_output_patches=nop)
            loss = out.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_([p for p in m.parameters() if p.requires_grad], 1.0)
            opt.step(); opt.zero_grad(set_to_none=True)
            losses.append(loss.detach().item()); step += 1
            if step % log_every == 0:
                print(f"    passo {step:4d} ep{ep} perda {np.mean(losses[-log_every:]):.4f} "
                      f"({time.time()-t0:.0f}s)", flush=True)
            if max_steps and step >= max_steps:
                done = True
                break
    m.eval()
    return dict(steps=step, loss_inicial=float(np.mean(losses[:10])),
                loss_final=float(np.mean(losses[-10:])), segundos=time.time() - t0)


def evaluate(pipe, yeast, arm, contexts):
    rows = []
    with torch.no_grad():
        for k in sorted(yeast):
            run = yeast[k]; X = run["X"]; T = X.shape[1]
            for C in contexts:
                for cut in windows(T, C, HORIZON, N_ORIGINS):
                    ctx, y = X[:, cut - C:cut], X[:, cut:cut + HORIZON]
                    if not (np.isfinite(ctx).all() and np.isfinite(y).all()):
                        continue
                    q, mu = pipe.predict_quantiles(ctx[None, ...].astype(np.float32),
                                                   prediction_length=HORIZON)
                    pt, qq = mu[0].numpy(), q[0].numpy()
                    mm, ww, cc = mase(y, pt, ctx), wql(y, qq, ctx), coverage(y, qq)
                    for v, chn in enumerate(run["dense"]):
                        rows.append(dict(arm=arm, run_id=k, cut=cut, context=C, channel=chn,
                                         mase=mm[v], wql=ww[v], coverage=cc[v], seconds=np.nan))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("release")
    ap.add_argument("--out", required=True)
    ap.add_argument("--donor-sizes", default="6,12,18,24")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--eval-contexts", default=",".join(map(str, EVAL_CONTEXTS)))
    ap.add_argument("--max-steps", type=int, default=0,
                    help="teto de passos; iguala o treino entre tamanhos de doador")
    ap.add_argument("--suffix", default="",
                    help="sufixo no nome do braco, para distinguir protocolos")
    ap.add_argument("--control", action="store_true",
                    help="embaralha o tempo no treino (controle negativo)")
    a = ap.parse_args()

    yeast = load(a.release, "uhlendorff2026", SHARED)
    cho = load(a.release, "uhlendorff2026_cho", SHARED)
    assert len(yeast) == 52, f"levedura esperada 52, veio {len(yeast)}"
    assert len(cho) == 24, f"CHO esperado 24, veio {len(cho)}"
    assert not (set(yeast) & set(cho)), "VAZAMENTO: corrida em ambos os conjuntos"
    print(f"alvo: {len(yeast)} corridas de levedura (NUNCA treinadas)")
    print(f"doador: {len(cho)} corridas de CHO-K1, canais {SHARED}", flush=True)

    ctxs = [int(x) for x in a.eval_contexts.split(",")]
    rows, meta = [], []
    rng = np.random.default_rng(a.seed)
    order = list(np.array(sorted(cho))[rng.permutation(len(cho))])

    for n in [int(x) for x in a.donor_sizes.split(",")]:
        sub = {k: cho[k] for k in order[:n]}
        wins = train_windows(sub, CONTEXT_TRAIN, HORIZON, STRIDE_TRAIN)
        if a.control:
            wins = shuffle_time(wins, np.random.default_rng(a.seed + 99))
        pts = sum(v["X"].size for v in sub.values())
        print(f"\n=== N={n} corridas de CHO | {len(wins)} janelas de treino | "
              f"{pts:,} pontos ===", flush=True)
        if len(wins) < a.batch:
            print("  janelas insuficientes, pulando"); continue
        pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
        info = finetune(pipe, wins, a.epochs, a.lr, a.batch, a.seed, max_steps=a.max_steps)
        print(f"  perda {info['loss_inicial']:.4f} -> {info['loss_final']:.4f} "
              f"em {info['steps']} passos, {info['segundos']:.0f}s", flush=True)
        arm = f"T_chronos2_cho{n}" + ("_shuf" if a.control else "") + a.suffix
        r = evaluate(pipe, yeast, arm, ctxs)
        rows += r
        meta.append(dict(arm=arm, n_runs=n, n_windows=len(wins), n_points=pts, **info))
        print(f"  avaliado em levedura: {len(r)} linhas", flush=True)
        del pipe

    d = pd.DataFrame(rows)
    d.to_csv(a.out, index=False)
    pd.DataFrame(meta).to_csv(a.out.replace(".csv", "_meta.csv"), index=False)
    print(f"\nescrito {a.out}: {len(d)} linhas")
    print(d.groupby("arm")[["mase", "wql", "coverage"]].median().round(4).to_string())


if __name__ == "__main__":
    main()
