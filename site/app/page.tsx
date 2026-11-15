import { ContactForm } from "@/components/ContactForm";
import { HeroArt } from "@/components/HeroArt";
import { HowItWorks } from "@/components/HowItWorks";
import {
  audiences,
  biomassByContext,
  coverage,
  coverageTarget,
  credit,
  datasetFacts,
  errorByContext,
  gainByContext,
  headlineStats,
  intro,
  limitations,
  ranking,
  roadmap,
  secondModel,
  site,
} from "@/content";

const nav = [
  { href: "#how", label: "How it works" },
  { href: "#results", label: "Results" },
  { href: "#data", label: "Data" },
  { href: "#roadmap", label: "Roadmap" },
];

const shell = "mx-auto w-full max-w-[86rem] px-5 md:px-11";
const h2 = "mx-auto max-w-3xl text-center text-3xl tracking-tight md:text-4xl md:leading-[1.15]";
const lead = "mx-auto mt-6 max-w-2xl text-center text-lg";
const th = "py-3 pr-6 text-left text-sm font-normal text-steel";
const pillDark = "rounded-full bg-ink px-5 py-2.5 font-medium text-foam hover:bg-ink/80";
const pillLight = "rounded-full bg-band px-5 py-2.5 font-medium hover:bg-line";
const card = "rounded-md border border-line bg-white p-6";
const textLink = "underline decoration-line underline-offset-8 hover:decoration-ink";

const washes = ["wash", "wash-b", "wash-c"];
const maxError = Math.max(...errorByContext.map((row) => row.simple));
const maxRank = Math.max(...ranking.map((row) => row.value));
const maxGain = Math.max(...gainByContext.map((row) => row.gain));

const icons = {
  plant: "M9 3h6M10 3v4l-4 3v10h12V10l-4-3V3M6 14h12",
  growth: "M4 19h16M5 15l4-4 3 3 6-7M14 7h4v4",
  flask: "M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3M8 15h8",
};

export default function Page() {
  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-20 focus:z-20 focus:rounded-full focus:bg-band focus:px-4 focus:py-2"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-10 bg-foam/90 backdrop-blur">
        <div className={`${shell} flex h-16 items-center gap-10`}>
          <a href="#main" className="text-xl font-semibold tracking-tight">
            {site.name}
          </a>
          <nav aria-label="Sections" className="hidden gap-8 text-sm md:flex">
            {nav.map((item) => (
              <a key={item.href} href={item.href} className="hover:text-steel">
                {item.label}
              </a>
            ))}
          </nav>
          <a href="#contact" className={`${pillDark} ml-auto text-sm`}>
            Contact us
          </a>
        </div>
      </header>

      <main id="main">
        <section className="relative isolate flex min-h-[calc(100svh-4rem)] flex-col items-center justify-center px-5 py-24 text-center">
          <HeroArt />
          <h1 className="text-6xl font-medium tracking-tight md:text-9xl">{site.name}</h1>
          <p className="mt-6 max-w-3xl text-xl md:text-2xl">
            Know where a fermentation is going, from its first eight hours of sensor data.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <a href="#contact" className={pillDark}>
              Contact us
            </a>
            <a href="#results" className={pillLight}>
              See the results
            </a>
          </div>
        </section>

        <section className={`${shell} py-20 md:py-28`}>
          <p className="mx-auto max-w-2xl text-center text-lg md:text-xl md:leading-relaxed">{intro}</p>
        </section>

        <section id="how" className={`${shell} py-16 md:py-24`}>
          <h2 className={h2}>From sensor history to a forecast with a range</h2>
          <p className={lead}>{site.description}</p>
          <HowItWorks />
        </section>

        <section id="results" className={`${shell} py-20 md:py-28`}>
          <p className="text-center text-sm">Benchmark results</p>
          <h2 className={`${h2} mt-6`}>Tested on real yeast fermentations</h2>
          <dl className="mx-auto mt-12 grid max-w-4xl gap-x-8 gap-y-16 text-center sm:grid-cols-2">
            {headlineStats.map((stat) => (
              <div key={stat.note} className="flex flex-col">
                <dt className="order-2 mt-5 text-lg">
                  {stat.label}
                  <span className="mt-2 block text-sm text-steel">{stat.note}</span>
                </dt>
                <dd className="text-5xl tracking-tight md:text-6xl">{stat.value}</dd>
              </div>
            ))}
          </dl>
          <p className="mx-auto mt-16 max-w-2xl text-center text-steel">
            Gains are measured against the best simple method, such as repeating the last value. The open models,
            Chronos-2 and TimesFM 2.5, were not trained on this data.
          </p>

          <div className="mx-auto mt-20 max-w-4xl">
            <h3 className="text-2xl tracking-tight">Chronos-2 leads at every history length</h3>
            <table className="mt-6 w-full border-collapse">
              <caption className="sr-only">
                Chronos-2 accuracy gain over the best simple method, by hours of history, across all five channels
              </caption>
              <thead>
                <tr className="border-b border-line">
                  <th scope="col" className={th}>History</th>
                  <th scope="col" className={th}>Gain over the best simple method</th>
                </tr>
              </thead>
              <tbody>
                {gainByContext.map((row) => (
                  <tr key={row.hours} className="border-b border-line">
                    <th scope="row" className="w-24 py-4 pr-6 text-left text-lg font-normal tabular-nums">
                      {row.hours} h
                    </th>
                    <td className="py-4">
                      <div className="flex items-center gap-4">
                        <div
                          className="h-6 rounded-sm bg-tank"
                          style={{ width: `${(row.gain / maxGain) * 80}%` }}
                          aria-hidden="true"
                        />
                        <span className="text-lg">+{row.gain}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="mt-16 grid gap-12 md:grid-cols-2">
              <div>
                <h3 className="text-2xl tracking-tight">Biomass, the channel that sets the outcome</h3>
                <p className="mt-3 text-steel">
                  Chronos-2, forecasting all channels together, against repeating the last value.
                </p>
                <table className="mt-5 w-full border-collapse tabular-nums">
                  <thead>
                    <tr className="border-b border-line">
                      <th scope="col" className={th}>History</th>
                      <th scope="col" className={th}>Gain</th>
                      <th scope="col" className={th}>Windows won</th>
                    </tr>
                  </thead>
                  <tbody>
                    {biomassByContext.map((row) => (
                      <tr key={row.hours} className="border-b border-line">
                        <th scope="row" className="py-3 pr-6 text-left font-normal">{row.hours} h</th>
                        <td className="py-3 pr-6">+{row.gain}%</td>
                        <td className="py-3">{row.wins}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <h3 className="text-2xl tracking-tight">A second open model agrees</h3>
                <p className="mt-3 text-steel">
                  TimesFM 2.5 with 48 hours of history, on the same 780 windows and all five channels.
                </p>
                <table className="mt-5 w-full border-collapse tabular-nums">
                  <thead>
                    <tr className="border-b border-line">
                      <th scope="col" className={th}>Compared with</th>
                      <th scope="col" className={th}>Gain</th>
                      <th scope="col" className={th}>Windows won</th>
                    </tr>
                  </thead>
                  <tbody>
                    {secondModel.map((row) => (
                      <tr key={row.against} className="border-b border-line">
                        <th scope="row" className="py-3 pr-6 text-left font-normal">{row.against}</th>
                        <td className="py-3 pr-6">+{row.gain}%</td>
                        <td className="py-3">{row.wins}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        <section className={`${shell} pb-20 md:pb-28`}>
          <h2 className={h2}>More from the evaluation</h2>
          <p className={lead}>
            Forecast error is measured as MASE, where lower is better. Every bar is a median over the test windows.
          </p>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            <figure className={card}>
              <figcaption>
                <h3 className="text-xl tracking-tight">Error falls as the batch runs</h3>
                <p className="mt-3 text-sm text-steel">
                  Chronos-2 (green) against repeating the last value (grey), by hours of history.
                </p>
              </figcaption>
              <ul className="mt-6 space-y-4">
                {errorByContext.map((row) => (
                  <li key={row.hours} className="grid grid-cols-[3rem_1fr] items-center gap-3 text-sm">
                    <span>{row.hours} h</span>
                    <span className="space-y-1">
                      {[
                        { name: "Chronos-2", value: row.model, tone: "bg-tank" },
                        { name: "last value", value: row.simple, tone: "bg-steel/40" },
                      ].map((bar) => (
                        <span key={bar.name} className="flex items-center gap-2">
                          <span
                            className={`h-3 rounded-sm ${bar.tone}`}
                            style={{ width: `${(bar.value / maxError) * 75}%` }}
                            aria-hidden="true"
                          />
                          <span>
                            {bar.value.toFixed(2)} <span className="sr-only">{bar.name}</span>
                          </span>
                        </span>
                      ))}
                    </span>
                  </li>
                ))}
              </ul>
            </figure>

            <figure className={card}>
              <figcaption>
                <h3 className="text-xl tracking-tight">Open models ahead of simple methods</h3>
                <p className="mt-3 text-sm text-steel">
                  Error with 48 hours of history, on the same 780 windows. Models in green, simple methods in grey.
                </p>
              </figcaption>
              <ul className="mt-6 space-y-4 text-sm">
                {ranking.map((row) => (
                  <li key={row.name}>
                    {row.name}
                    <span className="mt-1 flex items-center gap-2">
                      <span
                        className={`h-3 rounded-sm ${row.model ? "bg-tank" : "bg-steel/40"}`}
                        style={{ width: `${(row.value / maxRank) * 80}%` }}
                        aria-hidden="true"
                      />
                      {row.value.toFixed(2)}
                    </span>
                  </li>
                ))}
              </ul>
            </figure>

            <figure className={card}>
              <figcaption>
                <h3 className="text-xl tracking-tight">Ranges hold when channels are forecast together</h3>
                <p className="mt-3 text-sm text-steel">
                  Share of measurements that fell inside the 10% to 90% range. The line marks the{" "}
                  {coverageTarget * 100}% it should hold.
                </p>
              </figcaption>
              <ul className="mt-6 space-y-4 text-sm">
                {coverage.map((row) => (
                  <li key={row.name}>
                    {row.name}
                    <span className="mt-1 flex items-center gap-2">
                      <span className="relative h-3 flex-1 rounded-sm bg-band" aria-hidden="true">
                        <span
                          className="absolute inset-y-0 left-0 rounded-sm bg-tank"
                          style={{ width: `${row.value * 100}%` }}
                        />
                        <span
                          className="absolute -inset-y-1 w-0.5 bg-ink"
                          style={{ left: `${coverageTarget * 100}%` }}
                        />
                      </span>
                      {Math.round(row.value * 1000) / 10}%
                    </span>
                  </li>
                ))}
              </ul>
            </figure>
          </div>
        </section>

        <section id="roadmap" className="bg-band py-20 md:py-28">
          <div className={shell}>
            <h2 className={h2}>A free, general model already beats the simple methods</h2>
            <p className={lead}>The remaining gains come from data that only fermentation plants have.</p>
            <ol className="mx-auto mt-10 grid max-w-6xl gap-6 md:grid-cols-3">
              {roadmap.map((item, index) => (
                <li key={item.title} className={card}>
                  <span
                    className="flex h-5 w-5 items-center justify-center rounded-full bg-ink text-xs font-semibold text-foam"
                    aria-hidden="true"
                  >
                    {index + 1}
                  </span>
                  <h3 className="mt-6 text-xl tracking-tight">{item.title}</h3>
                  <p className="mt-5 text-sm leading-relaxed">{item.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="data" className={`${shell} py-20 md:py-28`}>
          <h2 className={h2}>Measured on real batches, with the limits stated</h2>
          <p className={lead}>
            Every number on this page comes from {datasetFacts[0].value} brewing-yeast propagation runs, half
            Saccharomyces cerevisiae and half S. pastorianus. Gains are median differences in scaled forecast error
            (MASE), compared window by window.
          </p>
          <dl className="mt-10 grid gap-6 sm:grid-cols-2 md:grid-cols-3">
            {datasetFacts.map((fact) => (
              <div key={fact.label} className={`${card} flex flex-col`}>
                <dt className="order-2 mt-3 text-sm">{fact.label}</dt>
                <dd className="text-4xl tracking-tight">{fact.value}</dd>
              </div>
            ))}
          </dl>
          <div className="mx-auto mt-10 max-w-3xl rounded-md bg-band p-8">
            <h3 className="text-xl tracking-tight">What these results do not show</h3>
            <ul className="mt-5 list-disc space-y-3 pl-5">
              {limitations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </section>

        <section className={`${shell} py-20 md:py-28`}>
          <h2 className={h2}>Choose how to start</h2>
          <div className="mt-10 grid gap-x-6 gap-y-12 md:grid-cols-3">
            {audiences.map((audience, index) => (
              <div key={audience.title}>
                <div className={`${washes[index]} flex aspect-square items-center justify-center rounded-md`}>
                  <div className="flex h-28 w-28 items-center justify-center rounded-2xl bg-white shadow-xl shadow-black/20">
                    <svg
                      viewBox="0 0 24 24"
                      className="h-14 w-14"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d={icons[audience.icon]} />
                    </svg>
                  </div>
                </div>
                <h3 className="mt-6 text-lg">{audience.title}</h3>
                <p className="mt-3 text-sm leading-relaxed">{audience.body}</p>
                <a href="#contact" className={`${textLink} mt-4 inline-block text-sm`}>
                  {audience.cta}
                </a>
              </div>
            ))}
          </div>
        </section>

        <section id="contact" className={`${shell} pb-20`}>
          <div className="rounded-md bg-band px-5 py-16 md:py-24">
            <h2 className={`${h2} md:text-5xl`}>Bring forecasting to your fermentations</h2>
            <p className={lead}>
              Tell us about your process or your interest. We read every message and reply by email.
            </p>
            <div className="mx-auto mt-10 max-w-xl">
              <ContactForm />
            </div>
          </div>
        </section>
      </main>

      <footer className={`${shell} border-t border-line py-10 text-sm text-steel`}>
        <p>
          Data: {credit.dataset},{" "}
          <a className="underline" href={`https://doi.org/${credit.doi}`}>
            DOI {credit.doi}
          </a>
          , {credit.licence}. Models: {credit.models}.
        </p>
        <p className="mt-2">{site.name}</p>
      </footer>
    </>
  );
}
