# Batchcast

Batchcast forecasts where a fermentation batch is heading. It reads the inline sensors of a
running batch and predicts the next 16 hours of every channel, with an uncertainty range around
each forecast.

This repository holds two things:

- **An evaluation** of open time-series foundation models on real fermentation data, with every
  reported number checked against the raw result files by a script.
- **A presentation site** (Next.js) that shows the results for the commercially licensed models.

The work is an early spike on public data. It has no customer data, no model of its own and no
production system. The negative results are reported next to the positive ones.

## What was measured

| Item | Value |
|---|---|
| Data | 52 real brewing-yeast propagation runs, `uhlendorff2026` from the Bioprocess Atlas |
| Channels | temperature, pH, dissolved oxygen, dissolved CO2, permittivity (tracks biomass) |
| Task | forecast the next 16 h (64 points on a 15-minute grid) with nine quantiles |
| History given to the model | 8 h to 48 h of a batch that lasts about 72 h |
| Evaluation | 780 forecast windows, every method on the same windows, compared pairwise |
| Hardware | one laptop, CPU only |

## What held up

**Open foundation models beat trivial forecasts, and one of them does it early.** Chronos-2,
used zero-shot, against the best trivial baseline (median paired MASE gain, all five channels):

| History | 8 h | 16 h | 24 h | 32 h | 48 h |
|---|---|---|---|---|---|
| Gain | +28.6% | +22.7% | +24.2% | +27.6% | +24.3% |

On the biomass channel, Chronos-2 forecasting all channels together beats repeating the last
value by 13% to 33% and wins 57% to 76% of the windows, depending on history length. TimesFM 2.5
reaches +14.6% over the same baseline with 48 h of history.

**Its uncertainty ranges are already calibrated.** The 10% to 90% range of zero-shot Chronos-2
(all channels together) contains 79.2% of the observations against a nominal 80%. Conformal
prediction, run as an independent check, found nothing to correct.

## What did not hold up

- **A forecaster is a poor deviation alarm.** A model conditioned on an anomalous history treats
  the anomaly as the new normal. On a paired heat-stress test, a two-component PCA detected all
  four deviating runs with a first alarm at 4.75 h, while the Chronos-2 quantile range detected
  none. Four positives is a small sample; the result supports the direction and the mechanism,
  not the exact rates.
- **Fine-tuning on bioprocess data did not help at this scale.** Fine-tuning Chronos-2 on up to
  24 CHO cell-culture runs (about 100,000 points) and testing on yeast gave at most +2.0%, with
  a 53% win rate. Training harder made it 8.7% worse. Fine-tuning on yeast itself sharpened the
  forecast but pushed coverage from 0.792 down to 0.670.
- **Model architecture choices are small.** No variation tested (joint multivariate input,
  setpoint covariates) moved accuracy by more than about 10%.
- **Two of my own first-draft claims were wrong.** Both came from aggregating before comparing:
  a covariate gain reported as 12% is 3.6% when paired, and a calibration claim based on the
  median coverage reverses when measured by the mean. The verification step caught both, and the
  reports document the corrections.

The full reports, with design, tables, limitations and reproduction steps, are written in
Portuguese:

- [RESULTS.md](RESULTS.md): model comparison, history length, covariates, deviation detection.
- [RESULTS_TRANSFER.md](RESULTS_TRANSFER.md): transfer from CHO to yeast, in-distribution
  ceiling, conformal prediction, and the calibration correction.

## Repository layout

| Path | Content |
|---|---|
| `spike/` | Evaluation code: data loaders, baselines, model runs, analysis, `verify.py` |
| `results/` | Per-window result CSVs and run logs that the reports are built from |
| `RESULTS.md`, `RESULTS_TRANSFER.md` | The two evaluation reports |
| `site/` | The Batchcast site (Next.js); its copy and numbers live in `site/content.ts` |
| `docs/` | The TimesFM 3.0 licence text and a draft announcement post |

## Verify the numbers

`spike/verify.py` recomputes the figures cited in the two reports from `results/*.csv` and exits
with status 1 if any of them differs. It currently passes 46 of 46 checks.

```bash
uv venv --python 3.12 .venv
VIRTUAL_ENV=.venv uv pip install "timesfm[torch,mlx]==3.0.2" chronos-forecasting \
    pandas numpy scikit-learn scipy pyarrow
git clone --depth 1 https://github.com/anupama29k/Bioprocess-Atlas.git data/atlas
.venv/bin/python -I spike/verify.py
```

To rerun the experiments themselves, follow the "Como reproduzir" section of each report. The
scripts take the data path as an argument and run with `python -I`, because downloaded data is
treated as untrusted input.

## Run the site

```bash
cd site
npm install
npm run dev
```

The contact form stores messages in Supabase. Copy `site/.env.example` to `site/.env.local` and
fill in the two values; the migration is in `site/supabase/migrations/`. `npm test` runs the
form validation tests.

## Data and licences

- **Code:** the code in `spike/` and `site/` is licensed under Apache-2.0, see
  [LICENSE](LICENSE). That licence does not extend to the third-party items below.
- **Data:** `uhlendorff2026` (yeast, DOI `10.5281/zenodo.19690248`) and `uhlendorff2026_cho`
  (CHO, DOI `10.5281/zenodo.20829178`), both CC BY 4.0, obtained through the Bioprocess Atlas.
  The data is not redistributed here.
- **Models behind the headline results:** Chronos-2 and TimesFM 2.5, both Apache-2.0.
- **TimesFM 3.0** was also measured. Its weights are under the TimesFM Non-Commercial License
  v1.0 (copy in `docs/timesfm-3.0-LICENSE.txt`). Its numbers appear in the reports as a research
  comparison only and stay subject to that licence; the site and the results above cite the
  Apache-2.0 models.

## Limitations

- One public dataset and one kind of process. Other organisms, scales and industrial plants are
  untested.
- One evaluation pass per window, without repeated seeds or confidence intervals.
- MASE values rank the methods; they are not a relative error an operator can read directly.
- The transfer result holds for about 100,000 training points and one organism pair. It does not
  say what a much larger or closer corpus would do.
