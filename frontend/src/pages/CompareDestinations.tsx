import React, { useState, useEffect } from 'react';
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

      {/* Data Source Note */}
      <div className="flex items-center gap-2 px-4 py-3 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 rounded-lg">
        <Zap size={14} className="text-blue-600 flex-shrink-0" />
        <p className="text-xs text-blue-700">
          All destinations and pricing are powered by live Geoapify data. Costs are estimated based on your preferences.
        </p>
      </div>
    </div>
  );
};
