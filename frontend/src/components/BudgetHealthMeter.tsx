import React from 'react';

interface BudgetHealthMeterProps {
  budget: number;
  estimatedCost: number;
  actualExpenses?: number;
  className?: string;
}

export const BudgetHealthMeter: React.FC<BudgetHealthMeterProps> = ({
  budget,
  estimatedCost,
  actualExpenses,
  className = '',
}) => {
  const isActualAvailable = typeof actualExpenses === 'number' && actualExpenses > 0;
  const currentSpent = isActualAvailable ? actualExpenses : estimatedCost;
  
  // Prevent division by zero
  const safeBudget = budget || 1;
  const percentage = (currentSpent / safeBudget) * 100;
  const remaining = Math.max(0, budget - currentSpent);

  // Status colors & messages
  let statusColor = 'text-emerald-500';
  let progressColor = 'stroke-emerald-500';
  let bgColor = 'bg-emerald-50 dark:bg-emerald-950/20';
  let borderColor = 'border-emerald-200 dark:border-emerald-900/30';
  let message = 'Excellent budget utilization';

  if (percentage >= 70 && percentage <= 90) {
    statusColor = 'text-amber-500';
    progressColor = 'stroke-amber-500';
    bgColor = 'bg-amber-50 dark:bg-amber-950/20';
    borderColor = 'border-amber-200 dark:border-amber-900/30';
    message = 'Approaching budget limit';
  } else if (percentage > 90) {
    statusColor = 'text-rose-500';
    progressColor = 'stroke-rose-500';
    bgColor = 'bg-rose-50 dark:bg-rose-950/20';
    borderColor = 'border-rose-200 dark:border-rose-900/30';
    message = 'Budget exceeded';
  }

  // SVG Circular math
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (Math.min(100, percentage) / 100) * circumference;

  return (
    <div className={`p-6 rounded-2xl border ${bgColor} ${borderColor} flex flex-col sm:flex-row items-center gap-6 shadow-sm transition-all ${className}`}>
      
      {/* Circular Progress Gauge */}
      <div className="relative w-28 h-28 shrink-0 flex items-center justify-center">
        <svg className="w-full h-full -rotate-90">
          {/* Background Circle */}
          <circle
            cx="56"
            cy="56"
            r={radius}
            className="stroke-paper-200 dark:stroke-paper-700 fill-none"
            strokeWidth="8"
          />
          {/* Progress Circle */}
          <circle
            cx="56"
            cy="56"
            r={radius}
            className={`${progressColor} fill-none transition-all duration-500 ease-out`}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
        </svg>
        {/* Inner Text Label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-extrabold text-paper-800 dark:text-white">
            {percentage.toFixed(0)}%
          </span>
          <span className="text-[9px] text-paper-400 dark:text-paper-500 font-bold uppercase tracking-wider">
            Used
          </span>
        </div>
      </div>

      {/* Stats Description */}
      <div className="flex-1 space-y-3.5 w-full text-left">
        <div>
          <span className="text-[10px] text-paper-400 dark:text-paper-500 font-bold uppercase tracking-widest block">
            Budget Health
          </span>
          <h4 className={`text-base font-extrabold ${statusColor} flex items-center gap-1.5 mt-0.5`}>
            {message}
          </h4>
        </div>

        <div className="grid grid-cols-2 gap-4 text-xs">
          <div className="space-y-0.5">
            <span className="text-paper-400 dark:text-paper-500 font-semibold block">Target Budget</span>
            <span className="font-bold text-paper-700 dark:text-paper-300">₹{budget.toLocaleString()}</span>
          </div>

          <div className="space-y-0.5">
            <span className="text-paper-400 dark:text-paper-500 font-semibold block">Remaining</span>
            <span className="font-bold text-paper-700 dark:text-paper-300">₹{remaining.toLocaleString()}</span>
          </div>

          <div className="space-y-0.5">
            <span className="text-paper-400 dark:text-paper-500 font-semibold block">Estimated Cost</span>
            <span className="font-bold text-paper-700 dark:text-paper-300">₹{estimatedCost.toLocaleString()}</span>
          </div>

          {isActualAvailable && (
            <div className="space-y-0.5">
              <span className="text-paper-400 dark:text-paper-500 font-semibold block">Actual Spent</span>
              <span className="font-bold text-paper-700 dark:text-paper-300">₹{actualExpenses.toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>

    </div>
  );
};



