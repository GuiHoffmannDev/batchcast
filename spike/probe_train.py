"""Descobre as formas que Chronos2Model.forward espera e se devolve perda."""
import inspect
import numpy as np, torch
from chronos import Chronos2Pipeline

p = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
m = p.model
print("tipo:", type(m).__name__)
print("params:", f"{sum(x.numel() for x in m.parameters()):,}")
cfg = m.config
for k in ("patch_size", "num_output_patches", "quantiles", "d_model", "num_hidden_layers",
          "max_context_length", "context_length", "prediction_length"):
    if hasattr(cfg, k):
        print(f"  config.{k} = {getattr(cfg, k)}")

print("\nforward:", inspect.signature(m.forward))
src = inspect.getsource(m.forward)
print("\n--- trechos sobre perda ---")
for ln in src.splitlines():
    if any(w in ln for w in ("loss", "future_target", "return ")):
        print("  ", ln.strip()[:150])
