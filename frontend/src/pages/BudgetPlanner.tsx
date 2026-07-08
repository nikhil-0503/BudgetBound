import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
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
  Plane,
  Train,
  Building,
  Utensils,
  Camera,
  Percent,
  LifeBuoy,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

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

export const BudgetPlanner: React.FC = () => {
  const navigate = useNavigate();
  const [startingCity, setStartingCity] = useState('');
  const [budget, setBudget] = useState<string>('20000');
  const [days, setDays] = useState<number>(4);
  const [travelType, setTravelType] = useState('Nature');
  const [travelersCount, setTravelersCount] = useState<number>(1);
  const [comfortScore, setComfortScore] = useState<number>(50);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plan, setPlan] = useState<PlanResult | null>(null);
  const [savedTripId, setSavedTripId] = useState<number | null>(null);
  const [savingTrip, setSavingTrip] = useState(false);

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
        
        sessionStorage.removeItem('prefilled_planner');

        // Trigger immediate matching
        setLoading(true);
        api.post('/api/trips/plan', {
          starting_city: data.startingCity || 'Bangalore',
          budget: data.budget || 20000,
          days: data.days || 4,
          travel_type: data.travelType || 'Nature',
          travelers_count: data.travelersCount || 1,
          comfort_score: data.comfortScore || 50
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

  const comfortInfo = getComfortLabel(comfortScore);

  const handleGeneratePlan = async (e: React.FormEvent) => {
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

    setLoading(true);
    try {
      const response = await api.post('/api/trips/plan', {
        starting_city: startingCity,
        budget: budgetNum,
        days,
        travel_type: travelType,
        travelers_count: travelersCount,
        comfort_score: comfortScore
      });
      setPlan(response.data);
      // Auto-expand first day
      setExpandedDays({ 1: true });
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to generate plan. Please try again.');
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

  const handleDownloadPDF = () => {
    if (!savedTripId) return;
    // Trigger direct browser download
    const token = localStorage.getItem('token');
    window.open(`http://localhost:8000/api/trips/${savedTripId}/pdf?token=${token}`, '_blank');
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
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
          <Compass className="text-violet-600" />
          Budget Travel Planner
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Enter your trip parameters and let our engine map out a complete itinerary that stays inside your budget.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Form Controls */}
        <div className="lg:col-span-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
            <Sliders className="text-violet-500" size={18} />
            Trip Settings
          </h2>

          <form onSubmit={handleGeneratePlan} className="flex flex-col gap-5">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Starting Location</label>
              <div className="relative">
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
            </div>

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

            <button
              type="submit"
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold py-3.5 rounded-xl transition-all shadow-md shadow-violet-500/10 disabled:opacity-50"
            >
              {loading ? (
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
          {!plan && !loading && (
            <div className="bg-slate-100 dark:bg-slate-800/40 border border-dashed border-slate-200 dark:border-slate-700 rounded-2xl h-96 flex flex-col items-center justify-center text-center p-6">
              <Compass className="h-16 w-16 text-slate-300 dark:text-slate-600 mb-4 animate-pulse" />
              <h3 className="text-lg font-bold text-slate-700 dark:text-slate-300 mb-2">No Plan Generated Yet</h3>
              <p className="text-sm text-slate-400 max-w-sm">
                Enter your details on the left and hit generate to compute matching travel packages.
              </p>
            </div>
          )}

          {loading && (
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

          {plan && (
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
                          className="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-800 dark:text-white px-4 py-2 rounded-xl text-sm font-bold transition-all"
                        >
                          <Download size={16} />
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

    </div>
  );
};
