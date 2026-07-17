import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { TripFlowGuide } from '../components/TripFlowGuide';
import { 
  ArrowLeft, 
  MapPin, 
  Loader, 
  AlertCircle, 
  Compass,
  Plane,
  Building,
  Utensils,
  Camera,
  Calendar,
  CloudSun
} from 'lucide-react';

interface Destination {
  id: number;
  name: string;
  state: string;
  avg_travel_cost: number;
  avg_hotel_cost: number;
  avg_food_cost: number;
  avg_activity_cost: number;
  rating: number;
  category: string;
  best_season: string;
  description: string;
  attractions: string[];
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

export const DestinationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [dest, setDest] = useState<Destination | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/api/destinations/${id}`);
        setDest(response.data);
      } catch (err: any) {
        console.error(err);
        setError('Failed to load destination profile details.');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchDetail();
    }
  }, [id]);

  const handlePlanHere = () => {
    if (!dest) return;
    
    // Set Prefilled session storage
    sessionStorage.setItem('prefilled_planner', JSON.stringify({
      startingCity: 'Your City',
      budget: 25000,
      days: 4,
      travelType: dest.category,
      travelersCount: 1,
      destName: dest.name,
      destinationId: dest.id,
      flowMode: 'plan'
    }));
    navigate('/planner');
  };

  if (loading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center text-slate-500 dark:text-slate-400 gap-4">
        <Loader className="h-10 w-10 text-violet-500 animate-spin" />
        <span className="text-sm font-semibold">Retrieving destination records...</span>
      </div>
    );
  }

  if (error || !dest) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 rounded-2xl flex flex-col items-start gap-3">
        <div className="flex items-center gap-2">
          <AlertCircle size={24} />
          <h3 className="font-bold">Error loading profile</h3>
        </div>
        <p className="text-xs">{error || 'Destination not found.'}</p>
        <Link to="/explorer" className="text-xs font-bold underline mt-2 block">
          Return to Explorer
        </Link>
      </div>
    );
  }

  // Generate a mock itinerary for details view
  const mockDays = [
    {
      day: 1,
      title: 'Arrival & Local Orientation',
      activities: [`Arrival at transit station, check-in to hotel`, `Orientation walk around the main city hub`, `Dinner at a highly rated local culinary spot`]
    },
    {
      day: 2,
      title: 'Sightseeing Highlights',
      activities: [`Guided exploration of ${dest.attractions[0] || 'popular sites'}`, `Lunch including traditional delicacies`, `Evening sunset viewpoint visit at ${dest.attractions[1] || 'scenic spots'}`]
    },
    {
      day: 3,
      title: 'Deeper Exploration',
      activities: [`Tour of the historic ${dest.attractions[2] || 'monumental areas'}`, `Short trek or adventure excursion`, `Leisure time for local shopping and street food tour`]
    },
    {
      day: 4,
      title: 'Souvenirs & Departure',
      activities: [`Morning walk & photography session`, `Last minute shopping at central bazaars`, `Checkout and board return transit`]
    }
  ];

  return (
    <div className="flex flex-col gap-8">

      <TripFlowGuide
        eyebrow="One destination, one shortcut"
        title="This page is for inspecting a destination before you plan it"
        description="Read the average costs, attractions, and season info first. If it looks right, the button below sends those values to the Budget Planner so you can build a full itinerary around this destination type."
        ctaLabel="Send this to planner"
        steps={[
          { title: 'Review the destination', description: 'Check costs, attractions, and the best season before you commit.' },
          { title: 'Use the plan button', description: 'Plan Itinerary Here pre-fills the planner with this destination category.' },
          { title: 'Generate the trip', description: 'Adjust budget and duration, then let the planner build the final trip.' }
        ]}
      />
      
      {/* Header back */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <Link 
            to="/explorer" 
            className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-violet-600 dark:hover:text-violet-400 uppercase tracking-widest transition-colors mb-2"
          >
            <ArrowLeft size={14} />
            Back to Explorer
          </Link>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {dest.name}
            </h1>
            <span className="bg-violet-100 dark:bg-violet-950/40 text-violet-700 dark:text-violet-400 text-xs font-bold px-3 py-1 rounded-full uppercase shrink-0">
              {dest.category}
            </span>
          </div>
          <span className="text-sm text-slate-500 dark:text-slate-400 flex items-center gap-1">
            <MapPin size={14} />
            {dest.state}, India
          </span>
        </div>

        <button 
          onClick={handlePlanHere}
          className="inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white font-bold px-6 py-3 rounded-xl text-sm transition-all shadow-md shadow-violet-600/15"
        >
          <Compass size={16} />
          Plan Itinerary Here
        </button>
      </div>

      {/* Profile splits */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side: General profile, costs and attractions */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          
          {/* Main Description */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
            <h3 className="font-bold text-slate-800 dark:text-white mb-3">Overview</h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed mb-6">
              {dest.description}
            </p>

            <div className="flex items-center gap-2.5 p-3.5 bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800 rounded-xl text-xs font-semibold">
              <CloudSun className="text-violet-500 shrink-0" size={18} />
              <span className="text-slate-500 dark:text-slate-400">Best Season to Visit:</span>
              <span className="text-slate-800 dark:text-white font-bold">{dest.best_season}</span>
            </div>
          </div>

          {/* Average Baseline Costs Grid */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
            <h3 className="font-bold text-slate-800 dark:text-white mb-4">Estimated Average Base Costs</h3>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              
              <div className="p-4 bg-slate-50 dark:bg-slate-900/40 rounded-xl flex flex-col gap-2">
                <Plane className="text-violet-500" size={18} />
                <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">Transit Cost</span>
                <span className="font-extrabold text-sm text-slate-800 dark:text-white">₹{dest.avg_travel_cost.toLocaleString()}</span>
                <span className="text-[8px] text-slate-400">Round trip base</span>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-900/40 rounded-xl flex flex-col gap-2">
                <Building className="text-violet-500" size={18} />
                <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">Lodging Cost</span>
                <span className="font-extrabold text-sm text-slate-800 dark:text-white">₹{dest.avg_hotel_cost.toLocaleString()}</span>
                <span className="text-[8px] text-slate-400">Per night stay</span>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-900/40 rounded-xl flex flex-col gap-2">
                <Utensils className="text-violet-500" size={18} />
                <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">Food / Day</span>
                <span className="font-extrabold text-sm text-slate-800 dark:text-white">₹{dest.avg_food_cost.toLocaleString()}</span>
                <span className="text-[8px] text-slate-400">Meals & beverages</span>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-900/40 rounded-xl flex flex-col gap-2">
                <Camera className="text-violet-500" size={18} />
                <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">Activity Fare</span>
                <span className="font-extrabold text-sm text-slate-800 dark:text-white">₹{dest.avg_activity_cost.toLocaleString()}</span>
                <span className="text-[8px] text-slate-400">Average entry fee</span>
              </div>

            </div>
          </div>

          {/* Attractions */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
            <h3 className="font-bold text-slate-800 dark:text-white mb-4">Curated Local Attractions</h3>
            <div className="flex flex-col gap-3 font-medium">
              {dest.attractions.map((a, idx) => (
                <div key={idx} className="flex items-center gap-3 text-slate-600 dark:text-slate-300 text-xs">
                  <div className="h-6 w-6 rounded-md bg-violet-50 dark:bg-violet-950/40 flex items-center justify-center font-bold text-violet-600 dark:text-violet-400 shrink-0">
                    {idx + 1}
                  </div>
                  <span>{a}</span>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Side: Sample Itinerary & Weather */}
        <div className="lg:col-span-5 flex flex-col gap-6">

          {/* Weather Intelligence Widget */}
          {dest.weather_intelligence && (
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-extrabold text-slate-850 dark:text-white uppercase tracking-wider flex items-center gap-2">
                  <CloudSun size={16} className="text-violet-500" />
                  Season Intelligence
                </h3>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  dest.weather_intelligence.season_rating === 'Excellent' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200/30' :
                  dest.weather_intelligence.season_rating === 'Good' ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-400 border border-blue-200/30' :
                  dest.weather_intelligence.season_rating === 'Fair' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400 border border-amber-200/30' :
                  'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400 border border-rose-200/30'
                }`}>
                  {dest.weather_intelligence.season_rating}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3.5 text-xs bg-slate-50 dark:bg-slate-900/40 p-3 rounded-xl border border-slate-100 dark:border-slate-800 font-bold">
                <div className="space-y-0.5">
                  <span className="text-[10px] text-slate-400 block uppercase">Current Season</span>
                  <span className="text-slate-800 dark:text-white">{dest.weather_intelligence.current_season}</span>
                </div>
                <div className="space-y-0.5">
                  <span className="text-[10px] text-slate-400 block uppercase">Temp Range</span>
                  <span className="text-slate-800 dark:text-white">{dest.weather_intelligence.temperature_range}</span>
                </div>
                <div className="space-y-0.5">
                  <span className="text-[10px] text-slate-400 block uppercase">Crowd Density</span>
                  <span className="text-slate-800 dark:text-white">{dest.weather_intelligence.crowd_level}</span>
                </div>
                <div className="space-y-0.5">
                  <span className="text-[10px] text-slate-400 block uppercase">Rain Chance</span>
                  <span className="text-slate-800 dark:text-white">{dest.weather_intelligence.rain_probability}</span>
                </div>
              </div>

              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed italic border-l-2 border-violet-400 pl-3">
                {dest.weather_intelligence.recommendation}
              </p>
            </div>
          )}

          {/* Sample Itinerary */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
            <h3 className="font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-1.5">
              <Calendar size={18} className="text-violet-500" />
              Sample 4-Day Itinerary Plan
            </h3>

            <div className="flex flex-col gap-5 text-xs">
              {mockDays.map((d) => (
                <div key={d.day} className="flex gap-4">
                  {/* Timeline bar */}
                  <div className="flex flex-col items-center shrink-0">
                    <div className="h-6 w-6 rounded-full bg-violet-600 text-white font-bold flex items-center justify-center text-[10px]">
                      D{d.day}
                    </div>
                    {d.day < 4 && <div className="w-0.5 bg-slate-200 dark:bg-slate-700 flex-1 my-1" />}
                  </div>

                  <div className="space-y-2 pb-2">
                    <h4 className="font-bold text-slate-800 dark:text-white">{d.title}</h4>
                    <ul className="list-disc pl-4 text-slate-500 dark:text-slate-400 space-y-1.5">
                      {d.activities.map((act, actIdx) => (
                        <li key={actIdx} className="leading-relaxed">{act}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
