"use client";

import { useEffect, useRef } from "react";

// Nine quantile curves that share one history and fan out after "now", echoing the product's output.
const ENDS = [70, 150, 220, 280, 330, 380, 440, 510, 590];
const MEDIAN = 330;

/** tilt moves the whole fan up or down; spread opens or closes it; lean shifts where it bends. */
function fanPath(end: number, tilt = 0, spread = 1, lean = 0) {
  const y = MEDIAN + (end - MEDIAN) * spread + tilt;
  return `M500 520 C ${760 + lean} 350, ${1080 + lean} ${y}, 1440 ${y}`;
}

export function HeroArt() {
  const svg = useRef<SVGSVGElement>(null);

  // The fan follows the pointer: up and down tilts the forecast, left and right narrows or widens the range.
  useEffect(() => {
    const area = svg.current?.parentElement;
    const paths = svg.current?.querySelectorAll<SVGPathElement>("[data-end]");
    if (!area || !paths) return;
    if (!window.matchMedia("(hover: hover) and (prefers-reduced-motion: no-preference)").matches) return;

    const target = { x: 0, y: 0 };
    const current = { x: 0, y: 0 };
    let frame = 0;

    const draw = () => {
      current.x += (target.x - current.x) * 0.08;
      current.y += (target.y - current.y) * 0.08;
      paths.forEach((path) => {
        path.setAttribute(
          "d",
          fanPath(Number(path.dataset.end), current.y * 90, 1 + current.x * 0.35, current.x * 120),
        );
      });
      const settled = Math.abs(target.x - current.x) < 0.001 && Math.abs(target.y - current.y) < 0.001;
      frame = settled ? 0 : requestAnimationFrame(draw);
    };

    const aim = (x: number, y: number) => {
      target.x = x;
      target.y = y;
      if (!frame) frame = requestAnimationFrame(draw);
    };
    const move = (event: PointerEvent) => {
      const box = area.getBoundingClientRect();
      aim((event.clientX - box.left) / box.width - 0.5, (event.clientY - box.top) / box.height - 0.5);
    };
    const rest = () => aim(0, 0);

    area.addEventListener("pointermove", move);
    area.addEventListener("pointerleave", rest);
    return () => {
      area.removeEventListener("pointermove", move);
      area.removeEventListener("pointerleave", rest);
      cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <svg
      ref={svg}
      viewBox="0 0 1440 700"
      preserveAspectRatio="none"
      aria-hidden="true"
      className="absolute inset-0 -z-10 h-full w-full"
      fill="none"
    >
      <path d="M0 640 C 260 640, 380 600, 500 520" className="stroke-line" strokeWidth="1.5" />
      <g className="forecast-fan">
        {ENDS.map((end) => (
          <path
            key={end}
            data-end={end}
            d={fanPath(end)}
            className={end === MEDIAN ? "stroke-wort/50" : "stroke-line"}
            strokeWidth="1.5"
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </g>
    </svg>
  );
}
