"""Teto em distribuicao: ajustar na PROPRIA levedura, com validacao por campanha.

Da o limite superior do ganho possivel com dado perfeitamente casado. Comparado
ao braco de transferencia de CHO, responde a pergunta de negocio:

  preciso de dado do mesmo processo, ou qualquer bioprocesso serve?

Se o teto em distribuicao for muito acima da transferencia de CHO, cada cliente
precisa dos proprios dados e o negocio tende a consultoria. Se forem parecidos,
um corpus de bateladas de terceiros serve e o modelo e um produto.

Divisao por CAMPANHA, nunca por corrida: os 4 reatores de uma campanha sao
replicas e dividi-los seria vazamento.
"""
import argparse, sys, time
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, "spike")
from chronos import Chronos2Pipeline
from data_bioprocess import SHARED, load
from metrics import coverage, mase, wql
from run_eval import HORIZON, N_ORIGINS, windows
from run_transfer import CONTEXT_TRAIN, STRIDE_TRAIN, finetune, train_windows


def campaign(run_id):
    return run_id.split(":")[1].split("_")[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("release")
    ap.add_argument("--out", required=True)
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--eval-contexts", default="32,64,96,128,192")
    a = ap.parse_args()

    y = load(a.release, "uhlendorff2026", SHARED)
    assert len(y) == 52
    camps = sorted({campaign(k) for k in y})
    rng = np.random.default_rng(a.seed)
    shuffled = list(np.array(camps)[rng.permutation(len(camps))])
    folds = [list(shuffled[i::a.folds]) for i in range(a.folds)]
    print(f"{len(y)} corridas, {len(camps)} campanhas, {a.folds} dobras por campanha")
    for i, f in enumerate(folds):
        n = sum(1 for k in y if campaign(k) in f)
        print(f"  dobra {i}: {len(f)} campanhas, {n} corridas de teste -> {f}")
    ctxs = [int(x) for x in a.eval_contexts.split(",")]

    rows, meta = [], []
    for i, test_camps in enumerate(folds):
        test = {k: v for k, v in y.items() if campaign(k) in test_camps}
        train = {k: v for k, v in y.items() if campaign(k) not in test_camps}
        assert not (set(test) & set(train)), "VAZAMENTO entre dobras"
        assert not ({campaign(k) for k in test} & {campaign(k) for k in train}), \
            "VAZAMENTO de campanha entre dobras"
        wins = train_windows(train, CONTEXT_TRAIN, HORIZON, STRIDE_TRAIN)
        print(f"\n=== dobra {i}: treino {len(train)} corridas / {len(wins)} janelas, "
              f"teste {len(test)} corridas ===", flush=True)
        pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
        info = finetune(pipe, wins, a.epochs, a.lr, a.batch, a.seed)
        print(f"  perda {info['loss_inicial']:.4f} -> {info['loss_final']:.4f} "
              f"em {info['steps']} passos, {info['segundos']:.0f}s", flush=True)
        n0 = len(rows)
        with torch.no_grad():
            for k in sorted(test):
                X = test[k]["X"]; T = X.shape[1]
                for C in ctxs:
                    for cut in windows(T, C, HORIZON, N_ORIGINS):
                        ctx, tgt = X[:, cut - C:cut], X[:, cut:cut + HORIZON]
                        if not (np.isfinite(ctx).all() and np.isfinite(tgt).all()):
                            continue
                        q, mu = pipe.predict_quantiles(ctx[None, ...].astype(np.float32),
                                                       prediction_length=HORIZON)
                        pt, qq = mu[0].numpy(), q[0].numpy()
                        mm, ww, cc = mase(tgt, pt, ctx), wql(tgt, qq, ctx), coverage(tgt, qq)
                        for v, chn in enumerate(test[k]["dense"]):
                            rows.append(dict(arm="I_chronos2_yeast_indist", run_id=k, cut=cut,
                                             context=C, channel=chn, mase=mm[v], wql=ww[v],
                                             coverage=cc[v], seconds=np.nan, fold=i))
        print(f"  avaliado: {len(rows)-n0} linhas", flush=True)
        meta.append(dict(fold=i, n_train=len(train), n_test=len(test),
                         n_windows=len(wins), **info))
        del pipe

    d = pd.DataFrame(rows)
    d.to_csv(a.out, index=False)
    pd.DataFrame(meta).to_csv(a.out.replace(".csv", "_meta.csv"), index=False)
    print(f"\nescrito {a.out}: {len(d)} linhas, "
          f"{d.run_id.nunique()} corridas cobertas (esperado 52)")
    print(d.groupby("arm")[["mase", "wql", "coverage"]].median().round(4).to_string())


if __name__ == "__main__":
    main()
