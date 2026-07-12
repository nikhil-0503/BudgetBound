import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { TripFlowGuide } from '../components/TripFlowGuide';
import {
  Search,
  Wallet,
  Calendar,
  Compass,
  Loader,
  AlertTriangle,
  ArrowRight,
  Star,
  Sliders,
  MapPin,
  Map
} from 'lucide-react';
import { LocationPickerModal } from '../components/LocationPickerModal';


interface DestinationResult {
  destination: {
    id: number;
    name: string;
    state: string;
    description: string;
    rating: number;
    category: string;
    best_season: string;
    attractions: string[];
    avg_travel_cost: number;
    avg_hotel_cost: number;
    avg_food_cost: number;
    avg_activity_cost: number;
  };
  estimated_cost: number;
  budget_fit: number;
  rating: number;
  value_score: number;
}

export const ReverseSearch: React.FC = () => {
  const navigate = useNavigate();
  const [startingCity, setStartingCity] = useState('Bangalore');
  const [budget, setBudget] = useState<number>(25000);
  const [days, setDays] = useState<number>(5);
  const [travelType, setTravelType] = useState('Nature');
  const [travelersCount, setTravelersCount] = useState<number>(1);
  const [comfortScore, setComfortScore] = useState<number>(50);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<DestinationResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [isMapModalOpen, setIsMapModalOpen] = useState(false);

  const travelTypes = [
    'Nature', 'Adventure', 'Family', 'Religious',
    'Beach', 'City Exploration', 'Romantic', 'Solo'
  ];

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResults([]);
    setHasSearched(false);

    if (!startingCity.trim()) {
      setError('Please enter a starting city.');
      return;
    }
    if (budget <= 0) {
      setError('Please enter a valid budget.');
      return;
    }
    if (days < 1 || days > 14) {
      setError('Duration must be between 1 and 14 days.');
      return;
    }

    setLoading(true);
    try {
      const response = await api.get('/api/trips/reverse/search', {
        params: {
          budget,
          days,
          travel_type: travelType,
          travelers_count: travelersCount,
          starting_city: startingCity,
          comfort_score: comfortScore
        }
      });
      setResults(response.data);
      setHasSearched(true);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch reverse search results.');
    } finally {
      setLoading(false);
    }
  };

  const handlePlanTrip = (destName: string) => {
    sessionStorage.setItem('prefilled_planner', JSON.stringify({
      startingCity,
      budget,
      days,
      travelType,
      travelersCount,
      comfortScore,
      destName
    }));
    navigate('/planner');
  };

  const getValueScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-505 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    if (score >= 50) return 'text-amber-505 dark:text-amber-400 bg-amber-500/10 border-amber-500/20';
    return 'text-rose-505 dark:text-rose-400 bg-rose-500/10 border-rose-500/20';
  };

  return (
    <div className="flex flex-col gap-8">

      {/* Title */}
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
          <Search className="text-violet-600" />
          Reverse Travel Search
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Enter your budget constraints, starting city and comfort choices. We rank the entire destination database dynamically to match.
        </p>
      </div>

      <TripFlowGuide
        eyebrow="Best for users who are still deciding where to go"
        title="Use Reverse Search when you know your budget, but not the destination"
        description="This screen scans the destination database and ranks the best options for your budget. Pick one result, and it sends the same values into the planner so you can build the final itinerary."
        ctaLabel="Find matching destinations"
        steps={[
          { title: 'Set your limits', description: 'Tell the app your budget, starting city, days, and comfort level.' },
          { title: 'Compare top matches', description: 'The app ranks destinations by value score instead of locking you into one place.' },
          { title: 'Move to planner', description: 'Select a destination and continue into the Budget Planner to generate the full trip.' }
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

        {/* Form panel */}
        <div className="lg:col-span-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
            <Sliders className="text-violet-500" size={18} />
            Search Constraints
          </h2>

          <form onSubmit={handleSearch} className="flex flex-col gap-5">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Starting From</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <MapPin className="absolute left-3.5 top-3.5 text-slate-400" size={16} />
                  <input
                    type="text"
                    required
                    value={startingCity}
                    onChange={(e) => setStartingCity(e.target.value)}
                    placeholder="e.g. Bangalore, Delhi"
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => setIsMapModalOpen(true)}
                  className="bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 px-4 rounded-xl border border-slate-200 dark:border-slate-700 transition-colors flex items-center justify-center"
                  title="Pick on map"
                >
                  <Map size={18} />
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Total Budget (INR)</label>
              <div className="relative">
                <Wallet className="absolute left-3.5 top-3.5 text-slate-400" size={16} />
                <input
                  type="number"
                  required
                  min={1000}
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  placeholder="25000"
                  className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Duration (Days)</label>
                <div className="relative">
                  <Calendar className="absolute left-3.5 top-3.5 text-slate-400" size={16} />
                  <input
                    type="number"
                    required
                    min={1}
                    max={14}
                    value={days}
                    onChange={(e) => setDays(Number(e.target.value))}
                    placeholder="5"
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Travelers</label>
                <input
                  type="number"
                  required
                  min={1}
                  value={travelersCount}
                  onChange={(e) => setTravelersCount(Number(e.target.value))}
                  className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Trip Category</label>
              <select
                value={travelType}
                onChange={(e) => setTravelType(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white appearance-none"
              >
                {travelTypes.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
                <span className="uppercase tracking-wider">Comfort vs Savings</span>
                <span className="text-violet-600 font-bold">{comfortScore}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={comfortScore}
                onChange={(e) => setComfortScore(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-100 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-violet-600"
              />
              <div className="flex justify-between text-[9px] text-slate-400 font-bold mt-1 uppercase">
                <span>Save Money</span>
                <span>Max Comfort</span>
              </div>
            </div>

            {error && (
              <p className="text-rose-500 text-xs font-medium bg-rose-500/10 border border-rose-500/20 p-3 rounded-lg flex items-center gap-2">
                <AlertTriangle size={14} className="shrink-0" />
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-violet-600 hover:bg-violet-500 text-white font-bold py-3.5 rounded-xl text-xs transition-all shadow-md shadow-violet-500/10 inline-flex items-center justify-center gap-2"
            >
              {loading ? <Loader size={16} className="animate-spin" /> : <Search size={16} />}
              Find Matching Trips
            </button>
          </form>
        </div>

        {/* Results panel */}
        <div className="lg:col-span-8 space-y-6">
          {loading && (
            <div className="border border-slate-200 dark:border-slate-700 rounded-2xl h-80 flex flex-col items-center justify-center text-center p-6 bg-white dark:bg-slate-800">
              <Loader className="h-10 w-10 text-violet-500 animate-spin mb-4" />
              <h3 className="text-sm font-bold text-slate-700 dark:text-slate-350">Scanning All Indian Gateways...</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-xs leading-normal">
                Applying weighted scoring model parameters against lodging tiers, regional multipliers and attractions...
              </p>
            </div>
          )}

          {!loading && !hasSearched && (
            <div className="border border-dashed border-slate-200 dark:border-slate-700 rounded-2xl h-80 flex flex-col items-center justify-center text-center p-6 bg-slate-50/20 dark:bg-slate-800/10">
              <Compass className="h-12 w-12 text-slate-300 dark:text-slate-655 mb-3 animate-pulse" />
              <h3 className="text-sm font-bold text-slate-600 dark:text-slate-400 mb-1">Set Constraints to Begin</h3>
              <p className="text-xs text-slate-400 max-w-xs leading-normal">
                Enter your total trip budget and location preferences on the left, and our scoring matrix will reveal the best getaways.
              </p>
            </div>
          )}

          {!loading && hasSearched && results.length === 0 && (
            <div className="border border-dashed border-slate-200 dark:border-slate-700 rounded-2xl h-80 flex flex-col items-center justify-center text-center p-6 bg-slate-50/20 dark:bg-slate-800/10">
              <AlertTriangle className="h-12 w-12 text-slate-300 dark:text-slate-655 mb-3" />
              <h3 className="text-sm font-bold text-slate-655 dark:text-slate-400 mb-1">No Matches Found</h3>
              <p className="text-xs text-slate-400 max-w-xs leading-normal">
                Try widening your budget limit or lowering travel days to discover suitable packages.
              </p>
            </div>
          )}

          {!loading && hasSearched && results.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-slate-550 dark:text-slate-400 uppercase tracking-wider">Top 5 Best Matches</h3>

              <div className="flex flex-col gap-4">
                {results.map((res, index) => (
                  <div
                    key={res.destination.id}
                    className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm flex flex-col md:flex-row gap-5 items-start justify-between relative group hover:border-violet-500/40 transition-colors"
                  >

                    {/* Left details */}
                    <div className="space-y-3 flex-1">
                      <div className="flex items-center gap-3 flex-wrap">
                        <div className="h-6 w-6 rounded-full bg-violet-650/10 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400 font-extrabold text-[10px] flex items-center justify-center">
                          #{index + 1}
                        </div>
                        <h4 className="font-extrabold text-lg text-slate-900 dark:text-white group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
                          {res.destination.name}
                        </h4>
                        <span className="bg-slate-100 dark:bg-slate-900 text-slate-550 dark:text-slate-400 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase">
                          {res.destination.category}
                        </span>
                      </div>

                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1">
                        <MapPin size={11} className="text-slate-400 shrink-0" />
                        {res.destination.state}
                      </span>

                      <p className="text-slate-500 dark:text-slate-400 text-xs leading-relaxed max-w-xl line-clamp-2">
                        {res.destination.description}
                      </p>

                      <div className="flex items-center gap-4 text-xs font-semibold text-slate-655 dark:text-slate-400 pt-1">
                        <div className="flex items-center gap-0.5 text-amber-500">
                          <Star size={13} fill="currentColor" />
                          <span className="font-bold text-slate-800 dark:text-white">{res.destination.rating}</span>
                        </div>
                        <span>Best season: {res.destination.best_season}</span>
                      </div>
                    </div>

                    {/* Right cost & action */}
                    <div className="flex flex-col items-start md:items-end gap-3 justify-between md:border-l md:border-slate-100 md:dark:border-slate-700/60 md:pl-6 shrink-0 w-full md:w-auto">
                      <div className="flex flex-col md:items-end">
                        <span className="text-[9px] text-slate-400 font-bold uppercase">Estimated Cost</span>
                        <span className="text-lg font-extrabold text-slate-900 dark:text-white">₹{res.estimated_cost.toLocaleString()}</span>
                        <span className="text-[9px] text-slate-400 font-medium">({res.budget_fit}% of budget)</span>
                      </div>

                      <div className={`px-2.5 py-1 rounded-lg border text-[10px] font-bold uppercase ${getValueScoreColor(res.value_score)}`}>
                        Match Score: {res.value_score}
                      </div>

                      <button
                        onClick={() => handlePlanTrip(res.destination.name)}
                        className="w-full md:w-auto inline-flex items-center justify-center gap-1 bg-slate-900 hover:bg-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 text-white font-bold px-4 py-2.5 rounded-xl text-xs transition-all"
                      >
                        Select & Plan
                        <ArrowRight size={13} />
                      </button>
                    </div>

                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

      </div>

      <LocationPickerModal
        isOpen={isMapModalOpen}
        onClose={() => setIsMapModalOpen(false)}
        onSelectLocation={(city) => setStartingCity(city)}
        initialCity={startingCity}
      />
    </div>
  );
};

