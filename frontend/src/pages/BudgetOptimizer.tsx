import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import api from '../services/api';
import { 
  ShieldAlert, 
  TrendingDown, 
  Check, 
  ArrowLeft, 
  Loader, 
  CheckCircle2, 
  Award,
  ChevronRight
} from 'lucide-react';

interface Allocation {
  transport_cost: number;
  hotel_cost: number;
  food_cost: number;
  activities_cost: number;
  emergency_reserve: number;
  local_transport_cost: number;
  taxes_fees_cost: number;
}

interface OptimizeOption {
  action_key: string;
  label: string;
  cost_difference: number;
  new_allocation: Allocation;
  description: string;
}

interface OptimizeResponse {
  current_cost: number;
  budget: number;
  allocations: Allocation;
  options: OptimizeOption[];
}

interface TripInfo {
  destination: {
    name: string;
    state: string;
  };
}

export const BudgetOptimizer: React.FC = () => {
  usePageTitle('Budget Optimizer | BudgetBound');
  const { tripId } = useParams<{ tripId: string }>();
  const navigate = useNavigate();
  
  const [data, setData] = useState<OptimizeResponse | null>(null);
  const [trip, setTrip] = useState<TripInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedOptionIdx, setSelectedOptionIdx] = useState<number>(0);
  const [applying, setApplying] = useState(false);
  const [success, setSuccess] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [optRes, tripRes] = await Promise.all([
        api.post(`/api/trips/${tripId}/optimize`),
        api.get(`/api/trips/${tripId}`)
      ]);
      setData(optRes.data);
      setTrip(tripRes.data);
      if (optRes.data.options.length > 0) {
        setSelectedOptionIdx(0);
      }
    } catch (err: any) {
      console.error(err);
      setError('Could not fetch optimization insights.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tripId) {
      fetchData();
    }
  }, [tripId]);

  const handleApplyOptimization = async () => {
    if (!data || data.options.length === 0 || applying) return;
    
    setApplying(true);
    const option = data.options[selectedOptionIdx];
    try {
      await api.post(`/api/trips/${tripId}/optimize/apply`, {
        action_key: option.action_key
      });
      setSuccess(true);
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (err: any) {
      console.error(err);
      setError('Failed to apply optimized changes.');
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center text-paper-500 dark:text-paper-400 gap-4">
        <Loader className="h-10 w-10 text-marigold-500 animate-spin" />
        <span className="text-sm font-semibold">Running budget simulations...</span>
      </div>
    );
  }

  if (error || !data || !trip) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 rounded-2xl flex flex-col items-start gap-3">
        <div className="flex items-center gap-2">
          <ShieldAlert size={24} />
          <h3 className="font-bold">Optimization Error</h3>
        </div>
        <p className="text-xs">{error || 'Failed to load optimization metrics.'}</p>
        <Link to="/dashboard" className="text-xs font-bold underline mt-2 block">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const hasOptions = data.options.length > 0;
  const currentOption = hasOptions ? data.options[selectedOptionIdx] : null;

  return (
    <div className="flex flex-col gap-8">
      
      {/* Header */}
      <div className="space-y-1">
        <Link 
          to="/dashboard" 
          className="inline-flex items-center gap-1.5 text-xs font-bold text-paper-400 hover:text-marigold-600 dark:hover:text-marigold-400 uppercase tracking-widest transition-colors mb-2"
        >
          <ArrowLeft size={14} />
          Back to Dashboard
        </Link>
        <h1 className="text-3xl font-extrabold text-paper-900 dark:text-white">
          Budget Optimizer: {trip.destination.name}
        </h1>
        <p className="text-sm text-paper-500 dark:text-paper-400">
          Analyze and adjust your trip parameters to save money or increase luxury dynamically.
        </p>
      </div>

      {success && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-sm font-bold flex items-center gap-3 animate-pulse">
          <CheckCircle2 size={20} />
          Optimization applied successfully! Redirecting to Dashboard...
        </div>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Current Total */}
        <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-6 rounded-2xl shadow-sm flex items-center justify-between">
          <div>
            <span className="text-[10px] text-paper-400 font-bold uppercase tracking-wider block">Current Total Cost</span>
            <span className="text-2xl font-extrabold text-paper-800 dark:text-white">₹{data.current_cost.toLocaleString()}</span>
          </div>
          <div className="h-10 w-10 rounded-lg bg-marigold-100 dark:bg-marigold-950/40 text-marigold-600 dark:text-marigold-400 flex items-center justify-center">
            ₹
          </div>
        </div>

        {/* Budget limit */}
        <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-6 rounded-2xl shadow-sm flex items-center justify-between">
          <div>
            <span className="text-[10px] text-paper-400 font-bold uppercase tracking-wider block">Target Budget</span>
            <span className="text-2xl font-extrabold text-paper-800 dark:text-white">₹{data.budget.toLocaleString()}</span>
          </div>
          <div className="h-10 w-10 rounded-lg bg-petrol-100 dark:bg-petrol-950/40 text-petrol-600 dark:text-petrol-400 flex items-center justify-center">
            L
          </div>
        </div>

        {/* Health status */}
        <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-6 rounded-2xl shadow-sm flex items-center justify-between">
          <div>
            <span className="text-[10px] text-paper-400 font-bold uppercase tracking-wider block">Target Variance</span>
            <span className={`text-xl font-extrabold block ${data.current_cost <= data.budget ? 'text-emerald-500' : 'text-rose-500'}`}>
              {data.current_cost <= data.budget 
                ? `Under Budget by ₹${(data.budget - data.current_cost).toLocaleString()}` 
                : `Over Budget by ₹${(data.current_cost - data.budget).toLocaleString()}`}
            </span>
          </div>
        </div>
      </div>

      {!hasOptions ? (
        <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-3xl p-12 text-center shadow-sm flex flex-col items-center justify-center">
          <Award className="h-16 w-16 text-emerald-500 mb-4" />
          <h3 className="text-lg font-bold text-paper-800 dark:text-white mb-2">Trip Highly Optimized</h3>
          <p className="text-sm text-paper-500 dark:text-paper-400 max-w-sm mb-6">
            Your current plan is already at budget limitations with sleeper transits and budget properties. No further optimizer guidelines are required.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Optimization Options List */}
          <div className="lg:col-span-5 flex flex-col gap-3">
            <h3 className="text-sm font-bold text-paper-500 dark:text-paper-400 uppercase tracking-wider mb-2">Optimization Strategies</h3>
            
            {data.options.map((option, index) => {
              const isSelected = index === selectedOptionIdx;
              const isSaving = option.cost_difference < 0;
              return (
                <button
                  key={option.action_key}
                  onClick={() => setSelectedOptionIdx(index)}
                  className={`w-full text-left p-4 rounded-xl border transition-all flex items-center justify-between gap-4 ${
                    isSelected
                      ? 'bg-marigold-600 border-marigold-600 text-white shadow-md shadow-marigold-600/10'
                      : 'bg-paper-50 dark:bg-paper-800 border-paper-200 dark:border-paper-700 text-paper-800 dark:text-paper-200 hover:border-paper-300 dark:hover:border-paper-600'
                  }`}
                >
                  <div className="space-y-1">
                    <span className="text-xs font-bold block">{option.label}</span>
                    <span className={`text-[10px] ${isSelected ? 'text-marigold-200' : 'text-paper-400'}`}>
                      {option.action_key.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className={`text-xs font-bold px-2 py-1 rounded ${
                      isSelected
                        ? 'bg-paper-50/20 text-white'
                        : isSaving ? 'bg-emerald-500/15 text-emerald-500' : 'bg-marigold-500/15 text-marigold-500'
                    }`}>
                      {isSaving 
                        ? `-₹${Math.abs(option.cost_difference).toLocaleString()}` 
                        : `+₹${option.cost_difference.toLocaleString()}`}
                    </span>
                    <ChevronRight size={16} className={isSelected ? 'text-white' : 'text-paper-400'} />
                  </div>
                </button>
              );
            })}
          </div>

          {/* Option Comparison details */}
          {currentOption && (
            <div className="lg:col-span-7 bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6 shadow-sm flex flex-col gap-6">
              
              <div>
                <h3 className="text-lg font-bold text-paper-900 dark:text-white mb-2">{currentOption.label}</h3>
                <p className="text-xs text-paper-500 dark:text-paper-400 leading-relaxed">
                  {currentOption.description}
                </p>
              </div>

              {/* Side by side comparison */}
              <div className="border border-paper-100 dark:border-paper-700 rounded-xl overflow-hidden text-xs">
                <div className="grid grid-cols-12 bg-paper-50 dark:bg-paper-900/40 p-3 font-bold text-paper-500 uppercase tracking-wider border-b border-paper-100 dark:border-paper-700">
                  <div className="col-span-6">Category</div>
                  <div className="col-span-3 text-right">Current</div>
                  <div className="col-span-3 text-right text-marigold-600 dark:text-marigold-400">Optimized</div>
                </div>

                <div className="divide-y divide-paper-100 dark:divide-paper-700/60 font-medium">
                  {/* Transportation */}
                  <div className="grid grid-cols-12 p-3 items-center">
                    <div className="col-span-6 text-paper-600 dark:text-paper-400">Transportation</div>
                    <div className="col-span-3 text-right">₹{data.allocations.transport_cost.toLocaleString()}</div>
                    <div className="col-span-3 text-right font-bold text-paper-900 dark:text-white">
                      ₹{currentOption.new_allocation.transport_cost.toLocaleString()}
                    </div>
                  </div>

                  {/* Accommodation */}
                  <div className="grid grid-cols-12 p-3 items-center">
                    <div className="col-span-6 text-paper-600 dark:text-paper-400">Lodging (Hotel)</div>
                    <div className="col-span-3 text-right">₹{data.allocations.hotel_cost.toLocaleString()}</div>
                    <div className="col-span-3 text-right font-bold text-paper-900 dark:text-white">
                      ₹{currentOption.new_allocation.hotel_cost.toLocaleString()}
                    </div>
                  </div>

                  {/* Food */}
                  <div className="grid grid-cols-12 p-3 items-center">
                    <div className="col-span-6 text-paper-600 dark:text-paper-400">Food & Dining</div>
                    <div className="col-span-3 text-right">₹{data.allocations.food_cost.toLocaleString()}</div>
                    <div className="col-span-3 text-right font-bold text-paper-900 dark:text-white">
                      ₹{currentOption.new_allocation.food_cost.toLocaleString()}
                    </div>
                  </div>

                  {/* Activities */}
                  <div className="grid grid-cols-12 p-3 items-center">
                    <div className="col-span-6 text-paper-600 dark:text-paper-400">Activities</div>
                    <div className="col-span-3 text-right">₹{data.allocations.activities_cost.toLocaleString()}</div>
                    <div className="col-span-3 text-right font-bold text-paper-900 dark:text-white">
                      ₹{currentOption.new_allocation.activities_cost.toLocaleString()}
                    </div>
                  </div>

                  {/* Local Trans */}
                  <div className="grid grid-cols-12 p-3 items-center">
                    <div className="col-span-6 text-paper-600 dark:text-paper-400">Local Travel</div>
                    <div className="col-span-3 text-right">₹{data.allocations.local_transport_cost.toLocaleString()}</div>
                    <div className="col-span-3 text-right font-bold text-paper-900 dark:text-white">
                      ₹{currentOption.new_allocation.local_transport_cost.toLocaleString()}
                    </div>
                  </div>

                  {/* Taxes */}
                  <div className="grid grid-cols-12 p-3 items-center">
                    <div className="col-span-6 text-paper-600 dark:text-paper-400">Taxes & Fees</div>
                    <div className="col-span-3 text-right">₹{data.allocations.taxes_fees_cost.toLocaleString()}</div>
                    <div className="col-span-3 text-right font-bold text-paper-900 dark:text-white">
                      ₹{currentOption.new_allocation.taxes_fees_cost.toLocaleString()}
                    </div>
                  </div>

                  {/* Emergency */}
                  <div className="grid grid-cols-12 p-3 items-center">
                    <div className="col-span-6 text-paper-600 dark:text-paper-400">Emergency Reserve</div>
                    <div className="col-span-3 text-right">₹{data.allocations.emergency_reserve.toLocaleString()}</div>
                    <div className="col-span-3 text-right font-bold text-paper-900 dark:text-white">
                      ₹{currentOption.new_allocation.emergency_reserve.toLocaleString()}
                    </div>
                  </div>

                  {/* Total */}
                  <div className="grid grid-cols-12 p-3 bg-paper-50 dark:bg-paper-900/30 items-center font-bold text-sm">
                    <div className="col-span-6 text-paper-700 dark:text-paper-300">Total Simulated Cost</div>
                    <div className="col-span-3 text-right">₹{data.current_cost.toLocaleString()}</div>
                    <div className="col-span-3 text-right text-marigold-600 dark:text-marigold-400">
                      ₹{
                        (
                          currentOption.new_allocation.transport_cost +
                          currentOption.new_allocation.hotel_cost +
                          currentOption.new_allocation.food_cost +
                          currentOption.new_allocation.activities_cost +
                          currentOption.new_allocation.local_transport_cost +
                          currentOption.new_allocation.taxes_fees_cost +
                          currentOption.new_allocation.emergency_reserve
                        ).toLocaleString()
                      }
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-4 justify-between items-center border-t border-paper-100 dark:border-paper-700 pt-4">
                <div className="flex items-center gap-2">
                  <TrendingDown className="text-emerald-500 animate-pulse" />
                  <span className="text-xs font-medium text-paper-500 dark:text-paper-400">
                    {currentOption.cost_difference < 0 
                      ? `Applying will save INR ${Math.abs(currentOption.cost_difference).toLocaleString()}`
                      : `Applying will cost INR ${currentOption.cost_difference.toLocaleString()} more`}
                  </span>
                </div>
                
                <button
                  onClick={handleApplyOptimization}
                  disabled={applying || success}
                  className="inline-flex items-center gap-1.5 bg-marigold-600 hover:bg-marigold-500 text-white font-bold px-5 py-2.5 rounded-xl text-xs transition-all shadow-md shadow-marigold-600/10 disabled:opacity-50"
                >
                  {applying ? (
                    <>
                      <Loader size={14} className="animate-spin" />
                      Applying changes...
                    </>
                  ) : (
                    <>
                      <Check size={14} />
                      Apply Strategy
                    </>
                  )}
                </button>
              </div>

            </div>
          )}

        </div>
      )}

    </div>
  );
};



