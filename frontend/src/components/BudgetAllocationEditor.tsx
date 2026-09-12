import React, { useState, useEffect } from 'react';
import { Sliders, RefreshCw, Save, Check } from 'lucide-react';

interface AllocationData {
  transport_cost: number;
  hotel_cost: number;
  food_cost: number;
  activities_cost: number;
  emergency_reserve: number;
  local_transport_cost?: number;
  taxes_fees_cost?: number;
}

interface BudgetAllocationEditorProps {
  budget: number;
  initialAllocations: AllocationData;
  onSave: (updatedAllocations: AllocationData, isCustom: boolean) => void;
  onReset?: () => void;
  isSaving?: boolean;
  className?: string;
}

export const BudgetAllocationEditor: React.FC<BudgetAllocationEditorProps> = ({
  budget,
  initialAllocations,
  onSave,
  onReset,
  isSaving = false,
  className = '',
}) => {
  // 5 main categories
  const [transportPercent, setTransportPercent] = useState(0);
  const [accommodationPercent, setAccommodationPercent] = useState(0);
  const [foodPercent, setFoodPercent] = useState(0);
  const [activitiesPercent, setActivitiesPercent] = useState(0);
  const [emergencyPercent, setEmergencyPercent] = useState(0);

  const [isCustomMode, setIsCustomMode] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Grouped recommended values helper
  const getGroupedRecommended = () => {
    const t = initialAllocations.transport_cost + (initialAllocations.local_transport_cost || 0);
    const a = initialAllocations.hotel_cost;
    const f = initialAllocations.food_cost;
    const ac = initialAllocations.activities_cost;
    const e = initialAllocations.emergency_reserve + (initialAllocations.taxes_fees_cost || 0);
    const sum = t + a + f + ac + e;
    return { t, a, f, ac, e, sum };
  };

  const syncSlidersWithProps = () => {
    const { t, a, f, ac, e, sum } = getGroupedRecommended();
    
    // If it's a custom allocation or we want to normalize it to 100% of the budget
    const denominator = isCustomMode ? budget : sum;
    const safeDenominator = denominator || 1;

    setTransportPercent((t / safeDenominator) * 100);
    setAccommodationPercent((a / safeDenominator) * 100);
    setFoodPercent((f / safeDenominator) * 100);
    setActivitiesPercent((ac / safeDenominator) * 100);
    setEmergencyPercent((e / safeDenominator) * 100);
  };

  useEffect(() => {
    syncSlidersWithProps();
  }, [initialAllocations, isCustomMode, budget]);

  const getPercentagesMap = () => {
    return {
      transport: transportPercent,
      accommodation: accommodationPercent,
      food: foodPercent,
      activities: activitiesPercent,
      emergency: emergencyPercent,
    };
  };

  const handleSliderChange = (key: string, newValue: number) => {
    if (!isCustomMode) {
      // Switch to custom mode first, which normalizes recommended to 100% of the budget
      setIsCustomMode(true);
      return;
    }

    const percentages = getPercentagesMap();
    const oldValue = percentages[key as keyof typeof percentages];
    const diff = newValue - oldValue;

    const otherKeys = Object.keys(percentages).filter((k) => k !== key);
    const sumOthers = otherKeys.reduce(
      (sum, k) => sum + percentages[k as keyof typeof percentages],
      0
    );

    const updated = { ...percentages, [key]: newValue };

    if (sumOthers > 0) {
      otherKeys.forEach((k) => {
        const val = percentages[k as keyof typeof percentages];
        const delta = diff * (val / sumOthers);
        updated[k as keyof typeof percentages] = Math.max(0, val - delta);
      });
    } else {
      otherKeys.forEach((k) => {
        updated[k as keyof typeof percentages] = Math.max(
          0,
          (100 - newValue) / otherKeys.length
        );
      });
    }

    // Normalize to ensure total is exactly 100%
    const totalSum = Object.values(updated).reduce((sum, v) => sum + v, 0);
    if (Math.abs(totalSum - 100) > 0.01) {
      const error = 100 - totalSum;
      const adjustKey = otherKeys[0];
      updated[adjustKey as keyof typeof percentages] = Math.max(
        0,
        updated[adjustKey as keyof typeof percentages] + error
      );
    }

    setTransportPercent(updated.transport);
    setAccommodationPercent(updated.accommodation);
    setFoodPercent(updated.food);
    setActivitiesPercent(updated.activities);
    setEmergencyPercent(updated.emergency);
  };

  // Recalculated values for preview display
  const currentDenominator = isCustomMode ? budget : getGroupedRecommended().sum;
  const currentTotal = isCustomMode ? budget : getGroupedRecommended().sum;

  const previewTransport = (transportPercent / 100) * currentDenominator;
  const previewAccommodation = (accommodationPercent / 100) * currentDenominator;
  const previewFood = (foodPercent / 100) * currentDenominator;
  const previewActivities = (activitiesPercent / 100) * currentDenominator;
  const previewEmergency = (emergencyPercent / 100) * currentDenominator;

  const currentSumPercent =
    transportPercent +
    accommodationPercent +
    foodPercent +
    activitiesPercent +
    emergencyPercent;

  const handleSave = () => {
    const updated: AllocationData = {
      transport_cost: previewTransport,
      hotel_cost: previewAccommodation,
      food_cost: previewFood,
      activities_cost: previewActivities,
      emergency_reserve: previewEmergency,
      local_transport_cost: 0.0, // merged
      taxes_fees_cost: 0.0, // merged
    };
    onSave(updated, isCustomMode);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const handleResetClick = () => {
    setIsCustomMode(false);
    if (onReset) {
      onReset();
    }
  };

  const sliderClass = "w-full h-2 bg-paper-200 dark:bg-paper-700 rounded-lg appearance-none cursor-pointer accent-marigold-600 focus:outline-none disabled:opacity-50";

  return (
    <div className={`bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6 shadow-sm flex flex-col gap-6 ${className}`}>
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-paper-100 dark:border-paper-700 pb-4">
        <div>
          <h3 className="font-extrabold text-paper-900 dark:text-white flex items-center gap-1.5">
            <Sliders className="text-marigold-500" size={18} />
            Budget Allocation Editor
          </h3>
          <p className="text-xs text-paper-500 dark:text-paper-400 mt-0.5">
            Manually customize how your trip budget is distributed
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-paper-400 font-bold uppercase">
            Mode:
          </span>
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
            isCustomMode 
              ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400' 
              : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400'
          }`}>
            {isCustomMode ? 'Custom' : 'Recommended'}
          </span>
        </div>
      </div>

      {/* Sliders Container */}
      <div className="space-y-4">
        {[
          { key: 'transport', label: 'Transportation', value: transportPercent, cost: previewTransport, color: 'accent-blue-500' },
          { key: 'accommodation', label: 'Accommodation', value: accommodationPercent, cost: previewAccommodation, color: 'accent-marigold-500' },
          { key: 'food', label: 'Food & Dining', value: foodPercent, cost: previewFood, color: 'accent-emerald-500' },
          { key: 'activities', label: 'Activities', value: activitiesPercent, cost: previewActivities, color: 'accent-pink-500' },
          { key: 'emergency', label: 'Emergency Reserve', value: emergencyPercent, cost: previewEmergency, color: 'accent-amber-500' },
        ].map((slider) => (
          <div key={slider.key} className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-bold text-paper-600 dark:text-paper-300">
              <span>{slider.label}</span>
              <div className="flex items-center gap-2">
                <span className="text-paper-400 dark:text-paper-500">{slider.value.toFixed(1)}%</span>
                <span className="text-paper-800 dark:text-white">₹{slider.cost.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              </div>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="0.1"
              value={slider.value}
              onChange={(e) => handleSliderChange(slider.key, parseFloat(e.target.value))}
              onClick={() => {
                if (!isCustomMode) {
                  // Initialize custom mode by locking to budget and scaling
                  setIsCustomMode(true);
                }
              }}
              className={`${sliderClass} ${slider.color}`}
            />
          </div>
        ))}
      </div>

      {/* Total Verification */}
      <div className="flex justify-between items-center bg-paper-50 dark:bg-paper-900/50 p-3.5 rounded-xl border border-paper-100 dark:border-paper-800 text-xs font-bold">
        <span className="text-paper-500 dark:text-paper-400">Total Allocations</span>
        <div className="flex items-center gap-3">
          <span className={Math.abs(currentSumPercent - 100) < 0.1 ? "text-emerald-500" : "text-rose-500"}>
            {currentSumPercent.toFixed(0)}%
          </span>
          <span className="text-paper-900 dark:text-white">
            ₹{currentTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center gap-3">
        <button
          type="button"
          onClick={handleResetClick}
          disabled={!isCustomMode}
          className="inline-flex items-center gap-1 text-xs font-bold text-paper-500 hover:text-paper-800 dark:text-paper-400 dark:hover:text-white disabled:opacity-40 transition-colors"
        >
          <RefreshCw size={13} />
          Reset to Recommended
        </button>

        <button
          type="button"
          onClick={handleSave}
          disabled={isSaving || (isCustomMode && Math.abs(currentSumPercent - 100) > 0.5)}
          className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-marigold-600 to-petrol-600 hover:from-marigold-500 hover:to-petrol-500 text-white font-bold px-4 py-2.5 rounded-xl text-xs transition-all disabled:opacity-50"
        >
          {isSaving ? (
            'Saving...'
          ) : saveSuccess ? (
            <>
              <Check size={14} />
              Saved!
            </>
          ) : (
            <>
              <Save size={14} />
              Save Custom Allocation
            </>
          )}
        </button>
      </div>

    </div>
  );
};



