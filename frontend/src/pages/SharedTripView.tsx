import React, { useEffect, useState } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import { TimelineItinerary } from '../components/TimelineItinerary';
import { TripChecklist } from '../components/TripChecklist';
import { 
  Calendar, 
  MapPin, 
  Wallet, 
  Compass, 
  Loader, 
  AlertCircle, 
  Leaf, 
  CloudSun,
  Building,
  Plane,
  Train,
  Utensils,
  Camera,
  Percent,
  LifeBuoy
} from 'lucide-react';

interface Destination {
  id: number;
  name: string;
  state: string;
  category: string;
  description: string;
  best_season: string;
  weather_intelligence?: {
    current_season: string;
    best_season: string;
    season_rating: string;
    crowd_level: string;
    temperature_range: string;
    rain_probability: string;
    recommendation: string;
  };
}

interface BudgetAllocation {
  transport_cost: number;
  hotel_cost: number;
  food_cost: number;
  activities_cost: number;
  local_transport_cost: number;
  taxes_fees_cost: number;
  emergency_reserve: number;
}

interface CarbonFootprint {
  transport_mode: string;
  co2_emissions: number;
  carbon_rating: string;
  eco_score: number;
  alternative_savings: number;
}

interface Trip {
  id: number;
  budget: number;
  days: number;
  travelers_count: number;
  travel_type: string;
  comfort_score: number;
  total_estimated_cost: number;
  hotel_tier: string;
  transport_mode: string;
  status: string;
  start_date?: string;
  destination: Destination;
  itineraries: any[];
  budget_allocation?: BudgetAllocation;
  carbon_footprint?: CarbonFootprint;
  packing_items: any[];
}

export const SharedTripView: React.FC = () => {
  usePageTitle('Shared Trip | BudgetBound');
  const { shareToken } = useParams<{ shareToken: string }>();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedDays, setExpandedDays] = useState<Record<number, boolean>>({});

  useEffect(() => {
    const fetchSharedTrip = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/api/trips/share/${shareToken}`);
        setTrip(response.data);
        
        // Expand all days by default for public viewing
        const allExpanded: Record<number, boolean> = {};
        response.data.itineraries.forEach((it: any) => {
          allExpanded[it.day_number] = true;
        });
        setExpandedDays(allExpanded);
      } catch (err: any) {
        console.error(err);
        setError(err.response?.data?.detail || 'This travel plan is set to private or does not exist.');
      } finally {
        setLoading(false);
      }
    };

    if (shareToken) {
      fetchSharedTrip();
    }
  }, [shareToken]);

  const toggleDay = (dayNumber: number) => {
    setExpandedDays(prev => ({ ...prev, [dayNumber]: !prev[dayNumber] }));
  };

  const getCategoryGradient = (category: string) => {
    const cat = category.toLowerCase();
    if (cat.includes('beach')) {
      return 'from-amber-400 via-orange-500 to-blue-600';
    }
    if (cat.includes('nature') || cat.includes('hills')) {
      return 'from-emerald-400 via-teal-500 to-petrol-700';
    }
    if (cat.includes('religious') || cat.includes('temple')) {
      return 'from-orange-400 via-red-500 to-amber-600';
    }
    return 'from-marigold-500 via-berry-600 to-petrol-700';
  };

  const getWeatherRatingBadgeClass = (rating: string) => {
    switch (rating) {
      case 'Excellent':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/30';
      case 'Good':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-400 border border-blue-200 dark:border-blue-900/30';
      case 'Fair':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400 border border-amber-200 dark:border-amber-900/30';
      case 'Avoid':
        return 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400 border border-rose-200 dark:border-rose-900/30';
      default:
        return 'bg-paper-100 text-paper-700';
    }
  };

  const getCarbonBadgeClass = (rating: string) => {
    if (rating === 'Eco Friendly') {
      return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-300';
    }
    if (rating === 'Moderate') {
      return 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400 border border-amber-300';
    }
    return 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400 border border-rose-300';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-paper-50 dark:bg-paper-900 flex flex-col items-center justify-center text-paper-500 gap-4">
        <Loader className="h-10 w-10 text-marigold-500 animate-spin" />
        <span className="text-sm font-semibold">Retrieving shared travel plan...</span>
      </div>
    );
  }

  if (error || !trip) {
    return (
      <div className="min-h-screen bg-paper-50 dark:bg-paper-900 flex flex-col items-center justify-center p-6 text-center">
        <div className="max-w-md bg-paper-50 dark:bg-paper-800 p-8 rounded-3xl border border-paper-200 dark:border-paper-700 shadow-xl space-y-4">
          <AlertCircle className="h-14 w-14 text-rose-500 mx-auto" />
          <h2 className="text-xl font-extrabold text-paper-900 dark:text-white">Plan Access Denied</h2>
          <p className="text-xs text-paper-500 dark:text-paper-400 leading-relaxed">
            {error || 'This itinerary is currently private. Please ask the owner to enable public sharing.'}
          </p>
          <div className="pt-2">
            <Link 
              to="/dashboard" 
              className="inline-flex items-center gap-1.5 bg-marigold-600 hover:bg-marigold-500 text-white font-bold px-6 py-2.5 rounded-xl text-xs transition-all shadow-md"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const { destination } = trip;
  const weather = destination.weather_intelligence;
  const carbon = trip.carbon_footprint;
  const alloc = trip.budget_allocation;

  return (
    <div className="min-h-screen bg-paper-50 dark:bg-paper-900 text-paper-900 dark:text-paper-100 flex flex-col items-center pb-12">
      
      {/* Category Gradient Header Banner */}
      <div className={`w-full h-64 bg-gradient-to-r ${getCategoryGradient(destination.category)} relative overflow-hidden flex flex-col justify-end p-8 text-white shadow`}>
        <div className="absolute top-0 right-0 w-80 h-80 bg-paper-50/10 rounded-full blur-3xl pointer-events-none" />
        <div className="max-w-5xl w-full mx-auto space-y-2 relative z-10">
          <div className="flex gap-2 items-center">
            <span className="text-[10px] bg-paper-50/20 backdrop-blur-md px-2 py-0.5 rounded-full uppercase font-bold tracking-wider">
              {destination.category}
            </span>
            <span className="text-[10px] bg-marigold-600/60 backdrop-blur-md px-2 py-0.5 rounded-full uppercase font-bold tracking-wider">
              Public Shared Plan
            </span>
          </div>
          <span className="text-xs font-bold uppercase tracking-wider text-paper-200 block">{destination.state}</span>
          <h1 className="text-4xl font-extrabold tracking-tight drop-shadow-md">{destination.name}</h1>
          <p className="text-xs text-paper-100/90 max-w-xl font-medium leading-relaxed drop-shadow-sm">
            {destination.description}
          </p>
        </div>
      </div>

      {/* Main Core Container */}
      <div className="max-w-5xl w-full px-6 md:px-8 mt-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left column: Itinerary */}
        <div className="lg:col-span-7 space-y-6">
          
          <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-4.5 rounded-2xl shadow-sm">
            <h2 className="text-base font-extrabold text-paper-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <Compass className="text-marigold-500" size={18} />
              Travel Schedule Itinerary
            </h2>
            <p className="text-[11px] text-paper-400 mt-0.5">Explore the daily chronological travel agenda details</p>
          </div>

          <TimelineItinerary
            itineraries={trip.itineraries}
            expandedDays={expandedDays}
            toggleDay={toggleDay}
            className="w-full animate-fade-in"
          />
        </div>

        {/* Right column: Widgets (Cost, Weather, Packing, Carbon) */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* Metadata Card */}
          <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-5 rounded-2xl shadow-sm grid grid-cols-3 gap-4 text-center">
            <div className="space-y-1">
              <span className="text-[10px] text-paper-400 font-bold uppercase block">Budget</span>
              <span className="font-extrabold text-paper-800 dark:text-white">₹{trip.budget.toLocaleString()}</span>
            </div>
            <div className="space-y-1 border-x border-paper-100 dark:border-paper-700">
              <span className="text-[10px] text-paper-400 font-bold uppercase block">Days</span>
              <span className="font-extrabold text-paper-800 dark:text-white">{trip.days} Days</span>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-paper-400 font-bold uppercase block">Travelers</span>
              <span className="font-extrabold text-paper-800 dark:text-white">{trip.travelers_count} People</span>
            </div>
          </div>

          {/* Weather Intelligence Widget */}
          {weather && (
            <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-5 rounded-2xl shadow-sm space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-extrabold text-paper-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                  <CloudSun size={16} className="text-marigold-500" />
                  Weather & Season Intelligence
                </h3>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${getWeatherRatingBadgeClass(weather.season_rating)}`}>
                  {weather.season_rating}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs bg-paper-50 dark:bg-paper-900/40 p-3 rounded-xl border border-paper-100 dark:border-paper-800">
                <div className="space-y-0.5">
                  <span className="text-paper-400 font-semibold block">Current Season</span>
                  <span className="font-bold text-paper-800 dark:text-white">{weather.current_season}</span>
                </div>
                <div className="space-y-0.5">
                  <span className="text-paper-400 font-semibold block">Temp Range</span>
                  <span className="font-bold text-paper-800 dark:text-white">{weather.temperature_range}</span>
                </div>
                <div className="space-y-0.5">
                  <span className="text-paper-400 font-semibold block">Crowd Level</span>
                  <span className="font-bold text-paper-800 dark:text-white">{weather.crowd_level}</span>
                </div>
                <div className="space-y-0.5">
                  <span className="text-paper-400 font-semibold block">Rain Probability</span>
                  <span className="font-bold text-paper-800 dark:text-white">{weather.rain_probability}</span>
                </div>
              </div>

              <p className="text-xs text-paper-500 dark:text-paper-400 leading-relaxed italic border-l-2 border-marigold-400 pl-3">
                {weather.recommendation}
              </p>
            </div>
          )}

          {/* Carbon Footprint Widget */}
          {carbon && (
            <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-5 rounded-2xl shadow-sm space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-extrabold text-paper-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                  <Leaf size={16} className="text-emerald-500" />
                  Carbon Footprint Impact
                </h3>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${getCarbonBadgeClass(carbon.carbon_rating)}`}>
                  {carbon.carbon_rating}
                </span>
              </div>

              <div className="flex items-center justify-between p-3.5 bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-800 rounded-xl">
                <div className="flex items-center gap-2.5">
                  {carbon.transport_mode === 'Flight' ? <Plane size={16} className="text-rose-500" /> : <Train size={16} className="text-emerald-500" />}
                  <span className="text-xs font-bold text-paper-800 dark:text-paper-300">
                    CO₂ Impact ({carbon.transport_mode})
                  </span>
                </div>
                <span className="text-sm font-extrabold text-paper-900 dark:text-white">
                  {carbon.co2_emissions} kg
                </span>
              </div>

              <div className="text-[11px] text-paper-500 dark:text-paper-400 leading-normal flex items-start gap-2 bg-emerald-50/20 dark:bg-emerald-950/10 border border-emerald-100/40 p-3 rounded-xl">
                <Leaf size={14} className="text-emerald-500 shrink-0 mt-0.5" fill="currentColor" />
                <span>
                  {carbon.transport_mode === 'Flight' 
                    ? `Choosing train instead of flight for this segment reduces emissions by ${carbon.alternative_savings} kg.`
                    : `Eco-friendly choice! Traveling by train instead of flight saved an estimated ${carbon.alternative_savings} kg of CO₂.`
                  }
                </span>
              </div>
            </div>
          )}

          {/* Budget Breakdown Summary */}
          {alloc && (
            <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-5 rounded-2xl shadow-sm space-y-4">
              <h3 className="text-sm font-extrabold text-paper-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                <Wallet size={16} className="text-marigold-500" />
                Allocated Budget Breakdown
              </h3>

              <div className="flex flex-col gap-3 text-xs text-paper-700 dark:text-paper-400">
                <div className="flex justify-between">
                  <span className="flex items-center gap-2"><Plane size={14} /> Transportation</span>
                  <span className="font-bold text-paper-800 dark:text-white">₹{alloc.transport_cost.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="flex items-center gap-2"><Building size={14} /> Accommodations</span>
                  <span className="font-bold text-paper-800 dark:text-white">₹{alloc.hotel_cost.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="flex items-center gap-2"><Utensils size={14} /> Food & Dining</span>
                  <span className="font-bold text-paper-800 dark:text-white">₹{alloc.food_cost.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="flex items-center gap-2"><Camera size={14} /> Sightseeing / Sights</span>
                  <span className="font-bold text-paper-800 dark:text-white">₹{alloc.activities_cost.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="flex items-center gap-2"><Percent size={14} /> Taxes & Booking Fees</span>
                  <span className="font-bold text-paper-800 dark:text-white">₹{alloc.taxes_fees_cost.toLocaleString()}</span>
                </div>
                <div className="flex justify-between border-t border-paper-100 dark:border-paper-700 pt-2 font-bold text-paper-800 dark:text-white">
                  <span className="flex items-center gap-2"><LifeBuoy size={14} /> Total Estimated Cost</span>
                  <span>₹{trip.total_estimated_cost.toLocaleString()}</span>
                </div>
              </div>
            </div>
          )}

          {/* Checklist Widget */}
          <TripChecklist
            tripId={trip.id}
            readOnly={true}
            initialItems={trip.packing_items}
          />

        </div>

      </div>

    </div>
  );
};



