# LinkedIn post: Batchcast / bioprocess forecasting spike

**I tested whether time-series foundation models can forecast real fermentations. The result was more interesting than I expected.**

I spent the last few days on a spike to decide whether a bioprocess forecasting product is worth building. I didn't want to decide on gut feeling, so I measured.

**The test**
- 52 real yeast fermentation runs (public dataset, CC BY 4.0)
- 780 forecast windows, 16 h horizon, 5 channels (temperature, pH, dissolved O₂, dissolved CO₂, permittivity)
- 4 foundation models against trivial baselines, all running on CPU on a Mac
- A verification script that checks every number in the report against the result CSVs

**What I found**

1. **There is signal.** With 48 h of history, the foundation models beat the trivial baselines by 14% to 29%.

2. **Picking the model is not the edge. Getting there early is.** At 48 h of history, all four models tie. With short history, only Chronos-2 works: it beats the trivial baseline by about 28% with just 8 h of a 72 h batch. TimesFM 3.0 loses in that range. For early warning, that is the difference that matters.

3. **Fancy architecture is not a shortcut.** No variation (multivariate, covariates) added more than ~10%. But setpoint covariates fixed quantile calibration, which matters more than their 3% accuracy gain, because it lets you act on the uncertainty.

4. **Deviation detection with a forecaster is a trap.** A forecaster conditioned on anomalous history treats the anomaly as the new normal. The better the model, the less it alarms. A plain 2-component PCA won: 100% detection versus 0% for Chronos-2 and 25% for TimesFM 3.0.

5. **The license decides.** The TimesFM 3.0 license forbids using the results for business decisions. TimesFM 2.5 and Chronos-2 are Apache-2.0 and perform equally well or better.

**A mistake I made myself:** in a first pass I reported a 12% gain from covariates. It came from comparing medians over different windows. Paired, it is 3.6%. The verification assertions caught it, and the correction is documented in the report.

**Conclusion:** go, but swap the product (from deviation alarms to trajectory and end-point forecasting) and the bet (from architecture to data and calibration). None of these models saw bioprocess data in pre-training, and only proprietary batch data closes that gap.

I also published a site, Batchcast, with the results for the commercially licensed models, including a real Chronos-2 forecast in the chart.

If you work on bioprocess, time-series forecasting, or fermentation data, I'd love to compare notes.

@Y Combinator

#TimeSeries #Bioprocess #MachineLearning #FoundationModels #Biotech #Chronos #TimesFM #YCombinator

---

## Posting notes

- Type `@Y Combinator` in the LinkedIn composer and pick the company page from the dropdown to create a real tag. Pasted text stays plain.
- No link in the body: the public site URL was not found. Put it in the first comment, since LinkedIn tends to reduce reach for posts with links in the body.
- "Batchcast" is the site name taken from the commit message. Change it if the product name differs.
