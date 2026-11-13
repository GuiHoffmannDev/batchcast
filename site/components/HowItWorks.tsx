"use client";

import { useState } from "react";
import { ForecastChart } from "@/components/ForecastChart";
import { steps } from "@/content";

export function HowItWorks() {
  const [active, setActive] = useState(0);

  return (
    <div className="mt-12 grid gap-8 md:grid-cols-[1fr_3fr] md:gap-6">
      <ol>
        {steps.map((step, index) => {
          const open = index === active;
          return (
            <li key={step.title} className="border-b border-line">
              <h3>
                <button
                  type="button"
                  aria-expanded={open}
                  aria-controls={`step-${index}`}
                  onClick={() => setActive(index)}
                  className={`w-full py-5 text-left ${open ? "text-2xl" : "text-steel hover:text-ink"}`}
                >
                  {step.title}
                </button>
              </h3>
              <p id={`step-${index}`} hidden={!open} className="pb-6 text-steel">
                {step.body}
              </p>
            </li>
          );
        })}
      </ol>

      <div className="wash flex items-center justify-center rounded-md p-5 md:min-h-[34rem] md:p-16">
        <div className="w-full max-w-3xl rounded-2xl bg-white p-5 shadow-2xl shadow-black/30 md:p-10">
          <p className="mb-4 font-medium">Biomass signal, batch in progress</p>
          <ForecastChart stage={active} />
        </div>
      </div>
    </div>
  );
}
