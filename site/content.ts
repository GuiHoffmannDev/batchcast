// Single source for the site's name, copy and numbers.
// Every figure below is copied from ../RESULTS.md, which ../spike/verify.py checks against results/*.csv.
// Only Apache-2.0 models (Chronos-2, TimesFM 2.5) are cited: the TimesFM 3.0 licence forbids commercial use of its results.

export const site = {
  name: "Batchcast",
  title: "Batchcast: fermentation forecasts from eight hours of sensor data",
  description:
    "Batchcast forecasts the next 16 hours of every sensor channel in a fermentation batch, with an uncertainty range around each forecast.",
};

/** Chronos-2, median paired MASE gain over the best trivial baseline, all 5 channels. */
export const gainByContext = [
  { hours: 8, gain: 28.6 },
  { hours: 16, gain: 22.7 },
  { hours: 24, gain: 24.2 },
  { hours: 32, gain: 27.6 },
  { hours: 48, gain: 24.3 },
];

/** Chronos-2 multivariate against repeating the last value, biomass channel (permittivity). */
export const biomassByContext = [
  { hours: 8, gain: 14.7, wins: 67 },
  { hours: 16, gain: 13.1, wins: 57 },
  { hours: 24, gain: 17.7, wins: 66 },
  { hours: 32, gain: 22.4, wins: 67 },
  { hours: 48, gain: 33.3, wins: 76 },
];

/** TimesFM 2.5 at 48 h of history, paired on the same 780 windows. */
export const secondModel = [
  { against: "Repeating the last value", gain: 14.6, wins: 66 },
  { against: "Linear extrapolation", gain: 28.6, wins: 67 },
];

export const steps = [
  {
    title: "Read the batch so far",
    body: "Batchcast takes the inline sensor history of a running batch: temperature, pH, dissolved oxygen, dissolved CO2 and permittivity, which tracks biomass.",
  },
  {
    title: "Forecast the next 16 hours",
    body: "It predicts every channel 16 hours ahead on a 15-minute grid. Eight hours of history from a 72-hour batch is enough to start.",
  },
  {
    title: "Show how sure the forecast is",
    body: "Each forecast comes with nine quantiles, from 10% to 90%, so an operator sees a range and not only a single line.",
  },
  {
    title: "Check it against what happened",
    body: "This is a real test window. The dotted line is what the batch went on to measure over the next 16 hours.",
  },
];

export const datasetFacts = [
  { label: "Fermentation runs", value: "52" },
  { label: "Sensor channels", value: "5" },
  { label: "Forecast windows", value: "780" },
  { label: "Forecast horizon", value: "16 h" },
  { label: "Sampling grid", value: "15 min" },
  { label: "Median run length", value: "72.8 h" },
];

export const limitations = [
  "One public dataset and one kind of process: brewing-yeast propagation. Other organisms and scales are untested.",
  "One evaluation pass per window, without repeated seeds or confidence intervals.",
  "Uncertainty ranges are too wide today. The 80% range of Chronos-2 covers 89% to 94% of observations.",
  "These are zero-shot results from open models. Batchcast has not yet trained a model of its own.",
  "Batchcast forecasts where a batch is going. It is not a deviation alarm.",
];

export const roadmap = [
  {
    title: "Pretrain on batch data",
    body: "The public benchmarks these models are tuned on contain no biology. A corpus of real fermentation batches is the gap that open models cannot close on their own.",
  },
  {
    title: "Tighten the uncertainty ranges",
    body: "Telling the model the planned temperature and pH brings Chronos-2 coverage from 0.89 to 0.84, against a target of 0.80. Recalibrating on process data should close the rest.",
  },
  {
    title: "Work with production plants",
    body: "The next step is running on industrial fermentations with a partner, starting with processes close to yeast, such as ethanol from sugarcane.",
  },
];

export const credit = {
  dataset: "uhlendorff2026, from the Bioprocess Atlas",
  doi: "10.5281/zenodo.19690248",
  licence: "CC BY 4.0",
  models: "Chronos-2 and TimesFM 2.5, both released under Apache-2.0",
};

export const intro =
  "Batchcast is a forecasting project for industrial fermentation. It reads the sensors of a running batch and predicts where every channel is heading, early enough to act.";

/** The four figures shown large in the results section. */
export const headlineStats = [
  { value: "+28.6%", label: "All five channels", note: "accuracy gain with 8 h of history" },
  { value: "+33.3%", label: "Biomass channel", note: "accuracy gain with 48 h of history" },
  { value: "76%", label: "Biomass channel", note: "of forecast windows won at 48 h" },
  { value: "+14.6%", label: "Second open model", note: "TimesFM 2.5 gain at 48 h" },
];

export const audiences = [
  {
    icon: "plant",
    title: "For fermentation plants",
    body: "Run Batchcast on your own batches and see how far ahead it can call the trajectory and the endpoint of your process.",
    cta: "Propose a pilot",
  },
  {
    icon: "growth",
    title: "For investors",
    body: "See the full evaluation, the limits we found and the plan for a model trained on fermentation data.",
    cta: "Ask for the full results",
  },
  {
    icon: "flask",
    title: "For researchers",
    body: "The evaluation runs on open data with open models. Compare methods with us or share a dataset.",
    cta: "Start a conversation",
  },
] as const;

/** Median forecast error (MASE, lower is better), all 5 channels. Chronos-2 channel by channel against repeating the last value. */
export const errorByContext = [
  { hours: 8, model: 6.349, simple: 8.886 },
  { hours: 16, model: 5.358, simple: 6.93 },
  { hours: 24, model: 4.568, simple: 6.023 },
  { hours: 32, model: 3.885, simple: 5.368 },
  { hours: 48, model: 3.377, simple: 4.461 },
];

/** Median MASE with 48 h of history, same 780 windows, all 5 channels. */
export const ranking = [
  { name: "Chronos-2, all channels together", value: 2.842, model: true },
  { name: "TimesFM 2.5", value: 3.135, model: true },
  { name: "Chronos-2, channel by channel", value: 3.377, model: true },
  { name: "Repeating the last value", value: 4.461, model: false },
  { name: "Linear extrapolation", value: 4.586, model: false },
];

/** Share of observations inside the 10% to 90% range, all history lengths. The range should hold 80%. */
export const coverageTarget = 0.8;
export const coverage = [
  { name: "Chronos-2 told the planned temperature and pH", value: 0.844 },
  { name: "Chronos-2, channel by channel", value: 0.891 },
  { name: "Chronos-2, all channels together", value: 0.938 },
];
