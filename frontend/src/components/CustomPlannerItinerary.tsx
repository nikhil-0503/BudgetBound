import React, { useMemo } from 'react';
import {
  MapPin,
  Clock,
  DollarSign,
  AlertCircle,
  Building,
  Utensils,
  Camera,
  Plane,
  AlertTriangle,
  CheckCircle,
  Zap,
  Target,
  Sparkles,
  Info
} from 'lucide-react';

interface Activity {
  time: string;
  start_time?: string;
  title: string;
  description: string;
  cost: number | string;
  duration?: string;
  location?: string;
}

interface Day {
  day_number: number;
  title: string;
  description: string;
  activities: Activity[];
}

interface BudgetBreakdown {
  accommodation_per_night?: number;
  food_per_day?: number;
  activities_per_day?: number;
  transport?: number;
  contingency?: number;
}

interface Requirement {
  key: string;
  category: string;
  value: string;
  matched_keywords: string[];
}

interface CustomPlannerItineraryProps {
  plan_name: string;
  destination: string;
  num_days: number;
  estimated_total_cost: number;
  budget_limit: number;
  summary: string;
  budget_breakdown?: BudgetBreakdown;
  days: Day[];
  requirements_extracted?: Requirement[];
  requirements_coverage?: Record<string, string>;
  validation_warnings?: string[];
  data_source?: string;
  semantic_score?: number;
  feasibility_score?: number;
  requirement_coverage_score?: number;
}

export const CustomPlannerItinerary: React.FC<CustomPlannerItineraryProps> = ({
  plan_name,
  destination,
  num_days,
  estimated_total_cost,
  budget_limit,
  summary,
  budget_breakdown,
  days,
  requirements_extracted = [],
  requirements_coverage = {},
  validation_warnings = [],
  data_source = "llm",
  semantic_score = 0,
  feasibility_score = 0,
  requirement_coverage_score = 0
}) => {
  const parseCost = (cost: number | string): number => {
    if (typeof cost === 'number') return cost;
    if (typeof cost === 'string') {
      const match = cost.match(/\d+\.?\d*/);
      return match ? parseFloat(match[0]) : 0;
    }
    return 0;
  };

  // Calculate overall quality score
  const overallQualityScore = useMemo(() => {
    return Math.round((semantic_score + feasibility_score + requirement_coverage_score) / 3);
  }, [semantic_score, feasibility_score, requirement_coverage_score]);

  // Get quality badge color based on score
  const getQualityColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-900/40 text-emerald-700 dark:text-emerald-300';
    if (score >= 60) return 'bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-900/40 text-blue-700 dark:text-blue-300';
    return 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900/40 text-amber-700 dark:text-amber-300';
  };

  const getQualityBadge = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    return 'Fair';
  };

  // Calculate total activity costs
  const activityCosts = useMemo(() => {
    let total = 0;
    days.forEach(day => {
      day.activities?.forEach(act => {
        total += parseCost(act.cost);
      });
    });
    return total;
  }, [days]);

  // Calculate breakdown totals
  const breakdownTotals = useMemo(() => {
    if (!budget_breakdown) return null;
    
    const accommodation = (budget_breakdown.accommodation_per_night || 0) * num_days;
    const food = (budget_breakdown.food_per_day || 0) * num_days;
    const activities = (budget_breakdown.activities_per_day || 0) * num_days;
    const transport = budget_breakdown.transport || 0;
    const contingency = budget_breakdown.contingency || 0;
    
    const total = accommodation + food + activities + transport + contingency;
    
    return {
      accommodation,
      food,
      activities,
      transport,
      contingency,
      total
    };
  }, [budget_breakdown, num_days]);

  const isOverBudget = estimated_total_cost > budget_limit;
  const remaining = budget_limit - estimated_total_cost;

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* Trip Overview */}
      <div className="bg-gradient-to-br from-marigold-50 to-petrol-50 dark:from-paper-900/60 dark:to-paper-800/60 border border-marigold-200 dark:border-marigold-900/40 rounded-2xl p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-2xl font-extrabold text-paper-900 dark:text-white mb-1">
              {plan_name}
            </h3>
            <p className="text-sm text-paper-600 dark:text-paper-400 mb-3">
              {num_days}-day customized journey
            </p>
            <p className="text-xs text-paper-600 dark:text-paper-400 leading-relaxed bg-paper-50 dark:bg-paper-900/30 p-3 rounded-lg border border-paper-200 dark:border-paper-700">
              {summary}
            </p>
          </div>
          <div className="flex-shrink-0">
            <div className="h-12 w-12 rounded-full bg-marigold-600/10 dark:bg-marigold-950/30 flex items-center justify-center">
              <MapPin className="text-marigold-600 dark:text-marigold-400" size={24} />
            </div>
          </div>
        </div>
      </div>

      {/* Plan Quality & Metadata */}
      <div className={`border rounded-2xl p-6 ${getQualityColor(overallQualityScore)}`}>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="flex items-center gap-3">
            <Sparkles size={20} />
            <div>
              <p className="text-[10px] font-bold uppercase opacity-75">Overall Quality</p>
              <p className="text-lg font-bold">{overallQualityScore}% {getQualityBadge(overallQualityScore)}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Target size={20} />
            <div>
              <p className="text-[10px] font-bold uppercase opacity-75">Requirement Match</p>
              <p className="text-lg font-bold">{Math.round(requirement_coverage_score)}%</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Zap size={20} />
            <div>
              <p className="text-[10px] font-bold uppercase opacity-75">Feasibility</p>
              <p className="text-lg font-bold">{Math.round(feasibility_score)}%</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Info size={20} />
            <div>
              <p className="text-[10px] font-bold uppercase opacity-75">Data Source</p>
              <p className="text-lg font-bold capitalize">{data_source === 'llm' ? '🤖 AI Generated' : '⚙️ Fallback'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Validation Warnings */}
      {validation_warnings && validation_warnings.length > 0 && (
        <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 rounded-2xl p-4">
          <h5 className="text-xs font-bold text-amber-900 dark:text-amber-200 uppercase mb-3 flex items-center gap-2">
            <AlertTriangle size={16} />
            Validation Notes
          </h5>
          <ul className="text-xs text-amber-800 dark:text-amber-300 space-y-1.5 ml-5">
            {validation_warnings.map((warning, idx) => (
              <li key={idx}>• {warning}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Extracted Requirements */}
      {requirements_extracted && requirements_extracted.length > 0 && (
        <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6">
          <h4 className="text-base font-bold text-paper-900 dark:text-white mb-4 flex items-center gap-2">
            <Target size={18} className="text-marigold-600" />
            Your Preferences in This Itinerary
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {requirements_extracted.map((req, idx) => {
              const coverage = requirements_coverage?.[req.key] || 'unknown';
              const isCovered = coverage === 'covered';
              
              return (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border flex items-start gap-3 ${
                    isCovered
                      ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/40'
                      : coverage === 'partial'
                      ? 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900/40'
                      : 'bg-paper-100 dark:bg-paper-900/50 border-paper-200 dark:border-paper-700'
                  }`}
                >
                  <div className="flex-shrink-0 pt-0.5">
                    {isCovered ? (
                      <CheckCircle size={16} className="text-emerald-600 dark:text-emerald-400" />
                    ) : coverage === 'partial' ? (
                      <AlertCircle size={16} className="text-blue-600 dark:text-blue-400" />
                    ) : (
                      <AlertCircle size={16} className="text-paper-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-paper-900 dark:text-white capitalize">
                      {req.category.replace(/_/g, ' ')}
                    </p>
                    <p className="text-xs text-paper-600 dark:text-paper-400 mt-0.5 break-words">
                      {req.value}
                    </p>
                    {req.matched_keywords && req.matched_keywords.length > 0 && (
                      <div className="mt-1.5 flex flex-wrap gap-1">
                        {req.matched_keywords.slice(0, 2).map((kw, i) => (
                          <span
                            key={i}
                            className="inline-block bg-paper-200 dark:bg-paper-700 text-paper-700 dark:text-paper-300 px-1.5 py-0.5 rounded text-[9px] font-semibold"
                          >
                            {kw}
                          </span>
                        ))}
                        {req.matched_keywords.length > 2 && (
                          <span className="text-[9px] text-paper-500 dark:text-paper-400 font-semibold">
                            +{req.matched_keywords.length - 2} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Budget Summary */}
      <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6">
        <h4 className="text-base font-bold text-paper-900 dark:text-white mb-4 flex items-center gap-2">
          <DollarSign size={18} className="text-marigold-600" />
          Budget Summary
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-paper-100 dark:bg-paper-900/50 rounded-xl p-4 border border-paper-200 dark:border-paper-700">
            <p className="text-[10px] text-paper-400 font-bold uppercase mb-1">Maximum Budget</p>
            <p className="text-lg font-bold text-paper-900 dark:text-white">
              Rs. {budget_limit?.toLocaleString()}
            </p>
          </div>

          <div className={`rounded-xl p-4 border ${
            isOverBudget
              ? 'bg-rose-50 dark:bg-rose-950/30 border-rose-200 dark:border-rose-900/40'
              : 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-900/40'
          }`}>
            <p className="text-[10px] font-bold uppercase mb-1 flex items-center gap-1">
              {isOverBudget ? (
                <>
                  <AlertTriangle size={12} className="text-rose-600 dark:text-rose-400" />
                  <span className="text-rose-600 dark:text-rose-400">Estimated Total</span>
                </>
              ) : (
                <span className="text-emerald-600 dark:text-emerald-400">Estimated Total</span>
              )}
            </p>
            <p className={`text-lg font-bold ${isOverBudget ? 'text-rose-700 dark:text-rose-300' : 'text-emerald-700 dark:text-emerald-300'}`}>
              Rs. {estimated_total_cost?.toLocaleString()}
            </p>
          </div>

          <div className={`rounded-xl p-4 border ${
            remaining >= 0
              ? 'bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-900/40'
              : 'bg-rose-50 dark:bg-rose-950/30 border-rose-200 dark:border-rose-900/40'
          }`}>
            <p className="text-[10px] font-bold uppercase mb-1">
              {remaining >= 0 ? (
                <span className="text-blue-600 dark:text-blue-400">Remaining Budget</span>
              ) : (
                <span className="text-rose-600 dark:text-rose-400">Over Budget</span>
              )}
            </p>
            <p className={`text-lg font-bold ${remaining >= 0 ? 'text-blue-700 dark:text-blue-300' : 'text-rose-700 dark:text-rose-300'}`}>
              Rs. {Math.abs(remaining)?.toLocaleString()}
            </p>
          </div>
        </div>

        {isOverBudget && (
          <div className="bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/40 rounded-lg p-3 flex gap-2">
            <AlertCircle size={16} className="text-rose-600 dark:text-rose-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-rose-700 dark:text-rose-300">
              Estimated cost exceeds budget by Rs. {Math.abs(remaining)?.toLocaleString()}. Consider adjusting days, comfort level, or budget.
            </p>
          </div>
        )}
      </div>

      {/* Budget Breakdown Details */}
      {breakdownTotals && (
        <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6">
          <h4 className="text-base font-bold text-paper-900 dark:text-white mb-4">Budget Breakdown</h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center p-3 bg-paper-100 dark:bg-paper-900/50 rounded-lg">
                <span className="flex items-center gap-2 text-paper-700 dark:text-paper-300">
                  <Building size={14} className="text-marigold-600" />
                  Accommodation
                </span>
                <span className="font-bold text-paper-900 dark:text-white">
                  Rs. {breakdownTotals.accommodation?.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-3 bg-paper-100 dark:bg-paper-900/50 rounded-lg">
                <span className="flex items-center gap-2 text-paper-700 dark:text-paper-300">
                  <Utensils size={14} className="text-marigold-600" />
                  Food & Dining
                </span>
                <span className="font-bold text-paper-900 dark:text-white">
                  Rs. {breakdownTotals.food?.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-3 bg-paper-100 dark:bg-paper-900/50 rounded-lg">
                <span className="flex items-center gap-2 text-paper-700 dark:text-paper-300">
                  <Camera size={14} className="text-marigold-600" />
                  Activities
                </span>
                <span className="font-bold text-paper-900 dark:text-white">
                  Rs. {breakdownTotals.activities?.toLocaleString()}
                </span>
              </div>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center p-3 bg-paper-100 dark:bg-paper-900/50 rounded-lg">
                <span className="flex items-center gap-2 text-paper-700 dark:text-paper-300">
                  <Plane size={14} className="text-marigold-600" />
                  Transport
                </span>
                <span className="font-bold text-paper-900 dark:text-white">
                  Rs. {breakdownTotals.transport?.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-3 bg-paper-100 dark:bg-paper-900/50 rounded-lg">
                <span className="flex items-center gap-2 text-paper-700 dark:text-paper-300">
                  <AlertCircle size={14} className="text-marigold-600" />
                  Contingency
                </span>
                <span className="font-bold text-paper-900 dark:text-white">
                  Rs. {breakdownTotals.contingency?.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-3 bg-marigold-100 dark:bg-marigold-950/30 rounded-lg border border-marigold-200 dark:border-marigold-900/40">
                <span className="font-bold text-marigold-900 dark:text-marigold-200">Total</span>
                <span className="font-bold text-marigold-900 dark:text-marigold-200">
                  Rs. {breakdownTotals.total?.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Planned Schedule - Daily Itinerary */}
      <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6">
        <h4 className="text-base font-bold text-paper-900 dark:text-white mb-4 flex items-center gap-2">
          <Clock size={18} className="text-marigold-600" />
          Planned Schedule
        </h4>

        <div className="space-y-6">
          {days.map((day) => (
            <div key={day.day_number} className="border border-paper-200 dark:border-paper-700 rounded-xl overflow-hidden">
              {/* Day Header */}
              <div className="bg-gradient-to-r from-paper-100 to-paper-50 dark:from-paper-900/50 dark:to-paper-900/30 px-4 py-3 border-b border-paper-200 dark:border-paper-700">
                <h5 className="text-sm font-bold text-paper-900 dark:text-white">
                  DAY {day.day_number.toString().padStart(2, '0')} - {day.title}
                </h5>
                <p className="text-xs text-paper-500 dark:text-paper-400 mt-1">
                  {day.description}
                </p>
              </div>

              {/* Activities */}
              <div className="divide-y divide-paper-100 dark:divide-paper-700">
                {day.activities?.map((activity, idx) => (
                  <div key={idx} className="p-4 hover:bg-paper-100 dark:hover:bg-paper-900/50 transition-colors">
                    <div className="flex flex-col gap-3">
                      {/* Time and Title */}
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 pt-1">
                          <span className="inline-block bg-marigold-100 dark:bg-marigold-950/40 text-marigold-700 dark:text-marigold-300 px-2.5 py-1 rounded text-xs font-bold">
                            {activity.time}
                          </span>
                        </div>
                        <div className="flex-1">
                          <h6 className="font-bold text-sm text-paper-900 dark:text-white">
                            {activity.title}
                          </h6>
                          {activity.start_time && (
                            <p className="text-xs text-paper-500 dark:text-paper-400 mt-0.5">
                              {activity.start_time}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-xs text-paper-600 dark:text-paper-400 leading-relaxed ml-14">
                        {activity.description}
                      </p>

                      {/* Details Grid */}
                      <div className="grid grid-cols-2 gap-3 ml-14 pt-2">
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-paper-500 dark:text-paper-400 font-semibold">Cost:</span>
                          <span className="text-paper-900 dark:text-paper-100 font-bold">
                            Rs. {parseCost(activity.cost).toLocaleString()}
                          </span>
                        </div>

                        {activity.duration && (
                          <div className="flex items-center gap-2 text-xs">
                            <Clock size={12} className="text-marigold-600" />
                            <span className="text-paper-600 dark:text-paper-400">
                              {activity.duration}
                            </span>
                          </div>
                        )}

                        {activity.location && (
                          <div className="col-span-2 flex items-center gap-2 text-xs">
                            <MapPin size={12} className="text-marigold-600" />
                            <span className="text-paper-600 dark:text-paper-400">
                              {activity.location}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Day Total */}
              <div className="bg-paper-100 dark:bg-paper-900/30 px-4 py-2 flex justify-between items-center text-xs border-t border-paper-200 dark:border-paper-700">
                <span className="font-semibold text-paper-700 dark:text-paper-300">Day {day.day_number} Total</span>
                <span className="font-bold text-paper-900 dark:text-white">
                  Rs. {(day.activities?.reduce((sum, act) => sum + parseCost(act.cost), 0) || 0).toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Important Notes */}
      <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/40 rounded-xl p-4">
        <h5 className="text-xs font-bold text-blue-900 dark:text-blue-200 uppercase mb-2 flex items-center gap-1.5">
          <AlertCircle size={14} />
          Important Notes
        </h5>
        <ul className="text-xs text-blue-800 dark:text-blue-300 space-y-1.5 ml-5">
          <li>• All costs are estimates based on average rates. Actual costs may vary.</li>
          <li>• Prices do not include visa, insurance, or international travel documentation.</li>
          <li>• Peak season and local events may affect accommodation and activity availability.</li>
          <li>• Travel times between activities are not included in estimated durations.</li>
          <li>• Always book accommodations and activities in advance during peak travel seasons.</li>
        </ul>
      </div>
    </div>
  );
};
