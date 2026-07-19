import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';
import { TripFlowGuide } from '../components/TripFlowGuide';
import {
  Compass,
  MapPin,
  Calendar,
  Users,
  Wallet,
  Sliders,
  Sparkles,
  Loader,
  Check,
  Download,
  AlertTriangle,
  ArrowRight,
  Search,
  Star,
  Plane,
  Train,
  Building,
  Utensils,
  Camera,
  Percent,
  LifeBuoy,
  ChevronDown,
  ChevronUp,
  Map
} from 'lucide-react';
import { LocationPickerModal } from '../components/LocationPickerModal';


interface ItineraryActivity {
  time: string;
  title: string;
  cost: number;
}

interface ItineraryDay {
  day_number: number;
  activities: ItineraryActivity[];
  description: string;
}

interface CostAllocation {
  transport_mode: string;
  hotel_tier: string;
  transport_cost: number;
  hotel_cost: number;
  food_cost: number;
  activities_cost: number;
  local_transport_cost: number;
  taxes_fees_cost: number;
  emergency_reserve: number;
  total_estimated_cost: number;
}

interface PlanResult {
  destination: {
    id: number;
    name: string;
    state: string;
    description: string;
    rating: number;
    category: string;
    best_season: string;
    attractions: string[];
  };
  costs: CostAllocation;
  savings: number;
  value_score: number;
  under_budget: boolean;
  itineraries: ItineraryDay[];
  budget: number;
  days: number;
  travelers_count: number;
  comfort_score: number;
  travel_type: string;
}

interface SearchResult {
  destination: PlanResult['destination'];
  estimated_cost: number;
  budget_fit: number;
  rating: number;
  value_score: number;
}

type PlannerMode = 'plan' | 'discover';

interface BudgetPlannerProps {
  initialMode?: PlannerMode;
}

export const BudgetPlanner: React.FC<BudgetPlannerProps> = ({ initialMode = 'discover' }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const modeParam = searchParams.get('mode');
  const startingMode: PlannerMode =
    modeParam === 'plan' ? 'plan' : modeParam === 'discover' ? 'discover' : initialMode;

  const [flowMode, setFlowMode] = useState<PlannerMode>(startingMode);
  const [startingCity, setStartingCity] = useState('');
  const [budget, setBudget] = useState<string>('20000');
  const [days, setDays] = useState<number>(4);
  const [travelType, setTravelType] = useState('Nature');
  const [travelersCount, setTravelersCount] = useState<number>(1);
  const [comfortScore, setComfortScore] = useState<number>(50);
  const [selectedDestinationId, setSelectedDestinationId] = useState<number | null>(null);
  const [selectedDestinationName, setSelectedDestinationName] = useState<string | null>(null);
  const [allDestinations, setAllDestinations] = useState<{ id: number; name: string; category: string; state: string }[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchCompleted, setSearchCompleted] = useState(false);
  const [plan, setPlan] = useState<PlanResult | null>(null);
  const [savedTripId, setSavedTripId] = useState<number | null>(null);
  const [savingTrip, setSavingTrip] = useState(false);
  const [isMapModalOpen, setIsMapModalOpen] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  // Fetch all destinations for select dropdown in Build Itinerary mode
  React.useEffect(() => {
    api.get('/api/destinations/', { params: { limit: 100 } })
      .then(response => {
        setAllDestinations(response.data.destinations || []);
      })
      .catch(err => {
        console.error('Failed to fetch destinations list:', err);
      });
  }, []);

  // Prefill hook from Reverse Search
  React.useEffect(() => {
    const rawData = sessionStorage.getItem('prefilled_planner');
    if (rawData) {
      try {
        const data = JSON.parse(rawData);
        setStartingCity(data.startingCity || 'Bangalore');
        setBudget(String(data.budget || 20000));
        setDays(data.days || 4);
        setTravelType(data.travelType || 'Nature');
        setTravelersCount(data.travelersCount || 1);
        setComfortScore(data.comfortScore || 50);
        setSelectedDestinationId(data.destinationId || null);
        setSelectedDestinationName(data.destName || null);
        if (data.flowMode === 'discover' || data.flowMode === 'plan') {
          setFlowMode(data.flowMode);
        }

        sessionStorage.removeItem('prefilled_planner');

        // Trigger immediate plan generation when a specific destination was passed in
        setLoading(true);
        api.post('/api/trips/plan', {
          starting_city: data.startingCity || 'Bangalore',
          budget: data.budget || 20000,
          days: data.days || 4,
          travel_type: data.travelType || 'Nature',
          travelers_count: data.travelersCount || 1,
          comfort_score: data.comfortScore || 50,
          destination_id: data.destinationId || null
        }).then(response => {
          setPlan(response.data);
          setExpandedDays({ 1: true });
        }).catch(err => {
          console.error(err);
          setError(err.response?.data?.detail || 'Failed to auto-generate plan.');
        }).finally(() => {
          setLoading(false);
        });
      } catch (e) {
        console.error("Error prefilling planner data", e);
      }
    }
  }, []);

  // Expandable days in itinerary
  const [expandedDays, setExpandedDays] = useState<Record<number, boolean>>({ 1: true });

  const toggleDay = (day: number) => {
    setExpandedDays(prev => ({ ...prev, [day]: !prev[day] }));
  };

  const travelTypes = [
    'Nature', 'Adventure', 'Family', 'Religious',
    'Beach', 'City Exploration', 'Romantic', 'Solo'
  ];

  const getComfortLabel = (score: number) => {
    if (score < 30) return { label: 'Budget Traveler', desc: 'Sleeper Trains, local homestays & street eats.', color: 'text-emerald-500' };
    if (score <= 70) return { label: 'Mid-Range Comfort', desc: 'AC Trains / Flights, 3-star hotels & dining.', color: 'text-violet-500' };
    return { label: 'Luxury Stays', desc: 'Premium Flights, 4/5-star resorts & fine dining.', color: 'text-amber-500' };
  };

  const getValueScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
    if (score >= 50) return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
    return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
  };

  const comfortInfo = getComfortLabel(comfortScore);

  const buildTripPayload = (destinationId?: number) => ({
    starting_city: startingCity,
    budget: Number(budget),
    days,
    travel_type: travelType,
    travelers_count: travelersCount,
    comfort_score: comfortScore,
    destination_id: destinationId ?? selectedDestinationId ?? null
  });

  const handlePrimaryAction = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setPlan(null);
    setSavedTripId(null);

    if (!startingCity.trim()) {
      setError('Please enter a starting city.');
      return;
    }
    const budgetNum = Number(budget);
    if (!budget || isNaN(budgetNum) || budgetNum <= 0) {
      setError('Please enter a valid budget.');
      return;
    }
    if (days < 1 || days > 14) {
      setError('Trip duration must be between 1 and 14 days.');
      return;
    }

    if (flowMode === 'discover') {
      setSearchLoading(true);
      setSearchCompleted(false);
      setSearchResults([]);
      try {
        const response = await api.get('/api/trips/reverse/search', {
          params: {
            budget: budgetNum,
            days,
            travel_type: travelType,
            travelers_count: travelersCount,
            starting_city: startingCity,
            comfort_score: comfortScore
          }
        });
        setSearchResults(response.data);
        setSearchCompleted(true);
      } catch (err: any) {
        console.error(err);
        setError(err.response?.data?.detail || 'Failed to fetch matching destinations.');
      } finally {
        setSearchLoading(false);
      }
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/api/trips/plan', buildTripPayload());
      setPlan(response.data);
      setExpandedDays({ 1: true });
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to generate plan. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDestination = async (result: SearchResult) => {
    setSelectedDestinationId(result.destination.id);
    setSelectedDestinationName(result.destination.name);
    setTravelType(result.destination.category);
    setFlowMode('plan');
    setError(null);
    setSearchCompleted(false);
    setPlan(null);
    setLoading(true);

    try {
      const response = await api.post('/api/trips/plan', buildTripPayload(result.destination.id));
      setPlan(response.data);
      setExpandedDays({ 1: true });
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to generate a plan for this destination.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTrip = async () => {
    if (!plan || savedTripId) return;
    setSavingTrip(true);
    try {
      const response = await api.post('/api/trips/', plan);
      setSavedTripId(response.data.id);
    } catch (err: any) {
      console.error(err);
      setError('Failed to save trip to database.');
    } finally {
      setSavingTrip(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!savedTripId || !plan) return;
    setDownloadingPdf(true);
    try {
      const response = await api.get(`/api/trips/${savedTripId}/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `budgetbound_${plan.destination.name.replace(/\s+/g, '_').toLowerCase()}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download PDF:', err);
    } finally {
      setDownloadingPdf(false);
    }
  };

  // Health Meter Colors
  const getUsagePercentage = () => {
    if (!plan) return 0;
    return (plan.costs.total_estimated_cost / plan.budget) * 100;
  };

  const pct = getUsagePercentage();
  const getHealthColor = (percent: number) => {
    if (percent <= 85) return 'bg-emerald-500';
    if (percent <= 100) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  const getHealthBg = (percent: number) => {
    if (percent <= 85) return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-400';
    if (percent <= 100) return 'bg-amber-500/10 border-amber-500/30 text-amber-700 dark:text-amber-400';
    return 'bg-rose-500/10 border-rose-500/30 text-rose-700 dark:text-rose-400';
  };

  return (
    <div className="flex flex-col gap-8">

      {/* Title */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <Compass className="text-violet-600" />
            Trip Flow
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-3xl mt-1">
            Start by finding good destinations if you are unsure, then continue into the planner to generate the final itinerary. It is the same inputs, but one guided path.
          </p>
        </div>

        <div className="inline-flex rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-1 shadow-sm self-start">
          <button
            type="button"
            onClick={() => setFlowMode('discover')}
            className={`rounded-xl px-4 py-2 text-xs font-bold transition-all ${flowMode === 'discover'
              ? 'bg-violet-600 text-white shadow-md shadow-violet-600/10'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
          >
            1. Find destinations
          </button>
          <button
            type="button"
            onClick={() => setFlowMode('plan')}
            className={`rounded-xl px-4 py-2 text-xs font-bold transition-all ${flowMode === 'plan'
              ? 'bg-violet-600 text-white shadow-md shadow-violet-600/10'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
          >
            2. Build itinerary
          </button>
        </div>
      </div>

      <TripFlowGuide
        eyebrow="One flow, two steps"
        title={flowMode === 'discover'
          ? 'First find the best destinations, then open the itinerary builder'
          : 'Then turn the chosen destination into a full trip plan'}
        description={flowMode === 'discover'
          ? 'Use this step to compare options. The app ranks destinations by your budget, days, starting city, and comfort level, then lets you choose one to continue.'
          : 'Use the selected destination or let the planner choose the strongest fit. The backend will calculate the trip and show the final itinerary in the same place.'}
        ctaLabel={flowMode === 'discover' ? 'Find matches first' : 'Build the itinerary next'}
        steps={[
          { title: 'Step 1: Set trip details', description: 'Enter the same trip details once for either discovery or planning.' },
          { title: 'Step 2: Compare or lock a destination', description: 'Search first, or jump straight into itinerary generation if you already know what you want.' },
          { title: 'Step 3: Save the final trip', description: 'Review the generated plan, save it, and then manage expenses later.' }
        ]}
      />

      {selectedDestinationName ? (
        <div className="inline-flex items-center gap-2 self-start rounded-full border border-violet-200 dark:border-violet-900/40 bg-violet-50 dark:bg-violet-950/30 px-4 py-2 text-xs font-bold text-violet-700 dark:text-violet-300">
          Locked destination: {selectedDestinationName}
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

        {/* Left Column: Form Controls */}
        <div className="lg:col-span-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
            <Sliders className="text-violet-500" size={18} />
            Trip Settings
          </h2>

          <form onSubmit={handlePrimaryAction} className="flex flex-col gap-5">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Starting Location</label>
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

            {flowMode === 'plan' && (
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Destination (Optional)</label>
                <div className="relative">
                  <select
                    value={selectedDestinationId || ''}
                    onChange={(e) => {
                      const idVal = e.target.value;
                      if (!idVal) {
                        setSelectedDestinationId(null);
                        setSelectedDestinationName(null);
                      } else {
                        const numericId = Number(idVal);
                        const match = allDestinations.find(d => d.id === numericId);
                        if (match) {
                          setSelectedDestinationId(numericId);
                          setSelectedDestinationName(match.name);
                          setTravelType(match.category);
                        }
                      }
                    }}
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white appearance-none"
                  >
                    <option value="">Let Planner Choose (Best Fit)</option>
                    {allDestinations.map(d => (
                      <option key={d.id} value={d.id}>{d.name} ({d.state})</option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Budget (INR)</label>
                <div className="relative">
                  <Wallet className="absolute left-3.5 top-3.5 text-slate-400" size={16} />
                  <input
                    type="number"
                    required
                    min={1000}
                    value={budget}
                    onChange={(e) => setBudget(e.target.value)}
                    placeholder="20000"
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

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
                    placeholder="4"
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Travelers Count</label>
                <div className="relative">
                  <Users className="absolute left-3.5 top-3.5 text-slate-400" size={16} />
                  <input
                    type="number"
                    required
                    min={1}
                    value={travelersCount}
                    onChange={(e) => setTravelersCount(Number(e.target.value))}
                    placeholder="1"
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white"
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
            </div>

            {/* Comfort vs Budget Slider */}
            <div className="border-t border-slate-100 dark:border-slate-700 pt-4 mt-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">Comfort vs Budget</span>
                <span className="text-sm font-bold text-violet-600 dark:text-violet-400">{comfortScore}/100</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={comfortScore}
                onChange={(e) => setComfortScore(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-violet-600 focus:outline-none"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-bold uppercase mt-1">
                <span>Maximum Savings</span>
                <span>Premium Quality</span>
              </div>

              {/* Dynamic slider details */}
              <div className="mt-4 p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-100 dark:border-slate-800 text-xs">
                <span className={`font-bold block ${comfortInfo.color} mb-1`}>{comfortInfo.label}</span>
                <span className="text-slate-500 dark:text-slate-400 leading-normal">{comfortInfo.desc}</span>
              </div>
            </div>

            {error && (
              <p className="text-rose-500 text-xs font-medium bg-rose-500/10 border border-rose-500/20 p-3 rounded-lg flex items-center gap-2">
                <AlertTriangle size={14} className="shrink-0" />
                {error}
              </p>
            )}

            {flowMode === 'discover' && (
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 p-3 rounded-xl">
                This step only compares destinations. Pick one result to continue into the itinerary builder automatically.
              </p>
            )}

            <button
              type="submit"
              disabled={loading || searchLoading}
              className="w-full inline-flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold py-3.5 rounded-xl transition-all shadow-md shadow-violet-500/10 disabled:opacity-50"
            >
              {flowMode === 'discover' ? (
                searchLoading ? (
                  <>
                    <Loader size={18} className="animate-spin" />
                    Finding Matches...
                  </>
                ) : (
                  <>
                    <Search size={18} />
                    Find Matching Trips
                  </>
                )
              ) : loading ? (
                <>
                  <Loader size={18} className="animate-spin" />
                  Mapping Destinations...
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  Generate Travel Plan
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Column: Generated Plans */}
        <div className="lg:col-span-8">
          {flowMode === 'discover' && (
            <div className="flex flex-col gap-6">
              {!searchCompleted && !searchLoading && (
                <div className="bg-slate-100 dark:bg-slate-800/40 border border-dashed border-slate-200 dark:border-slate-700 rounded-2xl h-96 flex flex-col items-center justify-center text-center p-6">
                  <Search className="h-16 w-16 text-slate-300 dark:text-slate-600 mb-4 animate-pulse" />
                  <h3 className="text-lg font-bold text-slate-700 dark:text-slate-300 mb-2">Search for matching destinations</h3>
                  <p className="text-sm text-slate-400 max-w-sm">
                    Use the same trip inputs to compare options first. The strongest matches will appear here.
                  </p>
                </div>
              )}

              {searchLoading && (
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm space-y-6 animate-pulse">
                  <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-2/3" />
                  <div className="space-y-3">
                    <div className="h-24 bg-slate-200 dark:bg-slate-700 rounded" />
                    <div className="h-24 bg-slate-200 dark:bg-slate-700 rounded" />
                    <div className="h-24 bg-slate-200 dark:bg-slate-700 rounded" />
                  </div>
                </div>
              )}

              {searchCompleted && searchResults.length === 0 && (
                <div className="bg-slate-100 dark:bg-slate-800/40 border border-dashed border-slate-200 dark:border-slate-700 rounded-2xl h-96 flex flex-col items-center justify-center text-center p-6">
                  <AlertTriangle className="h-16 w-16 text-slate-300 dark:text-slate-600 mb-4" />
                  <h3 className="text-lg font-bold text-slate-700 dark:text-slate-300 mb-2">No matches found</h3>
                  <p className="text-sm text-slate-400 max-w-sm">
                    Try adjusting the budget, duration, or trip type, then search again.
                  </p>
                </div>
              )}

              {searchCompleted && searchResults.length > 0 && (
                <div className="flex flex-col gap-4">
                  <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">Top destination matches</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Pick a destination below to lock it into the itinerary builder.
                    </p>
                  </div>

                  {searchResults.map((res, index) => (
                    <div
                      key={res.destination.id}
                      className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm flex flex-col md:flex-row gap-5 items-start justify-between relative group hover:border-violet-500/40 transition-colors"
                    >
                      <div className="space-y-3 flex-1">
                        <div className="flex items-center gap-3 flex-wrap">
                          <div className="h-6 w-6 rounded-full bg-violet-600/10 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400 font-extrabold text-[10px] flex items-center justify-center">
                            #{index + 1}
                          </div>
                          <h4 className="font-extrabold text-lg text-slate-900 dark:text-white group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
                            {res.destination.name}
                          </h4>
                          <span className="bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase">
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

                        <div className="flex items-center gap-4 text-xs font-semibold text-slate-600 dark:text-slate-400 pt-1">
                          <div className="flex items-center gap-0.5 text-amber-500">
                            <Star size={13} fill="currentColor" />
                            <span className="font-bold text-slate-800 dark:text-white">{res.destination.rating}</span>
                          </div>
                          <span>Best season: {res.destination.best_season}</span>
                        </div>
                      </div>

                      <div className="flex flex-col items-start md:items-end gap-3 justify-between md:border-l md:border-slate-100 md:dark:border-slate-700/60 md:pl-6 shrink-0 w-full md:w-auto">
                        <div className="flex flex-col md:items-end">
                          <span className="text-[9px] text-slate-400 font-bold uppercase">Estimated Cost</span>
                          <span className="text-lg font-extrabold text-slate-900 dark:text-white">INR {res.estimated_cost.toLocaleString()}</span>
                          <span className="text-[9px] text-slate-400 font-medium">({res.budget_fit}% of budget)</span>
                        </div>

                        <div className={`px-2.5 py-1 rounded-lg border text-[10px] font-bold uppercase ${getValueScoreColor(res.value_score)}`}>
                          Match Score: {res.value_score}
                        </div>

                        <button
                          onClick={() => handleSelectDestination(res)}
                          className="w-full md:w-auto inline-flex items-center justify-center gap-1 bg-slate-900 hover:bg-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 text-white font-bold px-4 py-2.5 rounded-xl text-xs transition-all"
                        >
                          Use this destination
                          <ArrowRight size={13} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {flowMode === 'plan' && !plan && !loading && (
            <div className="bg-slate-100 dark:bg-slate-800/40 border border-dashed border-slate-200 dark:border-slate-700 rounded-2xl h-96 flex flex-col items-center justify-center text-center p-6">
              <Compass className="h-16 w-16 text-slate-300 dark:text-slate-600 mb-4 animate-pulse" />
              <h3 className="text-lg font-bold text-slate-700 dark:text-slate-300 mb-2">No Plan Generated Yet</h3>
              <p className="text-sm text-slate-400 max-w-sm">
                Enter your details on the left and hit generate to compute the itinerary.
              </p>
            </div>
          )}

          {flowMode === 'plan' && loading && (
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm space-y-6 animate-pulse">
              <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-1/3" />
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-2/3" />
              <div className="grid grid-cols-3 gap-4">
                <div className="h-20 bg-slate-200 dark:bg-slate-700 rounded" />
                <div className="h-20 bg-slate-200 dark:bg-slate-700 rounded" />
                <div className="h-20 bg-slate-200 dark:bg-slate-700 rounded" />
              </div>
              <div className="h-40 bg-slate-200 dark:bg-slate-700 rounded" />
            </div>
          )}

          {flowMode === 'plan' && plan && (
            <div className="flex flex-col gap-6">

              {/* Plan Header Card */}
              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm relative overflow-hidden">
                <div className="absolute top-0 right-0 bg-violet-600 text-white text-xs font-semibold px-4 py-1.5 rounded-bl-2xl">
                  {plan.destination.category}
                </div>

                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                  <div>
                    <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">{plan.destination.state}</span>
                    <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">{plan.destination.name}</h2>
                  </div>
                  <div className="flex gap-2">
                    {savedTripId ? (
                      <>
                        <button
                          onClick={handleDownloadPDF}
                          disabled={downloadingPdf}
                          className="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-800 dark:text-white px-4 py-2 rounded-xl text-sm font-bold transition-all disabled:opacity-50"
                        >
                          {downloadingPdf ? (
                            <Loader size={16} className="animate-spin" />
                          ) : (
                            <Download size={16} />
                          )}
                          Download PDF
                        </button>
                        <button
                          onClick={() => navigate(`/expenses/${savedTripId}`)}
                          className="inline-flex items-center gap-1 bg-violet-600 hover:bg-violet-500 text-white px-4 py-2 rounded-xl text-sm font-bold transition-all shadow-md shadow-violet-600/10"
                        >
                          Manage Expenses
                          <ArrowRight size={14} />
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={handleSaveTrip}
                        disabled={savingTrip}
                        className="inline-flex items-center gap-1.5 bg-violet-600 hover:bg-violet-500 text-white px-5 py-2.5 rounded-xl text-sm font-bold transition-all shadow-md shadow-violet-600/10"
                      >
                        {savingTrip ? <Loader size={16} className="animate-spin" /> : <Check size={16} />}
                        Save Travel Plan
                      </button>
                    )}
                  </div>
                </div>

                <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed mb-6">
                  {plan.destination.description}
                </p>

                {/* Seeding attributes */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 border-t border-slate-100 dark:border-slate-700 pt-6">
                  <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl">
                    <span className="text-[10px] text-slate-400 font-bold block uppercase mb-1">Trip Duration</span>
                    <span className="text-sm font-bold text-slate-800 dark:text-white">{plan.days} Days</span>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl">
                    <span className="text-[10px] text-slate-400 font-bold block uppercase mb-1">Hotel Tier</span>
                    <span className="text-sm font-bold text-slate-800 dark:text-white">{plan.costs.hotel_tier}</span>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl">
                    <span className="text-[10px] text-slate-400 font-bold block uppercase mb-1">Transport</span>
                    <span className="text-sm font-bold text-slate-800 dark:text-white">{plan.costs.transport_mode}</span>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl">
                    <span className="text-[10px] text-slate-400 font-bold block uppercase mb-1">Best Season</span>
                    <span className="text-xs font-bold text-slate-800 dark:text-white truncate block">{plan.destination.best_season}</span>
                  </div>
                </div>
              </div>

              {/* Budget Health Meter */}
              <div className={`border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm ${getHealthBg(pct)}`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-3">
                  <div>
                    <h3 className="font-extrabold text-sm tracking-wide uppercase">Budget Utilization</h3>
                    <p className="text-[11px] opacity-80 mt-0.5">Estimated Cost vs Allocated Budget</p>
                  </div>
                  <div className="text-right sm:text-right">
                    <span className="text-base font-extrabold">INR {plan.costs.total_estimated_cost.toLocaleString()}</span>
                    <span className="text-xs font-semibold opacity-80"> of INR {plan.budget.toLocaleString()}</span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${getHealthColor(pct)}`}
                    style={{ width: `${Math.min(100, pct)}%` }}
                  />
                </div>

                <div className="flex items-center justify-between mt-3 text-xs font-bold">
                  <span>{pct.toFixed(0)}% Used</span>
                  <span>
                    {plan.savings >= 0 ? (
                      <span className="text-emerald-500">Remaining Savings: INR {plan.savings.toLocaleString()}</span>
                    ) : (
                      <span className="text-rose-500">Exceeds Budget By: INR {Math.abs(plan.savings).toLocaleString()}</span>
                    )}
                  </span>
                </div>
              </div>

              {/* Two Column Cost Breakdown & Daily Itinerary */}
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6">

                {/* Cost Breakdown Module */}
                <div className="md:col-span-5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm">
                  <h3 className="text-base font-bold text-slate-800 dark:text-white mb-4">Cost Breakdown</h3>

                  <div className="flex flex-col gap-3.5 text-xs text-slate-600 dark:text-slate-300">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        {plan.costs.transport_mode === 'Flight' ? <Plane size={15} className="text-violet-500" /> : <Train size={15} className="text-violet-500" />}
                        Transportation
                      </span>
                      <span className="font-bold text-slate-800 dark:text-white">INR {plan.costs.transport_cost.toLocaleString()}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Building size={15} className="text-violet-500" />
                        Accommodation
                      </span>
                      <span className="font-bold text-slate-800 dark:text-white">INR {plan.costs.hotel_cost.toLocaleString()}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Utensils size={15} className="text-violet-500" />
                        Food & Dining
                      </span>
                      <span className="font-bold text-slate-800 dark:text-white">INR {plan.costs.food_cost.toLocaleString()}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Camera size={15} className="text-violet-500" />
                        Activities
                      </span>
                      <span className="font-bold text-slate-800 dark:text-white">INR {plan.costs.activities_cost.toLocaleString()}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <MapPin size={15} className="text-violet-500" />
                        Local Transport
                      </span>
                      <span className="font-bold text-slate-800 dark:text-white">INR {plan.costs.local_transport_cost.toLocaleString()}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Percent size={15} className="text-violet-500" />
                        Taxes & Booking Fees
                      </span>
                      <span className="font-bold text-slate-800 dark:text-white">INR {plan.costs.taxes_fees_cost.toLocaleString()}</span>
                    </div>

                    <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-700 pt-3">
                      <span className="flex items-center gap-2">
                        <LifeBuoy size={15} className="text-violet-500" />
                        Emergency Reserve
                      </span>
                      <span className="font-bold text-slate-800 dark:text-white">INR {plan.costs.emergency_reserve.toLocaleString()}</span>
                    </div>
                  </div>

                  {/* Hidden Cost Prediction Module */}
                  <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 mt-6">
                    <h4 className="text-xs font-bold flex items-center gap-1.5 mb-3 text-violet-600 dark:text-violet-400 uppercase tracking-wide">
                      <LifeBuoy size={14} />
                      Hidden Cost Prediction
                    </h4>
                    <div className="flex flex-col gap-2.5 text-[11px] text-slate-500 dark:text-slate-400">
                      <div className="flex justify-between">
                        <span>Local Auto / Cab Pool</span>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">INR {Math.round(plan.costs.local_transport_cost * 0.6).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Attraction Toll / Parking</span>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">INR {Math.round(plan.costs.local_transport_cost * 0.15).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Booking Convenience Tax</span>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">INR {Math.round(plan.costs.taxes_fees_cost * 0.65).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Miscellaneous Contingency</span>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">INR {plan.costs.emergency_reserve.toLocaleString()}</span>
                      </div>
                      <div className="border-t border-slate-200 dark:border-slate-700 pt-2 flex justify-between font-bold text-slate-800 dark:text-white">
                        <span>Total Buffer Needed</span>
                        <span>INR {(Math.round(plan.costs.local_transport_cost * 0.75) + Math.round(plan.costs.taxes_fees_cost * 0.65) + plan.costs.emergency_reserve).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Smart Daily Planner (Itinerary) */}
                <div className="md:col-span-7 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm">
                  <h3 className="text-base font-bold text-slate-800 dark:text-white mb-4">Smart Daily Planner</h3>

                  <div className="flex flex-col gap-3">
                    {plan.itineraries.map((day) => {
                      const isOpen = !!expandedDays[day.day_number];
                      return (
                        <div key={day.day_number} className="border border-slate-100 dark:border-slate-700/60 rounded-xl overflow-hidden">
                          <button
                            type="button"
                            onClick={() => toggleDay(day.day_number)}
                            className="w-full flex items-center justify-between p-3.5 bg-slate-50 dark:bg-slate-900/40 text-left font-bold text-xs uppercase text-slate-700 dark:text-slate-300 focus:outline-none"
                          >
                            <span>Day {day.day_number} Plan</span>
                            {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                          </button>

                          {isOpen && (
                            <div className="p-4 border-t border-slate-100 dark:border-slate-700/60 bg-white dark:bg-slate-800 flex flex-col gap-3">
                              <p className="text-slate-500 dark:text-slate-400 text-xs italic leading-relaxed">{day.description}</p>

                              <div className="flex flex-col gap-2 pt-2 border-t border-slate-100 dark:border-slate-700/30">
                                {day.activities.map((act, actIdx) => (
                                  <div key={actIdx} className="flex justify-between items-start gap-4 text-xs">
                                    <div className="flex items-start gap-2.5">
                                      <span className="font-bold text-[10px] uppercase text-violet-500 shrink-0 mt-0.5 w-16">{act.time}</span>
                                      <span className="text-slate-700 dark:text-slate-300 font-medium leading-relaxed">{act.title}</span>
                                    </div>
                                    <span className="text-slate-400 font-medium shrink-0">
                                      {act.cost > 0 ? `INR ${act.cost}` : 'Free'}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

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
