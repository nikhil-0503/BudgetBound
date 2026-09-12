import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { DocumentManager } from '../components/DocumentManager';
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
  Map,
  Share2,
  CloudSun,
  Leaf
} from 'lucide-react';
import { LocationPickerModal } from '../components/LocationPickerModal';
import { BudgetHealthMeter } from '../components/BudgetHealthMeter';
import { RecommendationExplainability } from '../components/RecommendationExplainability';
import { BudgetAllocationEditor } from '../components/BudgetAllocationEditor';
import { TimelineItinerary } from '../components/TimelineItinerary';
import { TripChecklist } from '../components/TripChecklist';
import { ShareModal } from '../components/ShareModal';


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
    weather_intelligence?: {
      current_season: string;
      best_season: string;
      season_rating: string;
      crowd_level: string;
      temperature_range: string;
      rain_probability: string;
      recommendation: string;
    };
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
  breakdown?: any;
  is_public?: boolean;
  share_token?: string | null;
  packing_items?: any[];
  carbon_footprint?: {
    transport_mode: string;
    co2_emissions: number;
    carbon_rating: string;
    eco_score: number;
    alternative_savings: number;
  };
}

interface SearchResult {
  destination: PlanResult['destination'];
  estimated_cost: number;
  budget_fit: number;
  rating: number;
  value_score: number;
  breakdown?: any;
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
  const { user } = useAuth();

  // Pre-fill fields from user profile preferences if available on mount
  React.useEffect(() => {
    const tripIdParam = searchParams.get('tripId');
    if (user && !tripIdParam) {
      if (user.default_starting_city) setStartingCity(user.default_starting_city);
      if (user.default_budget) setBudget(String(user.default_budget));
      if (user.preferred_travel_style) setTravelType(user.preferred_travel_style);
      if (user.preferred_comfort_level !== undefined && user.preferred_comfort_level !== null) {
        setComfortScore(user.preferred_comfort_level);
      }
    }
  }, [user, searchParams]);

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

  const [tripStatus, setTripStatus] = useState<string>("Planned");
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);

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

  // Fetch existing saved trip details if tripId query param is provided
  React.useEffect(() => {
    const tripIdParam = searchParams.get('tripId');
    const fetchSavedTrip = async (id: string) => {
      try {
        setLoading(true);
        const response = await api.get(`/api/trips/${id}`);
        const trip = response.data;
        const alloc = trip.budget_allocation;
        setPlan({
          destination: trip.destination,
          costs: {
            transport_mode: trip.transport_mode,
            hotel_tier: trip.hotel_tier,
            transport_cost: alloc ? alloc.transport_cost : 0,
            hotel_cost: alloc ? alloc.hotel_cost : 0,
            food_cost: alloc ? alloc.food_cost : 0,
            activities_cost: alloc ? alloc.activities_cost : 0,
            local_transport_cost: alloc ? alloc.local_transport_cost : 0,
            taxes_fees_cost: alloc ? alloc.taxes_fees_cost : 0,
            emergency_reserve: alloc ? alloc.emergency_reserve : 0,
            total_estimated_cost: trip.total_estimated_cost
          },
          savings: trip.budget - trip.total_estimated_cost,
          value_score: trip.value_score || 85.0,
          under_budget: trip.total_estimated_cost <= trip.budget,
          itineraries: trip.itineraries,
          budget: trip.budget,
          days: trip.days,
          travelers_count: trip.travelers_count,
          comfort_score: trip.comfort_score,
          travel_type: trip.travel_type,
          breakdown: trip.breakdown || {
            budget_compatibility: 80,
            trip_type_match: 90,
            comfort_match: 85,
            destination_rating: 80,
            duration_suitability: 95,
            explanations: ["Loaded saved travel itinerary from history logs."]
          },
          is_public: trip.is_public,
          share_token: trip.share_token,
          packing_items: trip.packing_items,
          carbon_footprint: trip.carbon_footprint
        });
        setSavedTripId(trip.id);
        setTripStatus(trip.status || "Planned");
        
        setStartingCity('Your City');
        setBudget(String(trip.budget));
        setDays(trip.days);
        setTravelType(trip.travel_type);
        setTravelersCount(trip.travelers_count);
        setComfortScore(trip.comfort_score);
        setFlowMode('plan');
      } catch (err: any) {
        console.error(err);
        setError(err.response?.data?.detail || 'Failed to load saved trip.');
      } finally {
        setLoading(false);
      }
    };
    if (tripIdParam) {
      fetchSavedTrip(tripIdParam);
    }
  }, [searchParams]);

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
  const [expandedSearchIdx, setExpandedSearchIdx] = useState<number | null>(null);

  const toggleDay = (day: number) => {
    setExpandedDays(prev => ({ ...prev, [day]: !prev[day] }));
  };

  const handleAllocationSave = async (updated: any) => {
    if (!plan) return;

    if (savedTripId) {
      try {
        setSavingTrip(true);
        const response = await api.put(`/api/trips/${savedTripId}/allocations`, {
          transport_cost: updated.transport_cost,
          hotel_cost: updated.hotel_cost,
          food_cost: updated.food_cost,
          activities_cost: updated.activities_cost,
          emergency_reserve: updated.emergency_reserve
        });
        setPlan(prev => {
          if (!prev) return null;
          return {
            ...prev,
            costs: {
              ...prev.costs,
              transport_cost: response.data.budget_allocation.transport_cost,
              hotel_cost: response.data.budget_allocation.hotel_cost,
              food_cost: response.data.budget_allocation.food_cost,
              activities_cost: response.data.budget_allocation.activities_cost,
              emergency_reserve: response.data.budget_allocation.emergency_reserve,
              local_transport_cost: response.data.budget_allocation.local_transport_cost,
              taxes_fees_cost: response.data.budget_allocation.taxes_fees_cost,
              total_estimated_cost: response.data.total_estimated_cost
            },
            savings: prev.budget - response.data.total_estimated_cost
          };
        });
      } catch (err) {
        console.error(err);
        alert('Failed to save allocations.');
      } finally {
        setSavingTrip(false);
      }
    } else {
      const total = updated.transport_cost + updated.hotel_cost + updated.food_cost + updated.activities_cost + updated.emergency_reserve;
      setPlan({
        ...plan,
        costs: {
          ...plan.costs,
          transport_cost: updated.transport_cost,
          hotel_cost: updated.hotel_cost,
          food_cost: updated.food_cost,
          activities_cost: updated.activities_cost,
          emergency_reserve: updated.emergency_reserve,
          local_transport_cost: 0,
          taxes_fees_cost: 0,
          total_estimated_cost: total
        },
        savings: plan.budget - total
      });
    }
  };

  const handleAllocationReset = async () => {
    if (!plan) return;
    if (savedTripId) {
      try {
        setSavingTrip(true);
        const response = await api.post(`/api/trips/${savedTripId}/allocations/reset`, {
          starting_city: startingCity
        });
        setPlan(prev => {
          if (!prev) return null;
          return {
            ...prev,
            costs: {
              ...prev.costs,
              transport_cost: response.data.budget_allocation.transport_cost,
              hotel_cost: response.data.budget_allocation.hotel_cost,
              food_cost: response.data.budget_allocation.food_cost,
              activities_cost: response.data.budget_allocation.activities_cost,
              local_transport_cost: response.data.budget_allocation.local_transport_cost,
              taxes_fees_cost: response.data.budget_allocation.taxes_fees_cost,
              emergency_reserve: response.data.budget_allocation.emergency_reserve,
              total_estimated_cost: response.data.total_estimated_cost
            },
            savings: prev.budget - response.data.total_estimated_cost
          };
        });
      } catch (err) {
        console.error(err);
        alert('Failed to reset allocations.');
      } finally {
        setSavingTrip(false);
      }
    } else {
      setLoading(true);
      try {
        const response = await api.post('/api/trips/plan', {
          starting_city: startingCity || 'Bangalore',
          budget: Number(budget),
          days,
          travel_type: travelType,
          travelers_count: travelersCount,
          comfort_score: comfortScore,
          destination_id: selectedDestinationId
        });
        setPlan(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
  };

  const travelTypes = [
    'Nature', 'Adventure', 'Family', 'Religious',
    'Beach', 'City Exploration', 'Romantic', 'Solo'
  ];

  const getComfortLabel = (score: number) => {
    if (score < 30) return { label: 'Budget Traveler', desc: 'Sleeper Trains, local homestays & street eats.', color: 'text-emerald-500' };
    if (score <= 70) return { label: 'Mid-Range Comfort', desc: 'AC Trains / Flights, 3-star hotels & dining.', color: 'text-marigold-500' };
    return { label: 'Luxury Stays', desc: 'Premium Flights, 4/5-star resorts & fine dining.', color: 'text-amber-500' };
  };

  const getValueScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
    if (score >= 50) return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
    return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
  };

  const comfortInfo = getComfortLabel(comfortScore);

  const buildTripPayload = (destinationId?: number | null) => ({
    starting_city: startingCity || 'Bangalore',
    budget: Number(budget),
    days,
    travel_type: travelType,
    travelers_count: travelersCount,
    comfort_score: comfortScore,
    // Use explicit arg first, then fall back to current state
    destination_id: destinationId !== undefined ? destinationId : (selectedDestinationId ?? null)
  });

  const handlePrimaryAction = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setPlan(null);
    setSavedTripId(null);

    const budgetNum = Number(budget);
    if (!budget || isNaN(budgetNum) || budgetNum <= 0) {
      setError('Please enter a valid budget.');
      return;
    }
    if (days < 1 || days > 14) {
      setError('Trip duration must be between 1 and 14 days.');
      return;
    }

    // In discover mode: if no city is provided, fall back to 'Bangalore' silently
    // so the button always fires. Show a soft hint rather than a hard block.
    const effectiveCity = startingCity.trim() || 'Bangalore';
    if (!startingCity.trim() && flowMode === 'discover') {
      setStartingCity('Bangalore');
    }
    // In plan mode, starting city is required for accurate cost estimation
    if (!startingCity.trim() && flowMode === 'plan') {
      setError('Please enter a starting city for accurate cost estimation.');
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
            starting_city: effectiveCity,
            comfort_score: comfortScore
          }
        });
        setSearchResults(response.data);
        setSearchCompleted(true);
      } catch (err: any) {
        console.error(err);
        const detail = err.response?.data?.detail;
        if (err.response?.status === 422) {
          setError(detail || 'No destinations found within your budget. Try increasing the budget or reducing comfort score.');
        } else {
          setError(detail || 'Failed to fetch matching destinations.');
        }
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
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 422) {
        // Backend returned a user-friendly constraint message (e.g. no destination fits budget)
        setError(detail || 'No destination found within your selected budget. Try increasing your budget, reducing trip days, or lowering the comfort score.');
      } else if (status === 404) {
        setError('No destinations found in the database. Please contact support.');
      } else if (status === 500) {
        setError('Unable to generate itinerary. The planning service encountered an error. Please try adjusting your inputs and trying again.');
      } else if (!navigator.onLine) {
        setError('No internet connection. Please check your network and try again.');
      } else {
        setError(detail || 'Unable to generate the trip plan. Please check your inputs and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDestination = async (result: SearchResult) => {
    const destId = result.destination.id;
    const destCategory = result.destination.category;

    setSelectedDestinationId(destId);
    setSelectedDestinationName(result.destination.name);
    setTravelType(destCategory);
    setFlowMode('plan');
    setError(null);
    setSearchCompleted(false);
    setPlan(null);
    setLoading(true);

    // Build payload immediately using the local values "” don't wait for state to flush
    const payload = {
      starting_city: startingCity || 'Bangalore',
      budget: Number(budget),
      days,
      travel_type: destCategory,
      travelers_count: travelersCount,
      comfort_score: comfortScore,
      destination_id: destId
    };

    try {
      const response = await api.post('/api/trips/plan', payload);
      setPlan(response.data);
      setExpandedDays({ 1: true });
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.detail;
      if (err.response?.status === 422) {
        setError(detail || 'This destination exceeds your budget. Try increasing your budget or reducing duration.');
      } else {
        setError(detail || 'Failed to generate a plan for this destination.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTrip = async () => {
    if (!plan || savedTripId) return;
    setSavingTrip(true);
    setError(null);
    try {
      const response = await api.post('/api/trips/', plan);
      setSavedTripId(response.data.id);
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.detail;
      setError(detail || 'Failed to save trip to database. Please try again.');
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



  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="flex flex-col gap-8"
    >

      {/* Title */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-paper-900 dark:text-white flex items-center gap-2">
            <Compass className="text-marigold-600" />
            Trip Flow
          </h1>
          <p className="text-sm text-paper-500 dark:text-paper-400 max-w-3xl mt-1">
            Start by finding good destinations if you are unsure, then continue into the planner to generate the final itinerary. It is the same inputs, but one guided path.
          </p>
        </div>

        <div className="inline-flex rounded-2xl border border-paper-200 dark:border-paper-700 bg-paper-50 dark:bg-paper-800 p-1 shadow-sm self-start">
          <button
            type="button"
            onClick={() => setFlowMode('discover')}
            className={`rounded-xl px-4 py-2 text-xs font-bold transition-all ${flowMode === 'discover'
              ? 'bg-marigold-600 text-white shadow-md shadow-marigold-600/10'
              : 'text-paper-500 dark:text-paper-400 hover:text-paper-900 dark:hover:text-white'
              }`}
          >
            1. Find destinations
          </button>
          <button
            type="button"
            onClick={() => setFlowMode('plan')}
            className={`rounded-xl px-4 py-2 text-xs font-bold transition-all ${flowMode === 'plan'
              ? 'bg-marigold-600 text-white shadow-md shadow-marigold-600/10'
              : 'text-paper-500 dark:text-paper-400 hover:text-paper-900 dark:hover:text-white'
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
        <div className="inline-flex items-center gap-2 self-start rounded-full border border-marigold-200 dark:border-marigold-900/40 bg-marigold-50 dark:bg-marigold-950/30 px-4 py-2 text-xs font-bold text-marigold-700 dark:text-marigold-300">
          Locked destination: {selectedDestinationName}
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

        {/* Left Column: Form Controls */}
        <div className="lg:col-span-4 bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6 shadow-sm">
          <h2 className="text-lg font-bold text-paper-800 dark:text-white mb-6 flex items-center gap-2">
            <Sliders className="text-marigold-500" size={18} />
            Trip Settings
          </h2>

          <form onSubmit={handlePrimaryAction} className="flex flex-col gap-5">
            <div>
              <label className="block text-xs font-semibold text-paper-500 dark:text-paper-400 uppercase tracking-wider mb-2">Starting Location</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <MapPin className="absolute left-3.5 top-3.5 text-paper-400" size={16} />
                  <input
                    type="text"
                    required
                    value={startingCity}
                    onChange={(e) => setStartingCity(e.target.value)}
                    placeholder="e.g. Bangalore, Delhi"
                    className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-marigold-500 text-paper-900 dark:text-white"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => setIsMapModalOpen(true)}
                  className="bg-paper-100 hover:bg-paper-200 dark:bg-paper-800 dark:hover:bg-paper-700 text-paper-700 dark:text-paper-300 px-4 rounded-xl border border-paper-200 dark:border-paper-700 transition-colors flex items-center justify-center"
                  title="Pick on map"
                >
                  <Map size={18} />
                </button>
              </div>
            </div>

            {flowMode === 'plan' && (
              <div>
                <label className="block text-xs font-semibold text-paper-500 dark:text-paper-400 uppercase tracking-wider mb-2">Destination (Optional)</label>
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
                    className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-marigold-500 text-paper-900 dark:text-white appearance-none"
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
                <label className="block text-xs font-semibold text-paper-500 dark:text-paper-400 uppercase tracking-wider mb-2">Budget (INR)</label>
                <div className="relative">
                  <Wallet className="absolute left-3.5 top-3.5 text-paper-400" size={16} />
                  <input
                    type="number"
                    required
                    min={1000}
                    step={1000}
                    value={budget}
                    onChange={(e) => setBudget(e.target.value)}
                    placeholder="20000"
                    className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-marigold-500 text-paper-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-paper-500 dark:text-paper-400 uppercase tracking-wider mb-2">Duration (Days)</label>
                <div className="relative">
                  <Calendar className="absolute left-3.5 top-3.5 text-paper-400" size={16} />
                  <input
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    required
                    value={days}
                    onChange={(e) => {
                      const val = Number(e.target.value.replace(/[^0-9]/g, ''));
                      if (!isNaN(val)) setDays(val);
                    }}
                    placeholder="4"
                    className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-marigold-500 text-paper-900 dark:text-white"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-paper-500 dark:text-paper-400 uppercase tracking-wider mb-2">Travelers Count</label>
                <div className="relative">
                  <Users className="absolute left-3.5 top-3.5 text-paper-400" size={16} />
                  <input
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    required
                    value={travelersCount}
                    onChange={(e) => {
                      const val = Number(e.target.value.replace(/[^0-9]/g, ''));
                      if (!isNaN(val) && val >= 1) setTravelersCount(val);
                    }}
                    placeholder="1"
                    className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-marigold-500 text-paper-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-paper-500 dark:text-paper-400 uppercase tracking-wider mb-2">Trip Category</label>
                <select
                  value={travelType}
                  onChange={(e) => setTravelType(e.target.value)}
                  className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-marigold-500 text-paper-900 dark:text-white appearance-none"
                >
                  {travelTypes.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Comfort vs Budget Slider */}
            <div className="border-t border-paper-100 dark:border-paper-700 pt-4 mt-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-paper-500 dark:text-paper-400 uppercase">Comfort vs Budget</span>
                <span className="text-sm font-bold text-marigold-600 dark:text-marigold-400">{comfortScore}/100</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={comfortScore}
                onChange={(e) => setComfortScore(Number(e.target.value))}
                className="w-full h-2 bg-paper-200 dark:bg-paper-700 rounded-lg appearance-none cursor-pointer accent-marigold-600 focus:outline-none"
              />
              <div className="flex justify-between text-[10px] text-paper-400 font-bold uppercase mt-1">
                <span>Maximum Savings</span>
                <span>Premium Quality</span>
              </div>

              {/* Dynamic slider details */}
              <div className="mt-4 p-3 bg-paper-50 dark:bg-paper-900/50 rounded-xl border border-paper-100 dark:border-paper-800 text-xs">
                <span className={`font-bold block ${comfortInfo.color} mb-1`}>{comfortInfo.label}</span>
                <span className="text-paper-500 dark:text-paper-400 leading-normal">{comfortInfo.desc}</span>
              </div>
            </div>



            {flowMode === 'discover' && (
              <p className="text-xs text-paper-500 dark:text-paper-400 leading-relaxed bg-paper-50 dark:bg-paper-900/50 border border-paper-200 dark:border-paper-700 p-3 rounded-xl">
                This step only compares destinations. Pick one result to continue into the itinerary builder automatically.
              </p>
            )}

            <button
              type="submit"
              disabled={loading || searchLoading}
              className="w-full inline-flex items-center justify-center gap-2 bg-gradient-to-r from-marigold-600 to-petrol-600 hover:from-marigold-500 hover:to-petrol-500 text-white font-bold py-3.5 rounded-xl transition-all shadow-md shadow-marigold-500/10 disabled:opacity-50"
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
          {/* Error banner "” shown in results area so it appears where destination cards would be */}
              {error && (
                <div className="bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800/40 rounded-2xl p-6 flex items-start gap-4">
                  <div className="h-10 w-10 rounded-xl bg-rose-100 dark:bg-rose-950/40 text-rose-500 flex items-center justify-center shrink-0">
                    <AlertTriangle size={20} />
                  </div>
                  <div>
                    <h3 className="font-bold text-rose-700 dark:text-rose-400 text-sm mb-1">No results</h3>
                    <p className="text-rose-600 dark:text-rose-300 text-xs leading-relaxed">{error}</p>
                    <button
                      type="button"
                      onClick={() => setError(null)}
                      className="mt-3 text-[10px] font-bold uppercase tracking-wider text-rose-500 hover:text-rose-700 dark:hover:text-rose-300 transition-colors"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              )}

          {flowMode === 'discover' && (
            <div className="flex flex-col gap-6">
              {!searchCompleted && !searchLoading && !error && (
                <div className="bg-paper-100 dark:bg-paper-800/40 border border-dashed border-paper-200 dark:border-paper-700 rounded-2xl h-96 flex flex-col items-center justify-center text-center p-6">
                  <Search className="h-16 w-16 text-paper-300 dark:text-paper-600 mb-4 animate-pulse" />
                  <h3 className="text-lg font-bold text-paper-700 dark:text-paper-300 mb-2">Search for matching destinations</h3>
                  <p className="text-sm text-paper-400 max-w-sm">
                    Use the same trip inputs to compare options first. The strongest matches will appear here.
                  </p>
                </div>
              )}

              {searchLoading && (
                <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6 shadow-sm space-y-6 animate-pulse">
                  <div className="h-8 bg-paper-200 dark:bg-paper-700 rounded w-1/2" />
                  <div className="h-4 bg-paper-200 dark:bg-paper-700 rounded w-2/3" />
                  <div className="space-y-3">
                    <div className="h-24 bg-paper-200 dark:bg-paper-700 rounded" />
                    <div className="h-24 bg-paper-200 dark:bg-paper-700 rounded" />
                    <div className="h-24 bg-paper-200 dark:bg-paper-700 rounded" />
                  </div>
                </div>
              )}

              {searchCompleted && searchResults.length === 0 && (
                <div className="bg-paper-100 dark:bg-paper-800/40 border border-dashed border-paper-200 dark:border-paper-700 rounded-2xl h-96 flex flex-col items-center justify-center text-center p-6">
                  <AlertTriangle className="h-16 w-16 text-paper-300 dark:text-paper-600 mb-4" />
                  <h3 className="text-lg font-bold text-paper-700 dark:text-paper-300 mb-2">No matches found</h3>
                  <p className="text-sm text-paper-400 max-w-sm">
                    Try adjusting the budget, duration, or trip type, then search again.
                  </p>
                </div>
              )}

              {searchCompleted && searchResults.length > 0 && (
                <div className="flex flex-col gap-4">
                  <div>
                    <h3 className="text-lg font-bold text-paper-800 dark:text-white">Top destination matches</h3>
                    <p className="text-xs text-paper-500 dark:text-paper-400 mt-1">
                      Pick a destination below to lock it into the itinerary builder.
                    </p>
                  </div>

                  {searchResults.map((res, index) => {
                    const isExpanded = expandedSearchIdx === index;
                    return (
                      <div
                        key={res.destination.id}
                        className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-5 shadow-sm flex flex-col hover:border-marigold-500/40 transition-all gap-4"
                      >
                        <div className="flex flex-col md:flex-row gap-5 items-start justify-between w-full">
                          <div className="space-y-3 flex-1">
                            <div className="flex items-center gap-3 flex-wrap">
                              <div className="h-6 w-6 rounded-full bg-marigold-600/10 dark:bg-marigold-950/40 text-marigold-600 dark:text-marigold-400 font-extrabold text-[10px] flex items-center justify-center">
                                #{index + 1}
                              </div>
                              <h4 className="font-extrabold text-lg text-paper-900 dark:text-white hover:text-marigold-600 dark:hover:text-marigold-400 transition-colors">
                                {res.destination.name}
                              </h4>
                              <span className="bg-paper-100 dark:bg-paper-900 text-paper-600 dark:text-paper-400 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase">
                                {res.destination.category}
                              </span>
                            </div>

                            <span className="text-[10px] text-paper-400 font-bold uppercase tracking-wider flex items-center gap-1">
                              <MapPin size={11} className="text-paper-400 shrink-0" />
                              {res.destination.state}
                            </span>

                            <p className="text-paper-500 dark:text-paper-400 text-xs leading-relaxed max-w-xl line-clamp-2">
                              {res.destination.description}
                            </p>

                            <div className="flex items-center gap-4 text-xs font-semibold text-paper-600 dark:text-paper-400 pt-1">
                              <div className="flex items-center gap-0.5 text-amber-500">
                                <Star size={13} fill="currentColor" />
                                <span className="font-bold text-paper-800 dark:text-white">{res.destination.rating}</span>
                              </div>
                              <span>Best season: {res.destination.best_season}</span>
                            </div>
                          </div>

                          <div className="flex flex-col items-start md:items-end gap-3 justify-between md:border-l md:border-paper-100 md:dark:border-paper-700/60 md:pl-6 shrink-0 w-full md:w-auto">
                            <div className="flex flex-col md:items-end">
                              <span className="text-[9px] text-paper-400 font-bold uppercase">Estimated Cost</span>
                              <span className="text-lg font-extrabold text-paper-900 dark:text-white">INR {res.estimated_cost.toLocaleString()}</span>
                              <span className="text-[9px] text-paper-400 font-medium">({res.budget_fit}% of budget)</span>
                            </div>

                            <div className={`px-2.5 py-1 rounded-lg border text-[10px] font-bold uppercase ${getValueScoreColor(res.value_score)}`}>
                              Match Score: {res.value_score}
                            </div>

                            <div className="flex gap-2 w-full md:w-auto">
                              <button
                                type="button"
                                onClick={() => setExpandedSearchIdx(isExpanded ? null : index)}
                                className="flex-1 md:flex-none inline-flex items-center justify-center gap-1 bg-paper-100 hover:bg-paper-200 dark:bg-paper-700 dark:hover:bg-paper-600 text-paper-800 dark:text-white font-bold px-3 py-2 rounded-xl text-xs transition-all border border-paper-200 dark:border-paper-600"
                              >
                                {isExpanded ? 'Hide Match' : 'Show Match'}
                              </button>
                              <button
                                onClick={() => handleSelectDestination(res)}
                                className="flex-1 md:flex-none inline-flex items-center justify-center gap-1 bg-paper-900 hover:bg-paper-800 dark:bg-paper-700 dark:hover:bg-paper-600 text-white font-bold px-4 py-2 rounded-xl text-xs transition-all shadow-md shadow-paper-900/10"
                              >
                                Use this destination
                                <ArrowRight size={13} />
                              </button>
                            </div>
                          </div>
                        </div>

                        {isExpanded && res.breakdown && (
                          <RecommendationExplainability
                            destinationName={res.destination.name}
                            overallScore={res.value_score}
                            breakdown={res.breakdown}
                            className="w-full mt-2 border border-paper-100 dark:border-paper-700 bg-paper-50/50 dark:bg-paper-900/10"
                          />
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {flowMode === 'plan' && !plan && !loading && !error && (
            <div className="bg-paper-100 dark:bg-paper-800/40 border border-dashed border-paper-200 dark:border-paper-700 rounded-2xl h-96 flex flex-col items-center justify-center text-center p-6">
              <Compass className="h-16 w-16 text-paper-300 dark:text-paper-600 mb-4 animate-pulse" />
              <h3 className="text-lg font-bold text-paper-700 dark:text-paper-300 mb-2">No Plan Generated Yet</h3>
              <p className="text-sm text-paper-400 max-w-sm">
                Enter your details on the left and hit generate to compute the itinerary.
              </p>
            </div>
          )}

          {flowMode === 'plan' && loading && (
            <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6 shadow-sm space-y-6 animate-pulse">
              <div className="h-8 bg-paper-200 dark:bg-paper-700 rounded w-1/3" />
              <div className="h-4 bg-paper-200 dark:bg-paper-700 rounded w-2/3" />
              <div className="grid grid-cols-3 gap-4">
                <div className="h-20 bg-paper-200 dark:bg-paper-700 rounded" />
                <div className="h-20 bg-paper-200 dark:bg-paper-700 rounded" />
                <div className="h-20 bg-paper-200 dark:bg-paper-700 rounded" />
              </div>
              <div className="h-40 bg-paper-200 dark:bg-paper-700 rounded" />
            </div>
          )}

          {flowMode === 'plan' && plan && (
            <div className="flex flex-col gap-6">

              {/* Plan Header Card */}
              <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-6 shadow-sm relative overflow-hidden">
                <div className="absolute top-0 right-0 bg-marigold-600 text-white text-xs font-semibold px-4 py-1.5 rounded-bl-2xl">
                  {plan.destination.category}
                </div>

                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                  <div>
                    <span className="text-xs text-paper-400 font-bold uppercase tracking-wider">{plan.destination.state}</span>
                    <h2 className="text-2xl font-extrabold text-paper-900 dark:text-white">{plan.destination.name}</h2>
                    {savedTripId && (
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-paper-400 font-semibold">Status:</span>
                        <select
                          value={tripStatus}
                          onChange={async (e) => {
                            const newStatus = e.target.value;
                            try {
                              const response = await api.patch(`/api/trips/${savedTripId}/status`, { status: newStatus });
                              setTripStatus(response.data.status);
                            } catch (err) {
                              console.error(err);
                              alert('Failed to update trip status.');
                            }
                          }}
                          className="bg-paper-50 dark:bg-paper-700 text-paper-700 dark:text-paper-200 text-xs font-bold px-2.5 py-1 rounded-lg border border-paper-200 dark:border-paper-600 focus:outline-none"
                        >
                          {["Draft", "Planned", "In Progress", "Completed", "Cancelled"].map((st) => (
                            <option key={st} value={st}>{st}</option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {savedTripId ? (
                      <>
                        <button
                          onClick={() => setIsShareModalOpen(true)}
                          className="inline-flex items-center gap-1.5 bg-paper-100 hover:bg-paper-200 dark:bg-paper-700 dark:hover:bg-paper-600 text-paper-800 dark:text-white px-4 py-2 rounded-xl text-sm font-bold transition-all border border-paper-200 dark:border-paper-600"
                        >
                          <Share2 size={16} />
                          Share Plan
                        </button>
                        <button
                          onClick={handleDownloadPDF}
                          disabled={downloadingPdf}
                          className="inline-flex items-center gap-1.5 bg-paper-100 hover:bg-paper-200 dark:bg-ink-700 dark:hover:bg-ink-600 text-ink-900 dark:text-paper-50 px-4 py-2 rounded-xl text-sm font-semibold transition-all border border-paper-200 dark:border-ink-600 disabled:opacity-50"
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
                          className="inline-flex items-center gap-1 bg-marigold-600 hover:bg-marigold-500 text-white px-4 py-2 rounded-xl text-sm font-bold transition-all shadow-md shadow-marigold-600/10"
                        >
                          Manage Expenses
                          <ArrowRight size={14} />
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={handleSaveTrip}
                        disabled={savingTrip}
                        className="inline-flex items-center gap-1.5 bg-marigold-600 hover:bg-marigold-500 text-white px-5 py-2.5 rounded-xl text-sm font-bold transition-all shadow-md shadow-marigold-600/10"
                      >
                        {savingTrip ? <Loader size={16} className="animate-spin" /> : <Check size={16} />}
                        Save Travel Plan
                      </button>
                    )}
                  </div>
                </div>

                <p className="text-paper-600 dark:text-paper-400 text-sm leading-relaxed mb-6">
                  {plan.destination.description}
                </p>

                {/* Seeding attributes */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 border-t border-paper-100 dark:border-paper-700 pt-6">
                  <div className="p-3 bg-paper-50 dark:bg-paper-900/50 rounded-xl">
                    <span className="text-[10px] text-paper-400 font-bold block uppercase mb-1">Trip Duration</span>
                    <span className="text-sm font-bold text-paper-800 dark:text-white">{plan.days} Days</span>
                  </div>
                  <div className="p-3 bg-paper-50 dark:bg-paper-900/50 rounded-xl">
                    <span className="text-[10px] text-paper-400 font-bold block uppercase mb-1">Hotel Tier</span>
                    <span className="text-sm font-bold text-paper-800 dark:text-white">{plan.costs.hotel_tier}</span>
                  </div>
                  <div className="p-3 bg-paper-50 dark:bg-paper-900/50 rounded-xl">
                    <span className="text-[10px] text-paper-400 font-bold block uppercase mb-1">Transport</span>
                    <span className="text-sm font-bold text-paper-800 dark:text-white">{plan.costs.transport_mode}</span>
                  </div>
                  <div className="p-3 bg-paper-50 dark:bg-paper-900/50 rounded-xl">
                    <span className="text-[10px] text-paper-400 font-bold block uppercase mb-1">Best Season</span>
                    <span className="text-xs font-bold text-paper-800 dark:text-white truncate block">{plan.destination.best_season}</span>
                  </div>
                </div>
              </div>

              {/* Recommendation Explainability Match Insights */}
              {plan.breakdown && (
                <RecommendationExplainability
                  destinationName={plan.destination.name}
                  overallScore={plan.value_score}
                  breakdown={plan.breakdown}
                  className="w-full"
                />
              )}

              {/* Weather & Season Intelligence */}
              {plan.destination.weather_intelligence && (
                <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-5 shadow-sm space-y-3.5">
                  <div className="flex justify-between items-center">
                    <h3 className="text-xs font-extrabold uppercase tracking-wider text-paper-800 dark:text-white flex items-center gap-1.5">
                      <CloudSun size={15} className="text-marigold-500" />
                      Weather & Season Intelligence
                    </h3>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      plan.destination.weather_intelligence.season_rating === 'Excellent' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200/30' :
                      plan.destination.weather_intelligence.season_rating === 'Good' ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-400 border border-blue-200/30' :
                      plan.destination.weather_intelligence.season_rating === 'Fair' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400 border border-amber-200/30' :
                      'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400 border border-rose-200/30'
                    }`}>
                      {plan.destination.weather_intelligence.season_rating}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-bold bg-paper-50 dark:bg-paper-900/50 p-3 rounded-xl">
                    <div className="space-y-0.5">
                      <span className="text-[10px] text-paper-400 block uppercase">Current Season</span>
                      <span className="text-paper-700 dark:text-paper-400">{plan.destination.weather_intelligence.current_season}</span>
                    </div>
                    <div className="space-y-0.5">
                      <span className="text-[10px] text-paper-400 block uppercase">Expected Temp</span>
                      <span className="text-paper-700 dark:text-paper-400">{plan.destination.weather_intelligence.temperature_range}</span>
                    </div>
                    <div className="space-y-0.5">
                      <span className="text-[10px] text-paper-400 block uppercase">Rain Prob</span>
                      <span className="text-paper-700 dark:text-paper-400">{plan.destination.weather_intelligence.rain_probability}</span>
                    </div>
                    <div className="space-y-0.5">
                      <span className="text-[10px] text-paper-400 block uppercase">Crowd Level</span>
                      <span className="text-paper-700 dark:text-paper-400">{plan.destination.weather_intelligence.crowd_level}</span>
                    </div>
                  </div>
                  <p className="text-xs text-paper-500 dark:text-paper-400 leading-relaxed italic border-l-2 border-marigold-500 pl-3">
                    {plan.destination.weather_intelligence.recommendation}
                  </p>
                </div>
              )}

              {/* Circular Budget Health Meter */}
              <BudgetHealthMeter
                budget={plan.budget}
                estimatedCost={plan.costs.total_estimated_cost}
                className="w-full text-paper-800 dark:text-white"
              />

              {/* Two Column Cost Breakdown & Daily Itinerary */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

                {/* Left Column: Cost Breakdown + Budget Allocation Editor */}
                <div className="lg:col-span-5 flex flex-col gap-6">
                  
                  {/* Cost Breakdown Module */}
                  <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-5 shadow-sm">
                    <h3 className="text-base font-bold text-paper-800 dark:text-white mb-4">Cost Breakdown</h3>

                    <div className="flex flex-col gap-3.5 text-xs text-paper-600 dark:text-paper-300">
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-2">
                          {plan.costs.transport_mode === 'Flight' ? <Plane size={15} className="text-marigold-500" /> : <Train size={15} className="text-marigold-500" />}
                          Transportation
                        </span>
                        <span className="font-bold text-paper-800 dark:text-white">INR {plan.costs.transport_cost.toLocaleString()}</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-2">
                          <Building size={15} className="text-marigold-500" />
                          Accommodation
                        </span>
                        <span className="font-bold text-paper-800 dark:text-white">INR {plan.costs.hotel_cost.toLocaleString()}</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-2">
                          <Utensils size={15} className="text-marigold-500" />
                          Food & Dining
                        </span>
                        <span className="font-bold text-paper-800 dark:text-white">INR {plan.costs.food_cost.toLocaleString()}</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-2">
                          <Camera size={15} className="text-marigold-500" />
                          Activities
                        </span>
                        <span className="font-bold text-paper-800 dark:text-white">INR {plan.costs.activities_cost.toLocaleString()}</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-2">
                          <MapPin size={15} className="text-marigold-500" />
                          Local Transport
                        </span>
                        <span className="font-bold text-paper-800 dark:text-white">INR {plan.costs.local_transport_cost.toLocaleString()}</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-2">
                          <Percent size={15} className="text-marigold-500" />
                          Taxes & Booking Fees
                        </span>
                        <span className="font-bold text-paper-800 dark:text-white">INR {plan.costs.taxes_fees_cost.toLocaleString()}</span>
                      </div>

                      <div className="flex items-center justify-between border-t border-paper-100 dark:border-paper-700 pt-3">
                        <span className="flex items-center gap-2">
                          <LifeBuoy size={15} className="text-marigold-500" />
                          Emergency Reserve
                        </span>
                        <span className="font-bold text-paper-800 dark:text-white">INR {plan.costs.emergency_reserve.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  {/* Manual Budget Allocation Editor */}
                  <BudgetAllocationEditor
                    budget={plan.budget}
                    initialAllocations={plan.costs}
                    onSave={handleAllocationSave}
                    onReset={handleAllocationReset}
                    isSaving={savingTrip}
                  />

                  {/* Hidden Cost Prediction Module */}
                  <div className="bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl p-4 mt-6">
                    <h4 className="text-xs font-bold flex items-center gap-1.5 mb-3 text-marigold-600 dark:text-marigold-400 uppercase tracking-wide">
                      <LifeBuoy size={14} />
                      Hidden Cost Prediction
                    </h4>
                    <div className="flex flex-col gap-2.5 text-[11px] text-paper-500 dark:text-paper-400">
                      <div className="flex justify-between">
                        <span>Local Auto / Cab Pool</span>
                        <span className="font-semibold text-paper-700 dark:text-paper-300">INR {Math.round(plan.costs.local_transport_cost * 0.6).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Attraction Toll / Parking</span>
                        <span className="font-semibold text-paper-700 dark:text-paper-300">INR {Math.round(plan.costs.local_transport_cost * 0.15).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Booking Convenience Tax</span>
                        <span className="font-semibold text-paper-700 dark:text-paper-300">INR {Math.round(plan.costs.taxes_fees_cost * 0.65).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Miscellaneous Contingency</span>
                        <span className="font-semibold text-paper-700 dark:text-paper-300">INR {plan.costs.emergency_reserve.toLocaleString()}</span>
                      </div>
                      <div className="border-t border-paper-200 dark:border-paper-700 pt-2 flex justify-between font-bold text-paper-800 dark:text-white">
                        <span>Total Buffer Needed</span>
                        <span>INR {(Math.round(plan.costs.local_transport_cost * 0.75) + Math.round(plan.costs.taxes_fees_cost * 0.65) + plan.costs.emergency_reserve).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  {/* Carbon Footprint Estimator */}
                  {plan.carbon_footprint && (
                    <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-5 shadow-sm space-y-3.5 mt-6">
                      <div className="flex justify-between items-center">
                        <h4 className="text-xs font-extrabold uppercase tracking-wider text-paper-800 dark:text-white flex items-center gap-1.5">
                          <Leaf size={15} className="text-emerald-500" />
                          Carbon Footprint Impact
                        </h4>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          plan.carbon_footprint.carbon_rating === 'Eco Friendly' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200/30' :
                          plan.carbon_footprint.carbon_rating === 'Moderate' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400 border border-amber-200/30' :
                          'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400 border border-rose-300/30'
                        }`}>
                          {plan.carbon_footprint.carbon_rating}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center p-3.5 bg-paper-50 dark:bg-paper-900 rounded-xl text-xs font-bold border border-paper-100 dark:border-paper-800">
                        <span className="text-paper-500 flex items-center gap-2">
                          {plan.carbon_footprint.transport_mode === 'Flight' ? <Plane size={15} className="text-rose-500" /> : <Train size={15} className="text-emerald-500" />}
                          CO₂ Emissions ({plan.carbon_footprint.transport_mode})
                        </span>
                        <span className="text-paper-800 dark:text-white">{plan.carbon_footprint.co2_emissions} kg</span>
                      </div>
                      
                      <div className="text-[10px] text-paper-600 dark:text-paper-400 leading-relaxed bg-emerald-50/20 dark:bg-emerald-950/10 p-3 rounded-xl border border-emerald-100/40 flex items-start gap-2">
                        <Leaf size={13} className="text-emerald-500 mt-0.5 shrink-0" fill="currentColor" />
                        <span>
                          {plan.carbon_footprint.transport_mode === 'Flight'
                            ? `Choosing train instead of flight reduces segment emissions by ${plan.carbon_footprint.alternative_savings} kg.`
                            : `Eco Choice! Traveling by train instead of flight saved an estimated ${plan.carbon_footprint.alternative_savings} kg of CO₂.`
                          }
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Smart Packing Checklist */}
                  {savedTripId && (
                    <div className="mt-6">
                      <TripChecklist tripId={savedTripId} />
                    </div>
                  )}

                  {/* Travel Documents Manager */}
                  {savedTripId && (
                    <div className="mt-6">
                      <DocumentManager tripId={savedTripId} />
                    </div>
                  )}
                </div>

                {/* Timeline-Based Itinerary */}
                <div className="md:col-span-7 flex flex-col gap-4">
                  <div className="flex justify-between items-center bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-4.5 rounded-2xl shadow-sm">
                    <div>
                      <h3 className="text-base font-bold text-paper-800 dark:text-white">Smart Chronological Itinerary</h3>
                      <p className="text-[11px] text-paper-400 mt-0.5">Chronologically organized daily travel timeline</p>
                    </div>
                    <div className="flex gap-2">
                      <button
                         type="button"
                         onClick={() => {
                           const allExpanded = plan.itineraries.reduce((acc, it) => {
                             acc[it.day_number] = true;
                             return acc;
                           }, {} as Record<number, boolean>);
                           setExpandedDays(allExpanded);
                         }}
                         className="text-[10px] font-bold text-marigold-600 hover:text-marigold-500 uppercase"
                       >
                         Expand All
                       </button>
                       <span className="text-paper-300">|</span>
                       <button
                         type="button"
                         onClick={() => setExpandedDays({})}
                         className="text-[10px] font-bold text-paper-400 hover:text-paper-600 uppercase"
                       >
                         Collapse All
                       </button>
                    </div>
                  </div>
                  
                  <TimelineItinerary
                    itineraries={plan.itineraries}
                    expandedDays={expandedDays}
                    toggleDay={toggleDay}
                    className="w-full"
                  />
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

      {isShareModalOpen && savedTripId && plan && (
        <ShareModal
          tripId={savedTripId}
          isPublic={plan.is_public || false}
          shareToken={plan.share_token || null}
          onClose={() => setIsShareModalOpen(false)}
          onUpdate={(updatedTrip) => {
            setPlan(prev => {
              if (!prev) return null;
              return {
                ...prev,
                is_public: updatedTrip.is_public,
                share_token: updatedTrip.share_token
              };
            });
          }}
        />
      )}
    </motion.div>
  );
};



