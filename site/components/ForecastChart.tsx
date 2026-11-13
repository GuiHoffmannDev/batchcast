// A real forecast, exported by ../../spike/export_forecast.py from the evaluation's own code and data.
import forecast from "@/data/forecast.json";

const W = 1200;
const H = 520;
const PAD = 40;

const { history, actual, point, quantiles, step_h: step } = forecast;
const total = history.length + actual.length;
const all = [...history, ...actual, ...quantiles.flat()];
const lo = Math.min(...all);
const hi = Math.max(...all);

const x = (i: number) => (i / (total - 1)) * W;
const y = (v: number) => H - PAD - ((v - lo) / (hi - lo)) * (H - 2 * PAD);
const line = (points: [number, number][]) =>
  points.map(([px, py], i) => `${i ? "L" : "M"}${px.toFixed(1)} ${py.toFixed(1)}`).join(" ");

const now = history.length - 1;
// Forecast series start at the last measured point so the lines join.
const ahead = (values: number[]): [number, number][] => [
  [x(now), y(history[now])],
  ...values.map((v, i): [number, number] => [x(now + 1 + i), y(v)]),
];
// quantiles[0..8] are 10%..90%; pair them from the outside in.
const bands = [0, 1, 2, 3].map(
  (k) => `${line([...ahead(quantiles[k]), ...ahead(quantiles[8 - k]).reverse()])} Z`,
);

const descriptions = [
  `A biomass signal measured for the first ${forecast.context_h} hours of a real batch.`,
  `The same signal with a forecast line extending ${forecast.horizon_h} hours past the last measurement.`,
  "The forecast line surrounded by bands that widen with time, marking the 10% to 90% range.",
  "The forecast and its range, with the values the batch later measured drawn on top. Almost all measured values fall inside the range.",
];

/** stage 0: history. 1: plus the forecast. 2: plus the uncertainty bands. 3: plus what the batch really did. */
export function ForecastChart({ stage }: { stage: number }) {
  return (
    <figure>
      <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label={descriptions[stage]}>
        <line x1="0" y1={H - PAD} x2={W} y2={H - PAD} className="stroke-line" strokeWidth="2" />
        <line
          x1={x(now)}
          y1="10"
          x2={x(now)}
          y2={H - PAD}
          className="stroke-steel"
          strokeWidth="2"
          strokeDasharray="4 8"
        />
        <path
          d={line(history.map((v, i) => [x(i), y(v)]))}
          fill="none"
          strokeWidth="5"
          className="stroke-ink"
        />
        {stage > 0 && (
          // The key restarts the draw-in animation when the stage changes.
          <g key={stage} className="forecast-fan">
            {stage > 1 && bands.map((d) => <path key={d} d={d} className="fill-tank" opacity="0.16" />)}
            <path d={line(ahead(point))} fill="none" strokeWidth="5" className="stroke-wort" />
            {stage > 2 && (
              <path
                d={line(ahead(actual))}
                fill="none"
                strokeWidth="4"
                strokeDasharray="2 10"
                strokeLinecap="round"
                className="stroke-ink"
              />
            )}
          </g>
        )}
        <circle cx={x(now)} cy={y(history[now])} r="9" className="fill-ink" />
      </svg>
      <figcaption className="mt-3 text-sm text-steel">
        Real forecast by {forecast.model} on one yeast batch, {step * 60}-minute readings. A typical case: its
        error ({forecast.mase}) sits at the median of {forecast.n_windows} test windows ({forecast.median_mase}).
      </figcaption>
    </figure>
  );
}
