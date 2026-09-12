import React from 'react';
import { ArrowRight } from 'lucide-react';

interface GuideStep {
  title: string;
  description: string;
}

interface TripFlowGuideProps {
  eyebrow: string;
  title: string;
  description: string;
  steps: GuideStep[];
  ctaLabel?: string;
}

export const TripFlowGuide: React.FC<TripFlowGuideProps> = ({
  eyebrow,
  title,
  description,
  steps,
  ctaLabel
}) => {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-marigold-200/70 dark:border-marigold-900/50 bg-gradient-to-br from-marigold-50 via-white to-petrol-50 dark:from-paper-900 dark:via-paper-900 dark:to-paper-800 p-6 shadow-sm">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(124,58,237,0.14),transparent_32%),radial-gradient(circle_at_bottom_left,rgba(59,130,246,0.12),transparent_28%)]" />
      <div className="relative flex flex-col gap-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <span className="inline-flex items-center rounded-full border border-marigold-200 bg-paper-50/80 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.22em] text-marigold-700 dark:border-marigold-800 dark:bg-paper-900/70 dark:text-marigold-300">
              {eyebrow}
            </span>
            <h2 className="text-2xl font-black tracking-tight text-paper-900 dark:text-white">
              {title}
            </h2>
            <p className="max-w-3xl text-sm leading-relaxed text-paper-600 dark:text-paper-300">
              {description}
            </p>
          </div>

          {ctaLabel ? (
            <div className="inline-flex items-center gap-2 rounded-2xl bg-paper-900 px-4 py-3 text-xs font-bold text-white shadow-lg shadow-paper-900/10 dark:bg-marigold-600 dark:shadow-marigold-900/20">
              {ctaLabel}
              <ArrowRight size={14} />
            </div>
          ) : null}
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {steps.map((step, index) => (
            <div
              key={step.title}
              className="rounded-2xl border border-white/70 dark:border-paper-700/70 bg-paper-50/80 dark:bg-paper-900/60 p-4 backdrop-blur"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-marigold-600 text-sm font-black text-white">
                  {index + 1}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-paper-900 dark:text-white">{step.title}</h3>
                  <p className="text-xs leading-relaxed text-paper-500 dark:text-paper-400">{step.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};


