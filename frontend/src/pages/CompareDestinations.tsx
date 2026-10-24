<<<<<<< HEAD
import React, { useState, useEffect } from 'react';
=======
﻿import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
>>>>>>> 467e16fe48924e822e46cfc90613a82a82de7374
import { usePageTitle } from '../hooks/usePageTitle';
import api from '../services/api';
import { 
  GitCompare, 
  MapPin, 
  Wallet, 
  Loader,
  AlertCircle,
  Zap,
  Search,
  X,
  Star
} from 'lucide-react';

interface LivePlace {
  place_id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  rating: number | null;
  user_rating_count: number | null;
  data_source: string;
}

interface ComparisonSlot {
  place?: LivePlace;
  plan?: any;
  loading: boolean;
  error: string | null;
}

const COMPARE_BUDGET_SENTINEL = 9_999_999;

export const CompareDestinations: React.FC = () => {
  usePageTitle('Compare Destinations | BudgetBound');

  // Search and selection
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<LivePlace[]>([]);
  const [searching, setSearching] = useState(false);

  // User preferences
  const [startingCity, setStartingCity] = useState('Bangalore');
  const [budget, setBudget] = useState('100000');
  const [days, setDays] = useState(4);
  const [travelers, setTravelers] = useState(1);
  const [comfort, setComfort] = useState(50);
  const [travelType, setTravelType] = useState('Nature');

  // Comparison slots
  const [slots, setSlots] = useState<ComparisonSlot[]>([
    { loading: false, error: null },
    { loading: false, error: null },
    { loading: false, error: null }
  ]);

  // Debounced search
  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await api.get('/api/destinations-live/search', {
          params: { q: searchQuery, limit: 15 }
        });
        setSearchResults(res.data.results || []);
      } catch (err) {
        console.error('Search error:', err);
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Select a place for a slot
  const selectPlaceForSlot = async (slotIdx: number, place: LivePlace) => {
    setSlots(prev => {
      const newSlots = [...prev];
      newSlots[slotIdx] = { place, loading: true, error: null };
      return newSlots;
    });

    try {
      const res = await api.post('/api/trips/plan', {
        destination_name: place.name,
        latitude: place.latitude,
        longitude: place.longitude,
        starting_city: startingCity,
        budget: COMPARE_BUDGET_SENTINEL,
        days: Number(days),
        travel_type: travelType,
        travelers_count: Number(travelers),
        comfort_score: Number(comfort)
      });

      setSlots(prev => {
        const newSlots = [...prev];
        newSlots[slotIdx] = {
          place,
          plan: res.data,
          loading: false,
          error: null
        };
        return newSlots;
      });
    } catch (err: any) {
      setSlots(prev => {
        const newSlots = [...prev];
        newSlots[slotIdx] = {
          place,
          loading: false,
          error: err.response?.data?.detail || 'Failed to generate plan'
        };
        return newSlots;
      });
    }

    setSearchResults([]);
    setSearchQuery('');
  };

  // Clear a slot
  const clearSlot = (slotIdx: number) => {
    setSlots(prev => {
      const newSlots = [...prev];
      newSlots[slotIdx] = { loading: false, error: null };
      return newSlots;
    });
  };

  // Re-simulate all
  const reSimulate = () => {
    slots.forEach((slot, idx) => {
      if (slot.place) {
        selectPlaceForSlot(idx, slot.place);
      }
    });
  };

  const activePlans = slots.filter(s => s.plan).map(s => s.plan);

  const getCheapestIdx = () => {
    let minCost = Infinity;
    let minIdx = -1;
    slots.forEach((s, idx) => {
      if (s.plan?.costs?.total_estimated_cost < minCost) {
        minCost = s.plan.costs.total_estimated_cost;
        minIdx = idx;
      }
    });
    return minIdx >= 0 ? minIdx : null;
  };

  const getBestValueIdx = () => {
    let maxValue = -1;
    let maxIdx = -1;
    slots.forEach((s, idx) => {
      if (s.plan?.value_score > maxValue) {
        maxValue = s.plan.value_score;
        maxIdx = idx;
      }
    });
    return maxIdx >= 0 ? maxIdx : null;
  };

  const cheapestIdx = getCheapestIdx();
  const bestValueIdx = getBestValueIdx();

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <GitCompare className="text-marigold-600" size={28} />
          <span className="text-xs font-bold uppercase tracking-wide text-marigold-700">Live Comparison</span>
        </div>
        <h1 className="text-4xl font-bold text-paper-900 dark:text-white mb-2">
          Compare Live Destinations
        </h1>
        <p className="text-paper-600 dark:text-paper-400">
          Search for destinations using live Geoapify data, then compare costs and preferences side-by-side.
        </p>
      </div>

      {/* Search bar */}
      <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6 relative">
        <div className="relative">
          <Search className="absolute left-4 top-4 text-paper-400" size={18} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search for a destination (e.g., 'Goa', 'Munnar', 'Jaipur')..."
            className="w-full bg-white dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl pl-12 pr-4 py-3 text-sm focus:outline-none focus:border-marigold-500"
          />
        </div>

        {/* Search results dropdown */}
        {searchResults.length > 0 && (
          <div className="absolute z-50 top-20 left-6 right-6 bg-white dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl shadow-lg max-h-60 overflow-y-auto">
            {searchResults.map(place => (
              <button
                key={place.place_id}
                onClick={() => {
                  const emptySlot = slots.findIndex(s => !s.place);
                  if (emptySlot >= 0) {
                    selectPlaceForSlot(emptySlot, place);
                  }
                }}
                className="w-full text-left px-4 py-2 hover:bg-paper-50 dark:hover:bg-paper-800 border-b border-paper-100 dark:border-paper-700 last:border-b-0"
              >
                <div className="text-sm font-semibold text-paper-900 dark:text-white">{place.name}</div>
                <div className="text-xs text-paper-500">{place.address}</div>
                {place.rating && (
                  <div className="text-xs text-amber-600 mt-1">⭐ {place.rating.toFixed(1)}</div>
                )}
              </button>
            ))}
          </div>
        )}

        {searching && (
          <div className="absolute inset-y-0 right-4 flex items-center">
            <Loader className="animate-spin text-marigold-600" size={18} />
          </div>
        )}
      </div>

      {/* Preferences */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div>
          <label className="text-xs font-bold text-paper-600 block mb-2">Starting City</label>
          <input
            type="text"
            value={startingCity}
            onChange={(e) => setStartingCity(e.target.value)}
            className="w-full bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="text-xs font-bold text-paper-600 block mb-2">Budget (₹)</label>
          <input
            type="number"
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            className="w-full bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="text-xs font-bold text-paper-600 block mb-2">Days</label>
          <input
            type="number"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            min="1"
            max="30"
            className="w-full bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="text-xs font-bold text-paper-600 block mb-2">Travelers</label>
          <input
            type="number"
            value={travelers}
            onChange={(e) => setTravelers(Number(e.target.value))}
            min="1"
            className="w-full bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="text-xs font-bold text-paper-600 block mb-2">Comfort</label>
          <input
            type="range"
            value={comfort}
            onChange={(e) => setComfort(Number(e.target.value))}
            min="0"
            max="100"
            className="w-full"
          />
        </div>
        <div>
          <label className="text-xs font-bold text-paper-600 block mb-2">Travel Type</label>
          <select
            value={travelType}
            onChange={(e) => setTravelType(e.target.value)}
            className="w-full bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-lg px-3 py-2 text-sm"
          >
            <option>Nature</option>
            <option>Adventure</option>
            <option>Beach</option>
            <option>City Exploration</option>
          </select>
        </div>
      </div>

      {activePlans.length > 1 && (
        <button
          onClick={reSimulate}
          className="self-start px-6 py-2 bg-marigold-600 text-white rounded-lg hover:bg-marigold-700 text-sm font-semibold"
        >
          Re-Simulate Comparison
        </button>
      )}

      {/* Comparison Slots */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {slots.map((slot, idx) => (
          <div
            key={idx}
            className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6"
          >
            {!slot.place ? (
              <div className="text-center py-8 text-paper-500">
                <MapPin className="mx-auto mb-2 opacity-40" />
                <p className="text-sm">No destination selected</p>
              </div>
            ) : slot.loading ? (
              <div className="flex flex-col items-center py-8 gap-3">
                <Loader className="animate-spin text-marigold-600" />
                <p className="text-xs text-paper-500">Generating plan...</p>
              </div>
            ) : slot.error ? (
              <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-lg p-4">
                <div className="flex gap-2 mb-2">
                  <AlertCircle className="text-red-600 flex-shrink-0" size={16} />
                  <p className="text-xs text-red-700">{slot.error}</p>
                </div>
                <button
                  onClick={() => clearSlot(idx)}
                  className="text-xs text-red-600 hover:text-red-700 font-semibold"
                >
                  Clear selection
                </button>
              </div>
            ) : slot.plan ? (
              <div className="space-y-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold text-lg text-paper-900 dark:text-white">{slot.place.name}</h3>
                    <p className="text-xs text-paper-500">{slot.place.address}</p>
                  </div>
                  <button
                    onClick={() => clearSlot(idx)}
                    className="text-paper-400 hover:text-paper-600"
                  >
                    <X size={16} />
                  </button>
                </div>

                <div className="bg-white dark:bg-paper-900 rounded-lg p-3 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-xs text-paper-600">Total Cost</span>
                    <span className="font-bold text-paper-900 dark:text-white">
                      ₹{slot.plan.costs.total_estimated_cost.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-paper-600">vs Your Budget</span>
                    <span className={`text-xs font-bold ${parseFloat(budget) >= slot.plan.costs.total_estimated_cost ? 'text-green-600' : 'text-red-600'}`}>
                      {parseFloat(budget) >= slot.plan.costs.total_estimated_cost ? '✓ Fits' : '✗ Over'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-paper-600">Value Score</span>
                    <span className="font-bold text-amber-600">{(slot.plan.value_score || 0).toFixed(1)}/10</span>
                  </div>
                </div>

                {idx === cheapestIdx && (
                  <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900 rounded-lg px-3 py-2">
                    <p className="text-xs font-bold text-green-700">💰 Best Price</p>
                  </div>
                )}
                {idx === bestValueIdx && (
                  <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 rounded-lg px-3 py-2">
                    <p className="text-xs font-bold text-blue-700">⭐ Best Value</p>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        ))}
      </div>

<<<<<<< HEAD
      {/* Data Source Note */}
      <div className="flex items-center gap-2 px-4 py-3 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 rounded-lg">
        <Zap size={14} className="text-blue-600 flex-shrink-0" />
        <p className="text-xs text-blue-700">
          All destinations and pricing are powered by live Geoapify data. Costs are estimated based on your preferences.
        </p>
=======
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
                        <option value="">— Choose Destination —</option>
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
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">↳ Transport cost</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx] ? `₹${plans[idx].costs.transport_cost.toLocaleString()} (${plans[idx].costs.transport_mode})` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Hotel Cost */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">↳ Hotel cost</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx] ? `₹${plans[idx].costs.hotel_cost.toLocaleString()} (${plans[idx].costs.hotel_tier})` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Food Cost */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">↳ Food cost</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx] ? `₹${plans[idx].costs.food_cost.toLocaleString()}` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Activities Cost */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">↳ Activities cost</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx] ? `₹${plans[idx].costs.activities_cost.toLocaleString()}` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Local Transport + Taxes */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">↳ Local transport + taxes</td>
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
                    {plans[idx] ? `${Math.round(plans[idx].value_score)}%` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Budget Compatibility Score */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">↳ Budget Compatibility</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx]?.breakdown ? `${Math.round(plans[idx].breakdown.budget_compatibility * 100)}%` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Type Match Score */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">↳ Travel Type Match</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx]?.breakdown ? `${Math.round(plans[idx].breakdown.trip_type_match * 100)}%` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Comfort Match Score */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">↳ Comfort Match</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx]?.breakdown ? `${Math.round(plans[idx].breakdown.comfort_match * 100)}%` : '"”'}
                  </td>
                ))}
              </tr>

              {/* Row: Duration Suitability */}
              <tr>
                <td className="p-4 bg-paper-50/20 dark:bg-paper-900/5 pl-6">↳ Duration Suitability</td>
                {[0, 1, 2].map(idx => (
                  <td key={idx} className="p-4 border-l border-paper-100 dark:border-paper-700/60 font-medium text-paper-500 dark:text-paper-400">
                    {plans[idx]?.breakdown ? `${Math.round(plans[idx].breakdown.duration_suitability * 100)}%` : '"”'}
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
>>>>>>> 467e16fe48924e822e46cfc90613a82a82de7374
      </div>
    </div>
  );
};
