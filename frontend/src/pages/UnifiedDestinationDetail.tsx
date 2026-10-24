import React, { useEffect, useState } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom';
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
  CloudSun,
  Star,
  Zap,
  MapPinIcon
} from 'lucide-react';

interface SeededDestination {
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
  weather_intelligence?: any;
}

interface LiveDestination {
  place_id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  rating: number | null;
  user_rating_count: number | null;
  administrative_area: string;
  data_source: string;
}

interface UnifiedDetail {
  source: 'seeded' | 'live';
  destination: SeededDestination | LiveDestination;
  nearby_attractions?: any[];
  category?: string;
}

export const UnifiedDestinationDetail: React.FC = () => {
  usePageTitle('Destination Details | BudgetBound');
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [detail, setDetail] = useState<UnifiedDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Determine source from query params or ID
  const source = searchParams.get('source') || 'seeded';
  const lat = searchParams.get('lat');
  const lon = searchParams.get('lon');
  const category = searchParams.get('category') || 'Travel';

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        setLoading(true);
        let result: UnifiedDetail;

        if (source === 'live' && lat && lon) {
          // Fetch live destination details from Geoapify
          const response = await api.get(`/api/destinations-live/detail/${id}`, {
            params: { latitude: lat, longitude: lon }
          });
          
          result = {
            source: 'live',
            destination: {
              place_id: id,
              name: searchParams.get('name') || 'Unknown',
              address: searchParams.get('address') || '',
              latitude: parseFloat(lat),
              longitude: parseFloat(lon),
              rating: searchParams.get('rating') ? parseFloat(searchParams.get('rating')!) : null,
              user_rating_count: searchParams.get('reviews') ? parseInt(searchParams.get('reviews')!) : null,
              administrative_area: searchParams.get('state') || '',
              data_source: 'geoapify'
            } as LiveDestination,
            nearby_attractions: response.data.nearby_attractions || [],
            category
          };
        } else {
          // Fetch seeded destination details
          const response = await api.get(`/api/destinations/${id}`);
          result = {
            source: 'seeded',
            destination: response.data,
            category: response.data.category
          };
        }

        setDetail(result);
      } catch (err: any) {
        console.error(err);
        setError(err.response?.data?.detail || 'Failed to load destination details.');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchDetail();
    }
  }, [id, source, lat, lon, category]);

  const handlePlanHere = () => {
    if (!detail) return;
    
    const dest = detail.destination;
    const name = 'name' in dest ? dest.name : dest.name;
    const coords = 'latitude' in dest ? { lat: dest.latitude, lon: dest.longitude } : null;

    sessionStorage.setItem('prefilled_planner', JSON.stringify({
      startingCity: 'Your City',
      budget: 25000,
      days: 4,
      travelType: detail.category || 'Travel',
      travelersCount: 1,
      destName: name,
      destinationId: detail.source === 'seeded' ? (dest as SeededDestination).id : null,
      liveDestinationId: detail.source === 'live' ? (dest as LiveDestination).place_id : null,
      coordinates: coords,
      flowMode: 'plan'
    }));
    navigate('/planner');
  };

  if (loading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center text-paper-500 dark:text-paper-400 gap-4">
        <Loader className="h-10 w-10 text-marigold-500 animate-spin" />
        <span className="text-sm font-semibold">Loading destination details...</span>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 rounded-2xl flex flex-col items-start gap-3">
        <div className="flex items-center gap-2">
          <AlertCircle size={24} />
          <h3 className="font-bold">Error loading destination</h3>
        </div>
        <p className="text-xs">{error || 'Destination not found.'}</p>
        <Link to="/explorer" className="text-xs font-bold underline mt-2 block">
          Return to Explorer
        </Link>
      </div>
    );
  }

  const dest = detail.destination;
  const isSeeded = detail.source === 'seeded';
  const isLive = detail.source === 'live';

  // Prepare display data
  const displayName = 'name' in dest ? dest.name : '';
  const displayState = isSeeded ? (dest as SeededDestination).state : (isLive ? (dest as LiveDestination).administrative_area : '');
  const displayAddress = isLive ? (dest as LiveDestination).address : '';
  const displayRating = isSeeded ? (dest as SeededDestination).rating : isLive ? (dest as LiveDestination).rating : null;
  const displayDescription = isSeeded ? (dest as SeededDestination).description : displayAddress;

  // Get costs if seeded
  const costs = isSeeded ? {
    travel: (dest as SeededDestination).avg_travel_cost,
    hotel: (dest as SeededDestination).avg_hotel_cost,
    food: (dest as SeededDestination).avg_food_cost,
    activity: (dest as SeededDestination).avg_activity_cost
  } : null;

  // Get attractions
  const attractions = isSeeded ? (dest as SeededDestination).attractions : detail.nearby_attractions?.slice(0, 6).map(a => a.name) || [];

  // Generate mock itinerary for seeded destinations
  const mockDays = isSeeded ? [
    {
      day: 1,
      title: 'Arrival & Local Orientation',
      activities: [`Arrival at transit station, check-in to hotel`, `Orientation walk around the main city hub`, `Dinner at a highly rated local culinary spot`]
    },
    {
      day: 2,
      title: 'Sightseeing Highlights',
      activities: [`Guided exploration of ${attractions[0] || 'popular sites'}`, `Lunch including traditional delicacies`, `Evening sunset viewpoint visit at ${attractions[1] || 'scenic spots'}`]
    },
    {
      day: 3,
      title: 'Deeper Exploration',
      activities: [`Tour of the historic ${attractions[2] || 'monumental areas'}`, `Short trek or adventure excursion`, `Leisure time for local shopping and street food tour`]
    },
    {
      day: 4,
      title: 'Souvenirs & Departure',
      activities: [`Morning walk & photography session`, `Last minute shopping at central bazaars`, `Checkout and board return transit`]
    }
  ] : null;

  return (
    <div className="flex flex-col gap-8">

      <TripFlowGuide
        eyebrow="Explore & Plan"
        title="Review destination details before planning"
        description={isLive 
          ? "This is a live destination from Geoapify. View nearby attractions and local information, then send it to the planner to build a full itinerary."
          : "Read the average costs, attractions, and season info first. If it looks right, the button below sends those values to the Budget Planner so you can build a full itinerary around this destination type."
        }
        ctaLabel="Send to planner"
        steps={[
          { title: 'Review the destination', description: 'Check location, attractions, and ratings.' },
          { title: 'Use the plan button', description: 'Send this destination to the Budget Planner.' },
          { title: 'Generate the trip', description: 'Adjust budget and duration, then let the planner build the final trip.' }
        ]}
      />
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <Link 
            to="/explorer" 
            className="inline-flex items-center gap-1.5 text-xs font-bold text-paper-400 hover:text-marigold-600 dark:hover:text-marigold-400 uppercase tracking-widest transition-colors mb-2"
          >
            <ArrowLeft size={14} />
            Back to Explorer
          </Link>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-3xl font-extrabold text-paper-900 dark:text-white">
              {displayName}
            </h1>
            <span className={`text-xs font-bold px-3 py-1 rounded-full uppercase shrink-0 ${
              isLive 
                ? 'bg-blue-100 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 border border-blue-200/50 dark:border-blue-900/50'
                : 'bg-marigold-100 dark:bg-marigold-950/40 text-marigold-700 dark:text-marigold-400'
            }`}>
              {isLive ? 'Live' : detail.category || 'Travel'}
            </span>
          </div>
          <span className="text-sm text-paper-500 dark:text-paper-400 flex items-center gap-1">
            <MapPin size={14} />
            {displayState}{displayState && ', '}India
          </span>
          {displayRating && (
            <span className="text-sm text-amber-600 dark:text-amber-400 flex items-center gap-1">
              <Star size={14} fill="currentColor" />
              {displayRating.toFixed(1)} stars
            </span>
          )}
        </div>

        <button 
          onClick={handlePlanHere}
          className="inline-flex items-center gap-2 bg-marigold-600 hover:bg-marigold-500 text-white font-bold px-6 py-3 rounded-xl text-sm transition-all shadow-md shadow-marigold-600/15"
        >
          <Compass size={16} />
          Plan a Trip Here
        </button>
      </div>

      {/* Live Data Badge */}
      {isLive && (
        <div className="flex items-center gap-2 px-4 py-3 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 rounded-lg">
          <Zap size={14} className="text-blue-600 flex-shrink-0" />
          <p className="text-xs text-blue-700 dark:text-blue-300">
            This is a live destination powered by Geoapify. Location data is current and real-time.
          </p>
        </div>
      )}

      {/* Profile splits */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          
          {/* Description */}
          <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6 shadow-sm">
            <h3 className="font-bold text-paper-800 dark:text-white mb-3">About This Destination</h3>
            <p className="text-paper-600 dark:text-paper-400 text-sm leading-relaxed">
              {displayDescription}
            </p>
          </div>

          {/* Costs (seeded only) */}
          {costs && (
            <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6 shadow-sm">
              <h3 className="font-bold text-paper-800 dark:text-white mb-4">Estimated Average Base Costs</h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-paper-50 dark:bg-paper-900/40 rounded-xl flex flex-col gap-2">
                  <Plane className="text-marigold-500" size={18} />
                  <span className="text-[9px] text-paper-400 font-bold uppercase tracking-wider">Transit Cost</span>
                  <span className="font-extrabold text-sm text-paper-800 dark:text-white">₹{costs.travel.toLocaleString()}</span>
                  <span className="text-[8px] text-paper-400">Round trip base</span>
                </div>

                <div className="p-4 bg-paper-50 dark:bg-paper-900/40 rounded-xl flex flex-col gap-2">
                  <Building className="text-marigold-500" size={18} />
                  <span className="text-[9px] text-paper-400 font-bold uppercase tracking-wider">Lodging Cost</span>
                  <span className="font-extrabold text-sm text-paper-800 dark:text-white">₹{costs.hotel.toLocaleString()}</span>
                  <span className="text-[8px] text-paper-400">Per night stay</span>
                </div>

                <div className="p-4 bg-paper-50 dark:bg-paper-900/40 rounded-xl flex flex-col gap-2">
                  <Utensils className="text-marigold-500" size={18} />
                  <span className="text-[9px] text-paper-400 font-bold uppercase tracking-wider">Food / Day</span>
                  <span className="font-extrabold text-sm text-paper-800 dark:text-white">₹{costs.food.toLocaleString()}</span>
                  <span className="text-[8px] text-paper-400">Meals & beverages</span>
                </div>

                <div className="p-4 bg-paper-50 dark:bg-paper-900/40 rounded-xl flex flex-col gap-2">
                  <Camera className="text-marigold-500" size={18} />
                  <span className="text-[9px] text-paper-400 font-bold uppercase tracking-wider">Activity Fare</span>
                  <span className="font-extrabold text-sm text-paper-800 dark:text-white">₹{costs.activity.toLocaleString()}</span>
                  <span className="text-[8px] text-paper-400">Average entry fee</span>
                </div>
              </div>
            </div>
          )}

          {/* Attractions */}
          {attractions.length > 0 && (
            <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6 shadow-sm">
              <h3 className="font-bold text-paper-800 dark:text-white mb-4">
                {isLive ? 'Nearby Attractions & Places' : 'Curated Local Attractions'}
              </h3>
              <div className="flex flex-col gap-3 font-medium">
                {attractions.map((a, idx) => (
                  <div key={idx} className="flex items-center gap-3 text-paper-600 dark:text-paper-300 text-xs">
                    <div className="h-6 w-6 rounded-md bg-marigold-50 dark:bg-marigold-950/40 flex items-center justify-center font-bold text-marigold-600 dark:text-marigold-400 shrink-0">
                      {idx + 1}
                    </div>
                    <span>{a}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* Right Side */}
        <div className="lg:col-span-5 flex flex-col gap-6">

          {/* Location Coordinates (live only) */}
          {isLive && (
            <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6 shadow-sm">
              <h3 className="font-bold text-paper-800 dark:text-white mb-4 flex items-center gap-2">
                <MapPinIcon size={16} className="text-marigold-500" />
                Location Coordinates
              </h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-paper-50 dark:bg-paper-900/40 rounded-xl">
                  <span className="text-[9px] text-paper-400 font-bold uppercase">Latitude</span>
                  <span className="font-mono font-bold text-paper-800 dark:text-white block">{(dest as LiveDestination).latitude.toFixed(4)}</span>
                </div>
                <div className="p-4 bg-paper-50 dark:bg-paper-900/40 rounded-xl">
                  <span className="text-[9px] text-paper-400 font-bold uppercase">Longitude</span>
                  <span className="font-mono font-bold text-paper-800 dark:text-white block">{(dest as LiveDestination).longitude.toFixed(4)}</span>
                </div>
              </div>
              
              {(dest as LiveDestination).user_rating_count && (
                <p className="text-xs text-paper-500 dark:text-paper-400 mt-4">
                  {(dest as LiveDestination).user_rating_count} reviews on Geoapify
                </p>
              )}
            </div>
          )}

          {/* Sample Itinerary (seeded only) */}
          {mockDays && (
            <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6 shadow-sm">
              <h3 className="font-bold text-paper-800 dark:text-white mb-4 flex items-center gap-1.5">
                <Calendar size={18} className="text-marigold-500" />
                Sample 4-Day Itinerary Plan
              </h3>

              <div className="flex flex-col gap-5 text-xs">
                {mockDays.map((d) => (
                  <div key={d.day} className="flex gap-4">
                    <div className="flex flex-col items-center shrink-0">
                      <div className="h-6 w-6 rounded-full bg-marigold-600 text-white font-bold flex items-center justify-center text-[10px]">
                        D{d.day}
                      </div>
                      {d.day < 4 && <div className="w-0.5 bg-paper-200 dark:bg-paper-700 flex-1 my-1" />}
                    </div>

                    <div className="space-y-2 pb-2">
                      <h4 className="font-bold text-paper-800 dark:text-white">{d.title}</h4>
                      <ul className="list-disc pl-4 text-paper-500 dark:text-paper-400 space-y-1.5">
                        {d.activities.map((act, actIdx) => (
                          <li key={actIdx} className="leading-relaxed">{act}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

      </div>

    </div>
  );
};
