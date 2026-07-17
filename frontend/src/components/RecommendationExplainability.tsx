import React from 'react';
import { Check, Info } from 'lucide-react';

interface ScoreBreakdownData {
  budget_compatibility: number;
  trip_type_match: number;
  comfort_match: number;
  destination_rating: number;
  duration_suitability: number;
  explanations: string[];
}

interface RecommendationExplainabilityProps {
  destinationName: string;
  overallScore: number;
  breakdown?: ScoreBreakdownData;
  className?: string;
}

export const RecommendationExplainability: React.FC<RecommendationExplainabilityProps> = ({
  destinationName,
  overallScore,
  breakdown,
  className = '',
}) => {
  if (!breakdown) return null;

  const items = [
    { label: 'Budget Compatibility', value: breakdown.budget_compatibility },
    { label: 'Trip Type Match', value: breakdown.trip_type_match },
    { label: 'Comfort Match', value: breakdown.comfort_match },
    { label: 'Destination Rating', value: breakdown.destination_rating },
    { label: 'Duration Suitability', value: breakdown.duration_suitability },
  ];

  return (
    <div className={`bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm flex flex-col gap-6 ${className}`}>
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-700 pb-4">
        <div>
          <h3 className="font-extrabold text-slate-900 dark:text-white flex items-center gap-1.5">
            Why {destinationName}?
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Recommendation factors based on your travel preferences
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-center">
          <span className="text-[10px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider">
            Overall Match
          </span>
          <span className="bg-violet-100 dark:bg-violet-950/40 text-violet-700 dark:text-violet-400 text-sm font-extrabold px-3 py-1 rounded-xl border border-violet-200 dark:border-violet-900/30">
            {overallScore.toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Grid of Factors */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
        {items.map((item) => (
          <div key={item.label} className="p-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800 rounded-xl flex flex-col justify-between h-24">
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider block truncate">
                {item.label}
              </span>
              <div className="flex items-baseline gap-0.5">
                <span className="text-xl font-extrabold text-slate-900 dark:text-white">
                  {item.value.toFixed(0)}%
                </span>
              </div>
            </div>
            {/* Tiny progress bar */}
            <div className="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden mt-2">
              <div 
                className="bg-violet-600 h-full rounded-full" 
                style={{ width: `${item.value}%` }} 
              />
            </div>
          </div>
        ))}
      </div>

      {/* Explanations section */}
      <div className="bg-violet-50/50 dark:bg-violet-950/10 border border-violet-100/50 dark:border-violet-900/10 rounded-xl p-4 space-y-3">
        <h4 className="text-xs font-bold text-violet-800 dark:text-violet-300 flex items-center gap-1.5 uppercase tracking-wider">
          <Info size={14} />
          Details & Insights
        </h4>
        <ul className="space-y-2.5">
          {breakdown.explanations.map((exp, idx) => (
            <li key={idx} className="flex gap-2.5 items-start text-xs text-slate-600 dark:text-slate-300">
              <span className="p-0.5 bg-emerald-100 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400 rounded-full mt-0.5">
                <Check size={10} strokeWidth={3} />
              </span>
              <span>{exp}</span>
            </li>
          ))}
        </ul>
      </div>

    </div>
  );
};
