import React, { useState } from 'react';
import { AlertCircle, TrendingUp, TrendingDown, HelpCircle, Check, ChevronDown } from 'lucide-react';

interface CostExplanation {
  category: string;
  selected_option: string;
  selected_cost: number;
  estimated_cost: number;
  allocation_percentage: number;
  decision_factors: string[];
  alternatives?: Array<{
    mode?: string;
    tier?: string;
    cost?: number;
    cost_per_night?: number;
    total_cost?: number;
    description?: string;
    comfort_level?: string;
    duration?: string;
    notes?: string;
    amenities?: string[];
  }>;
  explanation: string;
}

interface FinancialSummary {
  total_budget: number;
  total_estimated_cost: number;
  remaining_budget: number;
  contingency_included: boolean;
  contingency_amount: number;
  contingency_percentage: number;
}

interface TripMetadata {
  destination_name: string;
  destination_state: string;
  trip_duration_days: number;
  traveler_count: number;
  comfort_score: number;
  travel_type: string;
  starting_city?: string;
  destination_category: string;
}

interface ExplainabilityData {
  trip_id: number;
  trip_metadata: TripMetadata;
  financial_summary: FinancialSummary;
  cost_explanations: CostExplanation[];
  ai_summary?: string;
  recommendations?: Array<{
    action: string;
    savings_potential?: number;
    trade_offs?: string[];
    implementation?: string;
  }>;
  has_alternative_prices: boolean;
  missing_decision_data: string[];
  data_source: string;
}

interface ExplainabilityReportProps {
  data: ExplainabilityData;
  isLoading?: boolean;
  error?: string;
}

export const ExplainabilityReport: React.FC<ExplainabilityReportProps> = ({
  data,
  isLoading = false,
  error
}) => {
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="bg-paper-50 dark:bg-paper-900/30 border border-paper-200 dark:border-paper-700 rounded-2xl p-8 animate-pulse">
        <div className="space-y-4">
          <div className="h-6 bg-paper-200 dark:bg-paper-700 rounded w-1/3"></div>
          <div className="h-4 bg-paper-200 dark:bg-paper-700 rounded w-full"></div>
          <div className="h-4 bg-paper-200 dark:bg-paper-700 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/30 rounded-2xl p-6">
        <div className="flex gap-3">
          <AlertCircle className="text-rose-600 dark:text-rose-400 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <h3 className="font-bold text-rose-900 dark:text-rose-200 mb-1">Error</h3>
            <p className="text-sm text-rose-700 dark:text-rose-300">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  const { trip_metadata, financial_summary, cost_explanations, ai_summary, recommendations, data_source } = data;

  return (
    <div className="space-y-6">
      {/* Header with Trip Summary */}
      <div className="bg-gradient-to-r from-marigold-50 to-petrol-50 dark:from-marigold-950/20 dark:to-petrol-950/20 border border-marigold-200 dark:border-marigold-900/30 rounded-2xl p-6">
        <h2 className="text-2xl font-extrabold text-paper-900 dark:text-white mb-2">
          Budget Analysis: {trip_metadata.destination_name}
        </h2>
        <p className="text-sm text-paper-600 dark:text-paper-400 mb-4">
          {trip_metadata.trip_duration_days} days • {trip_metadata.traveler_count} traveler{trip_metadata.traveler_count !== 1 ? 's' : ''} • {trip_metadata.travel_type} trip
        </p>

        {/* Financial Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-paper-800 rounded-xl p-4 border border-paper-100 dark:border-paper-700">
            <p className="text-xs text-paper-500 dark:text-paper-400 font-bold uppercase mb-1">Total Budget</p>
            <p className="text-2xl font-extrabold text-paper-900 dark:text-white">
              ₹{financial_summary.total_budget.toLocaleString('en-IN')}
            </p>
          </div>

          <div className="bg-white dark:bg-paper-800 rounded-xl p-4 border border-paper-100 dark:border-paper-700">
            <p className="text-xs text-paper-500 dark:text-paper-400 font-bold uppercase mb-1">Estimated Cost</p>
            <p className="text-2xl font-extrabold text-paper-900 dark:text-white">
              ₹{financial_summary.total_estimated_cost.toLocaleString('en-IN')}
            </p>
          </div>

          <div className={`rounded-xl p-4 border ${financial_summary.remaining_budget >= 0
              ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/30'
              : 'bg-rose-50 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900/30'
            }`}>
            <p className="text-xs text-paper-500 dark:text-paper-400 font-bold uppercase mb-1">Remaining</p>
            <p className={`text-2xl font-extrabold ${financial_summary.remaining_budget >= 0
                ? 'text-emerald-700 dark:text-emerald-400'
                : 'text-rose-700 dark:text-rose-400'
              }`}>
              ₹{Math.abs(financial_summary.remaining_budget).toLocaleString('en-IN')}
            </p>
          </div>
        </div>
      </div>

      {/* AI Summary if available */}
      {ai_summary && (
        <div className="bg-marigold-50/50 dark:bg-marigold-950/10 border border-marigold-100 dark:border-marigold-900/20 rounded-2xl p-6">
          <h3 className="font-bold text-paper-900 dark:text-white mb-3 flex items-center gap-2">
            <HelpCircle size={18} className="text-marigold-600" />
            Summary
          </h3>
          <p className="text-sm text-paper-700 dark:text-paper-300 leading-relaxed">{ai_summary}</p>
        </div>
      )}

      {/* Budget Breakdown by Category */}
      <div className="space-y-3">
        <h3 className="font-bold text-paper-900 dark:text-white flex items-center gap-2">
          <TrendingUp size={18} className="text-marigold-600" />
          Budget Breakdown
        </h3>

        {/* Visual breakdown bar */}
        <div className="flex gap-1 h-3 rounded-full overflow-hidden bg-paper-100 dark:bg-paper-800">
          {cost_explanations.map((exp, idx) => (
            <div
              key={idx}
              style={{
                width: `${exp.allocation_percentage}%`,
                backgroundColor: [
                  '#F59E0B', // Accommodation - amber
                  '#3B82F6', // Transport - blue
                  '#10B981', // Food - emerald
                  '#F97316', // Activities - orange
                  '#8B5CF6', // Local transport - violet
                  '#EF4444', // Taxes - red
                  '#6B7280'  // Contingency - gray
                ][idx % 7]
              }}
              className="rounded-full transition-opacity hover:opacity-80"
              title={`${exp.category}: ${exp.allocation_percentage.toFixed(1)}%`}
            />
          ))}
        </div>

        {/* Legend */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {cost_explanations.slice(0, 6).map((exp, idx) => (
            <div key={idx} className="flex items-center gap-2 text-xs">
              <div
                className="w-3 h-3 rounded-full"
                style={{
                  backgroundColor: [
                    '#F59E0B',
                    '#3B82F6',
                    '#10B981',
                    '#F97316',
                    '#8B5CF6',
                    '#EF4444'
                  ][idx]
                }}
              />
              <span className="text-paper-600 dark:text-paper-400">
                {exp.category} ({exp.allocation_percentage.toFixed(1)}%)
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Detailed Cost Explanations */}
      <div className="space-y-3">
        <h3 className="font-bold text-paper-900 dark:text-white">Category Details</h3>

        {cost_explanations.map((exp, idx) => (
          <div
            key={idx}
            className="bg-paper-50 dark:bg-paper-900/30 border border-paper-200 dark:border-paper-700 rounded-xl overflow-hidden"
          >
            {/* Category Header */}
            <button
              onClick={() => setExpandedCategory(expandedCategory === exp.category ? null : exp.category)}
              className="w-full p-4 text-left hover:bg-paper-100 dark:hover:bg-paper-800 transition-colors flex items-start justify-between gap-4"
            >
              <div className="flex-1">
                <h4 className="font-bold text-paper-900 dark:text-white mb-1 flex items-center gap-2">
                  {exp.category}
                  {exp.allocation_percentage > 30 && (
                    <span className="text-[10px] bg-orange-100 dark:bg-orange-950/40 text-orange-700 dark:text-orange-400 px-2 py-0.5 rounded">
                      {exp.allocation_percentage.toFixed(0)}% of budget
                    </span>
                  )}
                </h4>
                <p className="text-sm text-marigold-600 dark:text-marigold-400 font-extrabold">
                  ₹{exp.selected_cost.toLocaleString('en-IN')}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-paper-500 dark:text-paper-400">
                  {exp.selected_option}
                </span>
                <ChevronDown
                  size={18}
                  className={`text-paper-500 transition-transform ${
                    expandedCategory === exp.category ? 'rotate-180' : ''
                  }`}
                />
              </div>
            </button>

            {/* Expanded Details */}
            {expandedCategory === exp.category && (
              <div className="border-t border-paper-200 dark:border-paper-700 p-4 space-y-4 bg-paper-50 dark:bg-paper-900/20">
                {/* Explanation */}
                <div>
                  <p className="text-xs text-paper-500 dark:text-paper-400 font-bold uppercase mb-2">Why This Choice?</p>
                  <p className="text-sm text-paper-700 dark:text-paper-300 leading-relaxed">{exp.explanation}</p>
                </div>

                {/* Decision Factors */}
                {exp.decision_factors.length > 0 && (
                  <div>
                    <p className="text-xs text-paper-500 dark:text-paper-400 font-bold uppercase mb-2">Decision Factors</p>
                    <ul className="space-y-1">
                      {exp.decision_factors.map((factor, i) => (
                        <li key={i} className="text-sm text-paper-600 dark:text-paper-400 flex items-start gap-2">
                          <Check size={14} className="text-emerald-600 dark:text-emerald-400 mt-0.5 flex-shrink-0" />
                          {factor}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Alternatives */}
                {exp.alternatives && exp.alternatives.length > 0 && (
                  <div>
                    <p className="text-xs text-paper-500 dark:text-paper-400 font-bold uppercase mb-2">Alternatives</p>
                    <div className="space-y-2">
                      {exp.alternatives.map((alt, i) => (
                        <div key={i} className="bg-white dark:bg-paper-800 rounded-lg p-3 border border-paper-100 dark:border-paper-700">
                          <div className="flex items-start justify-between mb-1">
                            <p className="font-semibold text-paper-900 dark:text-white text-sm">
                              {alt.mode || alt.tier}
                            </p>
                            {alt.cost && (
                              <p className="text-sm font-extrabold text-marigold-600 dark:text-marigold-400">
                                ₹{alt.cost.toLocaleString('en-IN')}
                              </p>
                            )}
                            {alt.total_cost && (
                              <p className="text-sm font-extrabold text-marigold-600 dark:text-marigold-400">
                                ₹{alt.total_cost.toLocaleString('en-IN')}
                              </p>
                            )}
                          </div>
                          <p className="text-xs text-paper-600 dark:text-paper-400 mb-1">
                            {alt.description || alt.comfort_level}
                          </p>
                          {alt.notes && (
                            <p className="text-xs text-paper-500 dark:text-paper-500 italic">{alt.notes}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/30 rounded-2xl p-6">
          <h3 className="font-bold text-blue-900 dark:text-blue-200 mb-4 flex items-center gap-2">
            <TrendingUp size={18} />
            Recommendations
          </h3>

          <div className="space-y-3">
            {recommendations.map((rec, idx) => (
              <div key={idx} className="bg-white dark:bg-paper-800 rounded-lg p-4 border border-blue-100 dark:border-blue-900/30">
                <p className="font-semibold text-paper-900 dark:text-white mb-2">{rec.action}</p>
                {rec.savings_potential && (
                  <p className="text-sm text-emerald-600 dark:text-emerald-400 font-bold mb-2">
                    💰 Potential savings: ₹{rec.savings_potential.toLocaleString('en-IN')}
                  </p>
                )}
                {rec.trade_offs && (
                  <div className="mb-2">
                    <p className="text-xs text-paper-600 dark:text-paper-400 font-bold mb-1">Trade-offs:</p>
                    <ul className="space-y-1">
                      {rec.trade_offs.map((tradeoff, i) => (
                        <li key={i} className="text-sm text-paper-600 dark:text-paper-400">• {tradeoff}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {rec.implementation && (
                  <p className="text-xs text-paper-500 dark:text-paper-400 italic">{rec.implementation}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Source Footer */}
      <div className="text-xs text-paper-500 dark:text-paper-400 text-center p-4 border-t border-paper-200 dark:border-paper-700">
        <p>
          Analysis based on {data_source === 'calculated' ? 'calculated' : 'estimated'} decision data
          {!data.has_alternative_prices && ' (limited alternatives available)'}
        </p>
        {data.missing_decision_data.length > 0 && (
          <p className="mt-1 text-orange-600 dark:text-orange-400">
            ⚠️ Missing data: {data.missing_decision_data.join(', ')}
          </p>
        )}
      </div>
    </div>
  );
};
