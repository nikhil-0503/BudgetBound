import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { 
  GitCompare, 
  MapPin, 
  Wallet, 
  Calendar, 
  Users, 
  Sliders, 
  Star, 
  Flame, 
  Sparkles, 
  HelpCircle,
  Loader,
  TrendingDown,
  Activity,
  Heart,
  Home,
  Check,
  AlertTriangle
} from 'lucide-react';

interface DestinationDropdown {
  id: number;
  name: string;
  state: string;
  category: string;
}

// Large sentinel budget used only for comparison API calls.
// We send this so budget enforcement never blocks a comparison slot.
// The actual user budget is displayed separately as a reference column.
const COMPARE_BUDGET_SENTINEL = 9_999_999;

export const CompareDestinations: React.FC = () => {
  const navigate = useNavigate();

  // Catalog state
  const [destinations, setDestinations] = useState<DestinationDropdown[]>([]);
  const [loadingCatalog, setLoadingCatalog] = useState(true);

  // Preference Context state (used as simulation parameters, not budget enforcement)
  const [startingCity, setStartingCity] = useState('Bangalore');
  const [budget, setBudget] = useState('20000');
  const [days, setDays] = useState(4);
  const [travelersCount, setTravelersCount] = useState(1);
  const [comfortScore, setComfortScore] = useState(50);
  const [travelType, setTravelType] = useState('Nature');

  // Selected Comparison Slots
  const [selectedIds, setSelectedIds] = useState<(number | '')[]>(['', '', '']);
  const [plans, setPlans] = useState<(any | null)[]>([null, null, null]);
  // Per-slot loading and error state
  const [loadingSlots, setLoadingSlots] = useState<boolean[]>([false, false, false]);
  const [planErrors, setPlanErrors] = useState<(string | null)[]>([null, null, null]);

  // Fetch full catalog
  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        setLoadingCatalog(true);
        const response = await api.get('/api/destinations/', { params: { limit: 200 } });
        setDestinations(response.data.destinations || []);
      } catch (err) {
        console.error('Failed to fetch destinations list:', err);
      } finally {
        setLoadingCatalog(false);
      }
    };
    fetchCatalog();
  }, []);

  /**
   * Fetch a trip plan for a single comparison slot.
   *
   * Key design decisions:
   * - We send COMPARE_BUDGET_SENTINEL as the budget so the backend never rejects
   *   the request due to budget enforcement. The compare table shows actual cost
   *   vs the user's reference budget for visual comparison.
   * - All user preferences (city, days, travelers, comfort, travel type) are sent
   *   so costs are calculated under the same scenario for all slots.
   */
  const fetchPlanForSlot = async (slotIdx: number, destId: number): Promise<void> => {
    // Mark this slot as loading, clear prior error
    setLoadingSlots(prev => { const n = [...prev]; n[slotIdx] = true; return n; });
    setPlanErrors(prev => { const n = [...prev]; n[slotIdx] = null; return n; });

    try {
      const response = await api.post('/api/trips/plan', {
        starting_city: startingCity || 'Bangalore',
        budget: COMPARE_BUDGET_SENTINEL,   // bypass budget enforcement
        days: Number(days) || 4,
        travel_type: travelType,
        travelers_count: Number(travelersCount) || 1,
        comfort_score: Number(comfortScore) || 50,
        destination_id: destId
      });

      setPlans(prev => {
        const next = [...prev];
        next[slotIdx] = response.data;
        return next;
      });
    } catch (err: any) {
      console.error(`Failed to calculate plan for slot ${slotIdx}:`, err);
      const detail = err.response?.data?.detail || 'Failed to load plan for this destination.';
      setPlanErrors(prev => { const n = [...prev]; n[slotIdx] = detail; return n; });
      // Clear the plan for this slot so we don't show stale data
      setPlans(prev => { const n = [...prev]; n[slotIdx] = null; return n; });
    } finally {
      setLoadingSlots(prev => { const n = [...prev]; n[slotIdx] = false; return n; });
    }
  };

  const handleSelectChange = (slotIdx: number, val: string) => {
    const nextIds = [...selectedIds];
    nextIds[slotIdx] = val === '' ? '' : Number(val);
    setSelectedIds(nextIds);

    if (val === '') {
      setPlans(prev => { const n = [...prev]; n[slotIdx] = null; return n; });
      setPlanErrors(prev => { const n = [...prev]; n[slotIdx] = null; return n; });
    } else {
      fetchPlanForSlot(slotIdx, Number(val));
    }
  };

  /**
   * Re-simulate all loaded slots concurrently when the user changes
   * preferences and clicks "Re-Simulate Comparison".
   */
  const reSimulateAll = () => {
    const promises: Promise<void>[] = [];
    for (let i = 0; i < 3; i++) {
      const destId = selectedIds[i];
      if (typeof destId === 'number') {
        promises.push(fetchPlanForSlot(i, destId));
      }
    }
    // Fire all concurrently "” do not await sequentially
    Promise.all(promises).catch(err => console.error('Re-simulate error:', err));
  };

  // Compute highlights across loaded plans
  const activePlans = plans.filter((p): p is any => p !== null);

  const getCheapestIdx = () => {
    if (activePlans.length < 2) return null;
    let minCost = Infinity;
    let minIdx = -1;
    plans.forEach((p, idx) => {
      if (p && p.costs.total_estimated_cost < minCost) {
        minCost = p.costs.total_estimated_cost;
        minIdx = idx;
      }
    });
    return minIdx;
  };

  const getBestValueIdx = () => {
    if (activePlans.length < 2) return null;
    let maxValue = -1;
    let maxIdx = -1;
    plans.forEach((p, idx) => {
      if (p && p.value_score > maxValue) {
        maxValue = p.value_score;
        maxIdx = idx;
      }
    });
    return maxIdx;
  };

  const getBestComfortIdx = () => {
    if (activePlans.length < 2) return null;
    let maxComfort = -1;
    let maxIdx = -1;
    plans.forEach((p, idx) => {
      const comfort = p?.destination?.comfort_level || 0;
      if (p && comfort > maxComfort) {
        maxComfort = comfort;
        maxIdx = idx;
      }
    });
    return maxIdx;
  };

  const getHighestRatedIdx = () => {
    if (activePlans.length < 2) return null;
    let maxRating = -1;
    let maxIdx = -1;
    plans.forEach((p, idx) => {
      const r = p?.destination?.rating || 0;
      if (p && r > maxRating) {
        maxRating = r;
        maxIdx = idx;
      }
    });
    return maxIdx;
  };

  const cheapestIdx = getCheapestIdx();
  const bestValueIdx = getBestValueIdx();
  const bestComfortIdx = getBestComfortIdx();
  const highestRatedIdx = getHighestRatedIdx();

  const handleChoose = (plan: any) => {
    sessionStorage.setItem('prefilled_planner', JSON.stringify({
      startingCity,
      budget: Number(budget),
      days,
      travelType,
      travelersCount,
      comfortScore,
      destinationId: plan.destination.id,
      destName: plan.destination.name,
      flowMode: 'plan'
    }));
    navigate('/planner');
  };

  // Helper: is the cost over the user's reference budget?
  const isOverBudget = (plan: any) =>
    plan && plan.costs.total_estimated_cost > Number(budget || 20000);

  if (loadingCatalog) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-paper-500 gap-4">
        <Loader className="h-10 w-10 text-marigold-500 animate-spin" />
        <span className="text-sm font-semibold">Loading destination directory...</span>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="space-y-8 relative text-paper-900 dark:text-paper-100"
    >
      
      {/* Header */}
      <div>
        <span className="text-xs font-bold text-marigold-600 dark:text-marigold-400 uppercase tracking-widest">Analytics Studio</span>
        <h1 className="text-3xl font-extrabold text-paper-900 dark:text-white mt-1">Compare Destinations</h1>
        <p className="text-sm text-paper-500 dark:text-paper-400">
          Analyze and cross-reference multiple travel locations side-by-side. Costs are calculated live from the database using your simulation preferences.
        </p>
      </div>

      {/* Preferences context editor */}
      <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-6 rounded-2xl shadow-sm flex flex-col gap-6">
        <h3 className="font-extrabold text-sm uppercase tracking-wider text-paper-800 dark:text-white flex items-center gap-1.5">
          <Sliders className="text-marigold-500" size={16} />
          Simulation Preferences
        </h3>
        <p className="text-xs text-paper-400 dark:text-paper-500 -mt-4">
          Set your trip scenario below. All three destination plans are recalculated using the same parameters so costs are directly comparable.
          The <span className="font-bold text-paper-600 dark:text-paper-300">Target Budget</span> is your reference "” columns that exceed it are flagged in the table.
        </p>
        
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-xs font-bold">
          <div>
            <label className="block text-paper-400 mb-1">Starting City</label>
            <input
              type="text"
              value={startingCity}
              onChange={(e) => setStartingCity(e.target.value)}
              className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2 bg-paper-50 dark:bg-paper-900 focus:outline-none focus:border-marigold-500"
            />
          </div>

          <div>
            <label className="block text-paper-400 mb-1">Reference Budget (INR)</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2 bg-paper-50 dark:bg-paper-900 focus:outline-none focus:border-marigold-500"
            />
          </div>

          <div>
            <label className="block text-paper-400 mb-1">Duration (Days)</label>
            <input
              type="number"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2 bg-paper-50 dark:bg-paper-900 focus:outline-none focus:border-marigold-500"
            />
          </div>

          <div>
            <label className="block text-paper-400 mb-1">Travelers Count</label>
            <input
              type="number"
              value={travelersCount}
              onChange={(e) => setTravelersCount(Number(e.target.value))}
              className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2 bg-paper-50 dark:bg-paper-900 focus:outline-none focus:border-marigold-500"
            />
          </div>

          <div>
            <label className="block text-paper-400 mb-1">Comfort (0-100)</label>
            <input
              type="number"
              value={comfortScore}
              onChange={(e) => setComfortScore(Number(e.target.value))}
              className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2 bg-paper-50 dark:bg-paper-900 focus:outline-none focus:border-marigold-500"
            />
          </div>

          <div>
            <label className="block text-paper-400 mb-1">Travel Style</label>
            <select
              value={travelType}
              onChange={(e) => setTravelType(e.target.value)}
              className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2 bg-paper-50 dark:bg-paper-900 focus:outline-none focus:border-marigold-500"
            >
              {['Nature', 'Adventure', 'Family', 'Religious', 'Beach', 'City Exploration', 'Romantic', 'Solo'].map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={reSimulateAll}
          disabled={activePlans.length === 0}
          className="self-end inline-flex items-center gap-1.5 bg-marigold-600 hover:bg-marigold-500 disabled:opacity-40 text-white font-bold px-4 py-2 rounded-xl text-xs transition-all shadow-md shadow-marigold-600/10"
        >
          Re-Simulate Comparison
        </button>
      </div>

      {/* Compare Table Matrix */}
      <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-xs min-w-[700px]">
            <thead>
              <tr className="border-b border-paper-200 dark:border-paper-700 bg-paper-50/50 dark:bg-paper-900/10">
                <th className="p-4 font-bold uppercase text-[10px] text-paper-400 w-[220px]">Comparison Factors</th>
                
                {[0, 1, 2].map((slotIdx) => (
                  <th key={slotIdx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 w-[250px] align-top">
                    <div className="flex flex-col gap-2">
                      <select
                        value={selectedIds[slotIdx]}
                        onChange={(e) => handleSelectChange(slotIdx, e.target.value)}
                        className="w-full bg-paper-100 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl p-2 text-xs font-bold focus:outline-none focus:border-marigold-500"
                      >
                        <option value="">"” Choose Destination "”</option>
                        {destinations.map(d => (
                          <option key={d.id} value={d.id}>{d.name} ({d.state})</option>
                        ))}
                      </select>

                      {/* Per-slot loading spinner */}
                      {loadingSlots[slotIdx] && (
                        <div className="flex items-center gap-2 text-[10px] text-marigold-500 font-semibold">
                          <Loader size={12} className="animate-spin" />
                          <span>Simulating costs...</span>
                        </div>
                      )}

                      {/* Per-slot error message */}
                      {planErrors[slotIdx] && !loadingSlots[slotIdx] && (
                        <div className="flex items-start gap-1.5 text-[10px] text-rose-600 dark:text-rose-400 font-semibold bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/30 rounded-lg p-2">
                          <AlertTriangle size={11} className="shrink-0 mt-0.5" />
                          <span>{planErrors[slotIdx]}</span>
                        </div>
                      )}

                      {/* Over-budget flag */}
                      {plans[slotIdx] && isOverBudget(plans[slotIdx]) && (
                        <div className="flex items-center gap-1 text-[9px] text-amber-700 dark:text-amber-400 font-bold bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/30 rounded-lg px-2 py-1">
                          <AlertTriangle size={10} />
                          Exceeds reference budget
                        </div>
                      )}

                      {/* Highlight badges */}
                      {plans[slotIdx] && (
                        <div className="flex flex-wrap gap-1.5">
                          {cheapestIdx === slotIdx && (
                            <span className="bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase">
                              Cheapest
                            </span>
                          )}
                          {bestValueIdx === slotIdx && (
                            <span className="bg-marigold-100 text-marigold-800 dark:bg-marigold-950/40 dark:text-marigold-400 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase">
                              Best Value
                            </span>
                          )}
                          {bestComfortIdx === slotIdx && (
                            <span className="bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase">
                              Best Comfort
                            </span>
                          )}
                          {highestRatedIdx === slotIdx && (
                            <span className="bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-400 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase">
                              Highest Rated
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            
            <tbody className="divide-y divide-paper-100 dark:divide-paper-700/60 font-semibold text-paper-600 dark:text-paper-300">
              
              {/* Row: Destination Name */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 font-extrabold uppercase text-[10px] text-paper-400">Destination</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 text-paper-900 dark:text-white font-extrabold text-sm">
                    {plans[idx]?.destination.name || (loadingSlots[idx] ? '...' : '"”')}
                  </td>
                ))}
              </tr>

              {/* Row: State */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5">State</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 text-paper-500 dark:text-paper-400 font-medium">
                    {plans[idx]?.destination.state || '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Category */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5">Category</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 text-xs font-bold uppercase">
                    {plans[idx]?.destination.category || '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Budget Tier */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5">Budget Tier</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-bold">
                    {plans[idx]?.destination.budget_tier || '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Estimated Total Cost "” shows actual cost vs reference budget */}
              <tr className="bg-paper-50/30 dark:bg-paper-900/10">
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 font-extrabold text-paper-700 dark:text-paper-200">
                  Estimated Total Cost
                  <span className="block text-[9px] font-bold text-paper-400 mt-0.5 normal-case">
                    Reference budget: ₹{Number(budget || 20000).toLocaleString()}
                  </span>
                </td>
                {[0, 1, 2].map(idx => {
                  const p = plans[idx];
                  const over = p && isOverBudget(p);
                  return (
                    <td key={idx} className={`p-4 border-l border-paper-100 dark:border-paper-700/60 font-extrabold text-sm ${over ? 'text-rose-600 dark:text-rose-400' : 'text-paper-900 dark:text-white'}`}>
                      {p ? (
                        <div className="flex flex-col gap-0.5">
                          <span>₹{p.costs.total_estimated_cost.toLocaleString()}</span>
                          {over && (
                            <span className="text-[9px] font-bold text-rose-500">
                              +₹{(p.costs.total_estimated_cost - Number(budget || 20000)).toLocaleString()} over budget
                            </span>
                          )}
                          {!over && (
                            <span className="text-[9px] font-bold text-emerald-500">
                              ₹{(Number(budget || 20000) - p.costs.total_estimated_cost).toLocaleString()} under budget
                            </span>
                          )}
                        </div>
                      ) : '"”'}
                    </td>
                  );
                })}
              </tr>

              {/* Row: Transport Mode & Cost */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">â†³ Transport cost</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx] ? `₹${plans[idx].costs.transport_cost.toLocaleString()} (${plans[idx].costs.transport_mode})` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Hotel Cost */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">â†³ Hotel cost</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx] ? `₹${plans[idx].costs.hotel_cost.toLocaleString()} (${plans[idx].costs.hotel_tier})` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Food Cost */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">â†³ Food cost</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx] ? `₹${plans[idx].costs.food_cost.toLocaleString()}` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Activities Cost */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">â†³ Activities cost</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx] ? `₹${plans[idx].costs.activities_cost.toLocaleString()}` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Local Transport + Taxes */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">â†³ Local transport + taxes</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx] ? `₹${(plans[idx].costs.local_transport_cost + plans[idx].costs.taxes_fees_cost).toLocaleString()}` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Recommended Days */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5">Recommended Duration</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-bold">
                    {plans[idx] ? `${plans[idx].destination.recommended_duration} Days` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Rating */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5">User Rating</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 text-paper-900 dark:text-white font-extrabold">
                    {plans[idx] ? (
                      <div className="flex items-center gap-1 text-amber-500">
                        <Star size={14} fill="currentColor" />
                        <span>{plans[idx].destination.rating} / 5</span>
                      </div>
                    ) : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Best Season */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5">Best Season</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400 truncate">
                    {plans[idx]?.destination.best_season || '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Comfort Level */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5">Comfort Standard</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 text-paper-900 dark:text-white font-bold">
                    {plans[idx] ? `${plans[idx].destination.comfort_level} / 100` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Weather Intelligence */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5">Weather & Season</td>
                {[0, 1, 2].map(idx => {
                  const w = plans[idx]?.destination.weather_intelligence;
                  return (
                    <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 text-xs">
                      {w ? (
                        <div className="flex flex-col gap-1">
                          <span className="font-bold text-paper-800 dark:text-white">{w.current_season} Season</span>
                          <span className={`inline-block text-[9px] font-extrabold px-2 py-0.5 rounded-full w-max ${
                            w.season_rating === 'Excellent' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400' :
                            w.season_rating === 'Good' ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-400' :
                            w.season_rating === 'Fair' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400' :
                            'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400'
                          }`}>{w.season_rating}</span>
                        </div>
                      ) : '"”'}
                    </td>
                  );
                })}
              </tr>

              {/* Row: Temp & Rain */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5">Temp & Rain Prob</td>
                {[0, 1, 2].map(idx => {
                  const w = plans[idx]?.destination.weather_intelligence;
                  return (
                    <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 text-xs font-semibold text-paper-500 dark:text-paper-400">
                      {w ? `${w.temperature_range} (Rain: ${w.rain_probability})` : '"”'}
                    </td>
                  );
                })}
              </tr>

              {/* Row: CO2 Carbon Footprint */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5">Carbon Footprint</td>
                {[0, 1, 2].map(idx => {
                  const c = plans[idx]?.carbon_footprint;
                  return (
                    <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 text-xs">
                      {c ? (
                        <div className="flex flex-col gap-1">
                          <span className="font-bold text-paper-800 dark:text-white">{c.co2_emissions} kg ({c.transport_mode})</span>
                          <span className={`inline-block text-[9px] font-extrabold px-2 py-0.5 rounded-full w-max ${
                            c.carbon_rating === 'Eco Friendly' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400' :
                            c.carbon_rating === 'Moderate' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400' :
                            'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400'
                          }`}>{c.carbon_rating}</span>
                        </div>
                      ) : '"”'}
                    </td>
                  );
                })}
              </tr>

              {/* Row: Recommendation Score */}
              <tr className="bg-paper-50/30 dark:bg-paper-900/10">
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 text-marigold-700 dark:text-marigold-400 font-bold">Overall Recommendation Score</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-extrabold text-marigold-600 dark:text-marigold-400 text-sm">
                    {plans[idx] ? `${plans[idx].value_score.toFixed(1)}%` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Budget Compatibility Score */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">â†³ Budget Compatibility</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx]?.breakdown ? `${plans[idx].breakdown.budget_compatibility}%` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Type Match Score */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">â†³ Travel Type Match</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx]?.breakdown ? `${plans[idx].breakdown.trip_type_match}%` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Comfort Match Score */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">â†³ Comfort Match</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx]?.breakdown ? `${plans[idx].breakdown.comfort_match}%` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Duration Suitability */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">â†³ Duration Suitability</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx]?.breakdown ? `${plans[idx].breakdown.duration_suitability}%` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Category Scores from DB */}
              {[
                { key: 'nature_score', label: 'Nature Match' },
                { key: 'adventure_score', label: 'Adventure Match' },
                { key: 'family_score', label: 'Family Suitability' },
                { key: 'romantic_score', label: 'Romantic Score' },
                { key: 'religious_score', label: 'Religious Score' },
                { key: 'beach_score', label: 'Beach Score' },
                { key: 'solo_score', label: 'Solo Score' },
              ].map((row) => (
                <tr key={row.key}>
                  <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">{row.label}</td>
                  {[0, 1, 2].map(idx => (
                    <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                      {plans[idx] ? `${plans[idx].destination[row.key] ?? 0}%` : '"”'}
                    </td>
                  ))}
                </tr>
              ))}

              {/* Row: Action Button */}
              <tr className="bg-paper-50/10 dark:bg-paper-900/5">
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 uppercase font-bold text-[9px] text-paper-400">Lock Choice</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60">
                    {plans[idx] ? (
                      <button
                        onClick={() => handleChoose(plans[idx])}
                        className="inline-flex items-center gap-1 bg-marigold-600 hover:bg-marigold-500 text-white font-bold px-3.5 py-2 rounded-xl text-xs transition-all shadow-md shadow-marigold-600/10 w-full justify-center"
                      >
                        <Check size={14} />
                        Choose Destination
                      </button>
                    ) : (
                      <span className="text-paper-400 font-bold block text-center">"”</span>
                    )}
                  </td>
                ))}
              </tr>

            </tbody>
          </table>
        </div>
      </div>

    </motion.div>
  );
};



