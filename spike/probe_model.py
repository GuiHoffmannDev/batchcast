"""Fase 1: confirma que os pesos carregam, conta parametros, mede latencia base."""
import sys, time
import numpy as np
import timesfm

repo = sys.argv[1] if len(sys.argv) > 1 else "google/timesfm-3.0-pytorch"

t0 = time.time()
f = timesfm.TimesFM3Forecaster.from_pretrained(repo, device="cpu")
print(f"carregado em {time.time()-t0:.1f}s")

model = getattr(f, "model", None) or getattr(f, "_model", None)
if model is not None:
    n = sum(p.numel() for p in model.parameters())
    print(f"parametros: {n:,}")
    for attr in ("use_variate_attention", "input_patch_len", "output_patch_len", "quantiles"):
        if hasattr(model, attr):
            print(f"  {attr} = {getattr(model, attr)}")
else:
    print("atributo do modelo nao encontrado; membros:",
          [a for a in dir(f) if not a.startswith("__")])

print("global_context:", getattr(f, "global_context", "n/d"))

# forward de sanidade: seno com ruido, 3 variates
rng = np.random.default_rng(0)
t = np.arange(512)
ctx = np.stack([np.sin(t / 24.0) + 0.05 * rng.standard_normal(512),
                np.cos(t / 37.0) + 0.05 * rng.standard_normal(512),
                0.001 * t + 0.05 * rng.standard_normal(512)])
print("contexto:", ctx.shape)

t0 = time.time()
out = f.predict(context=ctx, horizon=64, return_quantiles=True)
dt = time.time() - t0
print(f"predict ok em {dt*1000:.0f} ms")
print("  forecast:", np.asarray(out.forecast).shape)
q = getattr(out, "quantiles", None)
print("  quantiles:", None if q is None else np.asarray(q).shape)
