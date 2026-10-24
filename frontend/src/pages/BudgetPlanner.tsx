import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
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
import { WeatherForecast } from '../components/WeatherForecast';
import { OriginCandidateRankingDetails, formatCandidateRating, capDisplayedOriginShortlist } from '../components/OriginCandidateRankingDetails.mjs';
import { useQuery } from '@tanstack/react-query';


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
    geoapify_place_id?: string | null;
    google_place_id?: string | null;
    name: string;
    state: string;
    description: string;
    address?: string | null;
    latitude?: number | null;
    longitude?: number | null;
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

interface OriginCandidate {
  destination_id: string;
  name: string;
  region?: string | null;
  country: string;
  country_code: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  estimated_travel_hours?: number | null;
  travel_time_type: string;
  rating: number | null;
  user_rating_count: number | null;
  google_place_id: string | null;
  google_maps_uri: string | null;
  rating_source: 'foursquare' | 'unavailable';
  provider?: string | null;
  rating_scale?: number | null;
  review_count?: number | null;
  rating_url?: string | null;
  fsq_place_id?: string | null;
  status?: string | null;
  rating_unavailable_reason?: string | null;
  address?: string | null;
  description?: string | null;
  destination_highlights: string[];
  why_visit: string;
  trip_fit: string;
  practical_note?: string | null;
  matched_categories: string[];
  data_source: string;
  estimated_cost: number;
  budget_remaining: number;
  under_budget: boolean;
  value_score: number | null;
  overall_match_score: number | null;
  category_relevance_score: number | null;
  interest_match_score: number | null;
  comfort_suitability_score: number | null;
  duration_suitability_score: number | null;
  destination_quality_score: number | null;
  match_reasons: string[];
  tradeoffs: string[];
  breakdown: Record<string, number | null>;
  explanation: string;
  costs: CostAllocation & { accommodation_nights: number };
}

type PlannerMode = 'plan' | 'discover';

interface BudgetPlannerProps {
  initialMode?: PlannerMode;
}

export const BudgetPlanner: React.FC<BudgetPlannerProps> = ({ initialMode = 'discover' }) => {
  usePageTitle('Budget Planner | BudgetBound');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const modeParam = searchParams.get('mode');
  const startingMode: PlannerMode =
    modeParam === 'plan' ? 'plan' : modeParam === 'discover' ? 'discover' : initialMode;

  const [flowMode, setFlowMode] = useState<PlannerMode>(startingMode);
  const [startingCity, setStartingCity] = useState('');
  const [originAddress, setOriginAddress] = useState('');
  const [originCoordinates, setOriginCoordinates] = useState<{ latitude: number; longitude: number } | null>(null);
  const [budget, setBudget] = useState<string>('20000');
  const [days, setDays] = useState<number>(4);
  const [travelType, setTravelType] = useState('Nature');
  const [additionalInterests, setAdditionalInterests] = useState('');
  const [travelersCount, setTravelersCount] = useState<number>(1);
  const [comfortScore, setComfortScore] = useState<number>(50);
  const [selectedDestinationId, setSelectedDestinationId] = useState<number | null>(null);
  const [selectedDestinationName, setSelectedDestinationName] = useState<string | null>(null);
  const [selectedCoordinates, setSelectedCoordinates] = useState<{ latitude: number; longitude: number } | null>(null);
  const [selectedDestinationAddress, setSelectedDestinationAddress] = useState<string | null>(null);
  const [selectedPlaceId, setSelectedPlaceId] = useState<string | null>(null);
  const [selectedGeoapifyPlaceId, setSelectedGeoapifyPlaceId] = useState<string | null>(null);
  const [selectedCountryCode, setSelectedCountryCode] = useState<string | null>(null);
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
  const [itineraryRetryAttempts, setItineraryRetryAttempts] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchCompleted, setSearchCompleted] = useState(false);
  const [discoveredCandidates, setDiscoveredCandidates] = useState<OriginCandidate[]>([]);
  const [discoveryWarnings, setDiscoveryWarnings] = useState<string[]>([]);
  const [discoveryStats, setDiscoveryStats] = useState<Record<string, number> | null>(null);
  const [rankingSource, setRankingSource] = useState<'ai' | 'fallback' | 'not_applicable'>('not_applicable');
  const [includeLocalGetaways, setIncludeLocalGetaways] = useState(false);
  const [plan, setPlan] = useState<PlanResult | null>(null);
  const [savedTripId, setSavedTripId] = useState<number | null>(null);
  const [savingTrip, setSavingTrip] = useState(false);
  const [isMapModalOpen, setIsMapModalOpen] = useState(false);
  const [isDestinationMapOpen, setIsDestinationMapOpen] = useState(false);

  const placeDiscovery = useQuery({
    queryKey: ['trip-places', selectedDestinationName, selectedCoordinates?.latitude, selectedCoordinates?.longitude, travelType],
    enabled: Boolean(selectedDestinationName && selectedCoordinates),
    staleTime: 10 * 60 * 1000,
    queryFn: async () => (await api.post('/api/trips/discover', {
      destination_name: selectedDestinationName,
      destination_address: selectedDestinationAddress,
      latitude: selectedCoordinates?.latitude,
      longitude: selectedCoordinates?.longitude,
      destination_country_code: selectedCountryCode || undefined,
      travel_type: travelType,
      days,
      interests: [travelType]
    })).data,
  });

  const [downloadingPdf, setDownloadingPdf] = useState(false);

  const [tripStatus, setTripStatus] = useState<string>("Planned");
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);

  // Fetch all destinations for select dropdown in Build Itinerary mode
  React.useEffect(() => {
    if (flowMode !== 'plan' || selectedCoordinates) return;
    api.get('/api/destinations/', { params: { limit: 100 } })
      .then(response => {
        setAllDestinations(response.data.destinations || []);
      })
      .catch(err => {
        console.error('Failed to fetch destinations list:', err);
      });
  }, [flowMode, selectedCoordinates]);

  // Fetch existing saved trip details if tripId query param is provided
  React.useEffect(() => {
    const tripIdParam = searchParams.get('tripId');
    const fetchSavedTrip = async (id: string) => {
      try {
        setLoading(true);
        const response = await api.get(`/api/trips/${id}`);
        const trip = response.data;
        if (trip.destination?.latitude != null && trip.destination?.longitude != null) {
          setSelectedCoordinates({ latitude: trip.destination.latitude, longitude: trip.destination.longitude });
          setSelectedDestinationName(trip.destination.name);
          setSelectedDestinationAddress(trip.destination.address || null);
        }
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
    if (score < 34) return { label: 'Maximum Savings', desc: 'Favors lower-cost transport, stays, dining, and activities.', color: 'text-emerald-500' };
    if (score > 66) return { label: 'Higher Comfort', desc: 'Gradually increases estimated spend for more comfortable options; it does not automatically select luxury stays or flights.', color: 'text-amber-500' };
    return { label: 'Balanced Comfort', desc: 'Uses the middle of the continuous comfort-adjusted cost range.', color: 'text-marigold-500' };
  };

  const comfortInfo = getComfortLabel(comfortScore);

  const buildTripPayload = (destinationId?: number | null) => ({
    starting_city: startingCity || 'Bangalore',
    ...(originCoordinates ? { origin_latitude: originCoordinates.latitude, origin_longitude: originCoordinates.longitude } : {}),
    budget: Number(budget),
    days,
    travel_type: travelType,
    travelers_count: travelersCount,
    comfort_score: comfortScore,
    interests: Array.from(new Set([travelType, ...additionalInterests.split(',').map((item) => item.trim()).filter(Boolean)])).slice(0, 12),
    // Use explicit arg first, then fall back to current state
    destination_id: destinationId !== undefined ? destinationId : (selectedDestinationId ?? null),
    ...(selectedCoordinates || {}),
    ...(selectedDestinationName ? { destination_name: selectedDestinationName } : {}),
    ...(selectedDestinationAddress ? { destination_address: selectedDestinationAddress } : {}),
    ...(selectedPlaceId ? { google_place_id: selectedPlaceId } : {}),
    ...(selectedGeoapifyPlaceId ? { geoapify_place_id: selectedGeoapifyPlaceId } : {}),
    ...(selectedCountryCode ? { destination_country_code: selectedCountryCode } : {})
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

    // In plan mode, starting city is required for accurate cost estimation
    if (!startingCity.trim() && flowMode === 'plan') {
      setError('Please enter a starting city for accurate cost estimation.');
      return;
    }

    if (flowMode === 'discover') {
      if (!startingCity.trim()) {
        setError('Enter or select a valid starting location to discover destinations.');
        return;
      }
      setSearchLoading(true);
      setSearchCompleted(false);
      setSearchResults([]);
      setDiscoveredCandidates([]);
      setDiscoveryWarnings([]);
      setDiscoveryStats(null);
      setRankingSource('not_applicable');
      try {
        const response = await api.post('/api/trips/discover-from-origin', {
          origin_name: startingCity.trim(),
          origin_address: originAddress || undefined,
          origin_latitude: originCoordinates?.latitude,
          origin_longitude: originCoordinates?.longitude,
          budget: budgetNum,
          days,
          travelers_count: travelersCount,
          travel_type: travelType,
          comfort_score: comfortScore,
          interests: Array.from(new Set([travelType, ...additionalInterests.split(',').map((item) => item.trim()).filter(Boolean)])).slice(0, 12),
          short_local_getaway: includeLocalGetaways
        });
        if (response.data.origin?.latitude != null && response.data.origin?.longitude != null) {
          setOriginCoordinates({ latitude: response.data.origin.latitude, longitude: response.data.origin.longitude });
        }
        setDiscoveredCandidates(response.data.candidates || []);
        setDiscoveryWarnings(response.data.warnings || []);
        setDiscoveryStats({ ...(response.data.filter_counts || {}), examined_candidate_count: response.data.examined_candidate_count || 0, shortlisted: response.data.candidate_count || 0 });
        setRankingSource(response.data.ranking_source || 'not_applicable');
        setSearchCompleted(true);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Destination discovery is unavailable. Check the starting location and try again.');
        setSearchCompleted(true);
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
      setItineraryRetryAttempts(0);
    } catch (err: any) {
      console.error(err);
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      setItineraryRetryAttempts(prev => prev + 1);
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

  const handleSelectOriginCandidate = async (candidate: OriginCandidate) => {
    setSelectedDestinationId(null);
    setSelectedDestinationName(candidate.name);
    setSelectedDestinationAddress([candidate.region, candidate.country].filter(Boolean).join(', '));
    setSelectedCoordinates({ latitude: candidate.latitude, longitude: candidate.longitude });
    // Keep the Geoapify destination ID separate from Google's identifier.
    setSelectedPlaceId(candidate.google_place_id || null);
    setSelectedGeoapifyPlaceId(candidate.destination_id);
    setSelectedCountryCode(candidate.country_code || null);
    setError(null);
    setPlan(null);
    setFlowMode('plan');
    setSearchCompleted(false);
    setItineraryRetryAttempts(0);
    
    // Immediately generate the plan with the selected destination
    setLoading(true);
    try {
      const payload = {
        starting_city: startingCity || 'Bangalore',
        origin_latitude: originCoordinates?.latitude,
        origin_longitude: originCoordinates?.longitude,
        budget: Number(budget),
        days,
        travel_type: travelType,
        travelers_count: travelersCount,
        comfort_score: comfortScore,
        interests: Array.from(new Set([travelType, ...additionalInterests.split(',').map((item) => item.trim()).filter(Boolean)])).slice(0, 12),
        // Use the geoapify place ID for discovered destinations
        geoapify_place_id: candidate.destination_id,
        latitude: candidate.latitude,
        longitude: candidate.longitude,
        destination_name: candidate.name,
        destination_address: [candidate.region, candidate.country].filter(Boolean).join(', '),
        destination_country_code: candidate.country_code || undefined
      };
      
      const response = await api.post('/api/trips/plan', payload);
      setPlan(response.data);
      setExpandedDays({ 1: true });
      setItineraryRetryAttempts(0);
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.detail;
      if (err.response?.status === 422) {
        setError(detail || `This destination exceeds your budget. Try increasing your budget or reducing duration.`);
      } else {
        setError(detail || 'Failed to generate a plan for this destination.');
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
    setSelectedPlaceId(null);
    setSelectedGeoapifyPlaceId(null);
    setSelectedCountryCode(null);
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
      destination_id: destId,
      ...(selectedCoordinates || {})
    };

    try {
      const response = await api.post('/api/trips/plan', payload);
      setPlan(response.data);
      setExpandedDays({ 1: true });
      setItineraryRetryAttempts(0);
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
        responseType: 'arraybuffer',
        headers: {
          'Accept': 'application/pdf'
        }
      });
      
      console.log('PDF response received:', response.status, response.data.byteLength);
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `budgetbound_${plan.destination.name.replace(/\s+/g, '_').toLowerCase()}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      console.log('PDF download completed');
    } catch (err: any) {
      console.error('Failed to download PDF:', {
        message: err.message,
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data
      });
      alert('Failed to download PDF. Check browser console for details.');
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
        ctaLabel={flowMode === 'discover' ? 'Find matches first' : 'Build the itinerary'}
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

<<<<<<< HEAD
          <form id="trip-settings-form" onSubmit={handlePrimaryAction} className="flex flex-col gap-5">
=======
          <form onSubmit={handlePrimaryAction} className="flex flex-col gap-4">
>>>>>>> 467e16fe48924e822e46cfc90613a82a82de7374
            <div>
              <label className="block text-xs font-semibold text-paper-500 dark:text-paper-400 uppercase tracking-wider mb-2">Starting Location</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <MapPin className="absolute left-3.5 top-3.5 text-paper-400" size={16} />
                  <input
                    type="text"
                    required
                    value={startingCity}
                    onChange={(e) => { setStartingCity(e.target.value); setOriginCoordinates(null); setOriginAddress(''); }}
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
              {flowMode === 'discover' && <label className="flex items-start gap-2 text-xs text-paper-600 dark:text-paper-300"><input type="checkbox" checked={includeLocalGetaways} onChange={e => setIncludeLocalGetaways(e.target.checked)} className="mt-0.5 accent-marigold-600"/>Include nearby getaways (20 km minimum)</label>}
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
                        setSelectedPlaceId(null);
                        setSelectedGeoapifyPlaceId(null);
                        setSelectedCoordinates(null);
                      } else {
                        const numericId = Number(idVal);
                        const match = allDestinations.find(d => d.id === numericId);
                        if (match) {
                          setSelectedDestinationId(numericId);
                          setSelectedDestinationName(match.name);
                          setSelectedPlaceId(null);
                          setSelectedGeoapifyPlaceId(null);
                          setSelectedCoordinates(null);
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
            {flowMode === 'plan' && <button type="button" onClick={() => setIsDestinationMapOpen(true)} className="inline-flex items-center gap-2 self-start rounded-xl border border-paper-200 px-3 py-2 text-xs font-bold text-paper-700 dark:border-paper-700 dark:text-paper-200"><MapPin size={14}/> Choose any destination on map</button>}

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
                    type="number"
                    min="1"
                    max="20"
                    required
                    value={travelersCount}
                    onChange={(e) => {
                      const val = parseInt(e.target.value) || 1;
                      setTravelersCount(val);
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

            {flowMode === 'discover' && <div>
              <label htmlFor="destination-interests" className="block text-xs font-semibold text-paper-500 dark:text-paper-400 uppercase tracking-wider mb-2">Additional Interests</label>
              <input id="destination-interests" type="text" value={additionalInterests} onChange={(event) => setAdditionalInterests(event.target.value)} placeholder="e.g. wildlife, local food, museums" className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-marigold-500 text-paper-900 dark:text-white" />
              <p className="mt-1 text-[10px] text-paper-400">Separate interests with commas. They guide personalization after budget checks.</p>
            </div>}

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
                <span>Higher Comfort</span>
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
                  Generating itinerary...
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
                    <h3 className="font-bold text-rose-700 dark:text-rose-400 text-sm mb-1">{flowMode === 'discover' ? 'Discovery notice' : 'Itinerary builder error'}</h3>
                    <p className="text-rose-600 dark:text-rose-300 text-xs leading-relaxed">{error}</p>
                    {(flowMode === 'discover' || itineraryRetryAttempts < 3) && <button
                      type="button"
                      onClick={() => { setError(null); (document.getElementById('trip-settings-form') as HTMLFormElement | null)?.requestSubmit(); }}
                      className="mt-3 text-[10px] font-bold uppercase tracking-wider text-rose-500 hover:text-rose-700 dark:hover:text-rose-300 transition-colors"
                    >
                      {flowMode === 'discover' ? 'Try again' : `Retry itinerary generation (${itineraryRetryAttempts + 1}/3)`}
                    </button>}
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
                    Set your starting location and trip details. We’ll find destination cities you can reach within your budget.
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

              {searchCompleted && discoveredCandidates.length === 0 && !error && (
                <div className="bg-paper-100 dark:bg-paper-800/40 border border-dashed border-paper-200 dark:border-paper-700 rounded-2xl h-96 flex flex-col items-center justify-center text-center p-6">
                  <AlertTriangle className="h-16 w-16 text-paper-300 dark:text-paper-600 mb-4" />
                  <h3 className="text-lg font-bold text-paper-700 dark:text-paper-300 mb-2">No matches found</h3>
                  <p className="text-sm text-paper-400 max-w-sm">
                    {discoveryWarnings.length ? discoveryWarnings.join(' ') : 'Try adjusting the budget, duration, or trip type, then search again.'}
                  </p>
                </div>
              )}

              {searchCompleted && discoveredCandidates.length > 0 && (
                <div className="flex flex-col gap-4">
                  {discoveryWarnings.map((warning, index) => <p key={index} role="status" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">{warning}</p>)}
                  <div>
                    <h3 className="text-lg font-bold text-paper-800 dark:text-white">Destinations from {startingCity}</h3>
                    <p className="text-xs text-paper-500 dark:text-paper-400 mt-1">
                      Geoapify Places · {rankingSource === 'ai' ? 'AI-personalized ranking · Groq' : 'Fallback ranking · verified destination evidence and trip fit; no AI score'} · cost values are planning estimates, not live quotes.
                    </p>
                    <p className="mt-1 text-xs font-semibold text-paper-600 dark:text-paper-300">Showing {capDisplayedOriginShortlist(discoveredCandidates).length} of {discoveryStats?.examined_candidate_count ?? discoveredCandidates.length} eligible destinations · maximum 8</p>
                    {discoveryStats && <p className="mt-1 text-[11px] text-paper-500">{discoveryStats.received || 0} Geoapify places · {discoveryStats.verified_country || 0} verified in India · {(discoveryStats.low_quality_records_rejected || 0) + (discoveryStats.low_quality_localities_rejected || 0)} low-quality records/localities excluded · {discoveryStats.budget_survivors || 0} budget-feasible candidates ranked · {discoveryStats.shortlisted || 0} shown</p>}
                  </div>

                  {capDisplayedOriginShortlist(discoveredCandidates).map((candidate, index) => {
                    return (
                      <div
                        key={candidate.destination_id}
                        className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-5 shadow-sm flex flex-col hover:border-marigold-500/40 transition-all gap-4"
                      >
                        <div className="flex flex-col md:flex-row gap-5 items-start justify-between w-full">
                          <div className="space-y-3 flex-1">
                            <div className="flex items-center gap-3 flex-wrap">
                              <div className="h-6 w-6 rounded-full bg-marigold-600/10 dark:bg-marigold-950/40 text-marigold-600 dark:text-marigold-400 font-extrabold text-[10px] flex items-center justify-center">
                                #{index + 1}
                              </div>
                              <h4 className="font-extrabold text-lg text-paper-900 dark:text-white">{candidate.name}</h4>
                              {candidate.matched_categories.map((category: string) => <span key={category} className="bg-paper-100 dark:bg-paper-900 text-paper-600 dark:text-paper-400 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase">{category}</span>)}
                            </div>

                            <span className="text-[10px] text-paper-400 font-bold uppercase tracking-wider flex items-center gap-1">
                              <MapPin size={11} className="text-paper-400 shrink-0" />
                              {[candidate.region, candidate.country].filter(Boolean).join(', ')}
                            </span>

                            <p className="text-paper-500 dark:text-paper-400 text-xs leading-relaxed max-w-xl">{candidate.distance_km} km straight-line from origin · live route distance and travel time unavailable</p>

                            <div className="flex items-center gap-4 text-xs font-semibold text-paper-600 dark:text-paper-400 pt-1">
                              <div className="flex items-center gap-0.5 text-amber-500">
                                <Star size={13} fill="currentColor" />
                                <span className="font-bold text-paper-800 dark:text-white" title={candidate.rating_unavailable_reason || undefined}>{formatCandidateRating(candidate.rating, candidate.review_count ?? candidate.user_rating_count, candidate.rating_scale ?? 10)}</span>
                              </div>
                              <span translate="no">{candidate.rating != null ? 'Foursquare rating' : 'Rating unavailable'}</span>
                              {candidate.rating_url && <a href={candidate.rating_url} target="_blank" rel="noreferrer" className="text-xs font-semibold text-blue-600 hover:underline">Open Foursquare place</a>}
                            </div>
                            {candidate.rating == null && candidate.rating_unavailable_reason && <p className="text-[10px] text-paper-500">{candidate.rating_unavailable_reason}</p>}
                            <OriginCandidateRankingDetails candidate={candidate} rankingSource={rankingSource} expanded={expandedSearchIdx === index} />
                          </div>

                          <div className="flex flex-col items-start md:items-end gap-3 justify-between md:border-l md:border-paper-100 md:dark:border-paper-700/60 md:pl-6 shrink-0 w-full md:w-auto">
                            <div className="flex flex-col md:items-end">
                              <span className="text-[9px] text-paper-400 font-bold uppercase">Estimated Cost</span>
                              <span className="text-lg font-extrabold text-paper-900 dark:text-white">INR {candidate.estimated_cost.toLocaleString()}</span>
                              <span className="text-[9px] text-paper-400 font-medium">INR {candidate.budget_remaining.toLocaleString()} remaining · estimate</span>
                              <span className="mt-2 text-[10px] text-paper-500">Travel INR {candidate.costs.transport_cost.toLocaleString()} · lodging INR {candidate.costs.hotel_cost.toLocaleString()} ({candidate.costs.accommodation_nights} nights)</span>
                            </div>

                            <div className="flex gap-2 w-full md:w-auto">
                              <button
                                type="button"
                                onClick={() => setExpandedSearchIdx(expandedSearchIdx === index ? null : index)}
                                className="flex-1 md:flex-none inline-flex items-center justify-center gap-1 bg-paper-100 hover:bg-paper-200 dark:bg-paper-700 dark:hover:bg-paper-600 text-paper-800 dark:text-white font-bold px-3 py-2 rounded-xl text-xs transition-all border border-paper-200 dark:border-paper-600"
                              >
                                {expandedSearchIdx === index ? 'Hide ranking details' : 'Ranking details'}
                              </button>
                              <button
                                onClick={() => handleSelectOriginCandidate(candidate)}
                                className="flex-1 md:flex-none inline-flex items-center justify-center gap-1 bg-paper-900 hover:bg-paper-800 dark:bg-paper-700 dark:hover:bg-paper-600 text-white font-bold px-4 py-2 rounded-xl text-xs transition-all shadow-md shadow-paper-900/10"
                              >
                                Choose destination
                                <ArrowRight size={13} />
                              </button>
                            </div>
                          </div>
                        </div>

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
                {selectedDestinationName ? `${selectedDestinationName} is selected. Review your trip settings, then choose Generate Travel Plan when you’re ready to create the itinerary.` : 'Enter your details on the left and hit generate to compute the itinerary.'}
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

      {selectedCoordinates && selectedDestinationName && (
        <section className="space-y-4">
          <WeatherForecast latitude={selectedCoordinates.latitude} longitude={selectedCoordinates.longitude} location={selectedDestinationName} days={days} />
          <div className="rounded-2xl border border-paper-200 bg-paper-50 p-5 dark:border-paper-700 dark:bg-paper-900">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div><h3 className="text-lg font-black text-paper-900 dark:text-white">Places near {selectedDestinationName}</h3><p className="text-xs text-paper-500">{placeDiscovery.data?.data_source === 'geoapify' ? 'Geoapify Places results matched to your destination and travel type.' : 'Places results matched to your destination and travel type.'}</p></div>
              {placeDiscovery.data?.data_source === 'database_fallback' && <span role="status" className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">Older database fallback</span>}
            </div>
            {placeDiscovery.isLoading && <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3" aria-label="Searching places">{[1,2,3].map(i => <div key={i} className="h-28 animate-pulse rounded-xl bg-paper-200 dark:bg-paper-800" />)}</div>}
            {placeDiscovery.isError && <div role="alert" className="mt-3 flex items-center gap-3 text-sm text-rose-600">{(placeDiscovery.error as any)?.response?.data?.detail || 'Places could not be loaded.'} <button onClick={() => placeDiscovery.refetch()} className="font-bold underline">Retry</button></div>}
            {!placeDiscovery.isLoading && !placeDiscovery.isError && placeDiscovery.data?.fallback_notice && <p className="mt-3 text-sm text-amber-700 dark:text-amber-300">{placeDiscovery.data.fallback_notice}</p>}
            {!placeDiscovery.isLoading && !placeDiscovery.isError && placeDiscovery.data?.places?.length === 0 && <p className="mt-4 text-sm text-paper-500">No places matched this search. Try another destination or travel type.</p>}
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {placeDiscovery.data?.places?.map((place: any, index: number) => <div key={place.place_id || `${place.name}-${index}`} className="rounded-xl border border-paper-200 bg-white p-4 text-left transition hover:border-marigold-500 dark:border-paper-700 dark:bg-paper-800">
                <button type="button" onClick={() => { if (place.latitude == null || place.longitude == null) return; setSelectedDestinationName(place.name); setSelectedDestinationAddress(place.address || null); setSelectedCoordinates({ latitude: place.latitude, longitude: place.longitude }); setSelectedPlaceId(place.data_source === 'google_places' ? place.place_id || null : null); setSelectedGeoapifyPlaceId(place.data_source === 'geoapify' ? place.place_id || null : null); setSelectedCountryCode(place.data_source === 'geoapify' ? 'IN' : null); setPlan(null); }} className="w-full text-left" aria-label={`Select ${place.name}`}>
                <span className="flex items-start justify-between gap-2"><strong className="text-sm text-paper-900 dark:text-white">{place.name}</strong>{place.rating != null && <span className="shrink-0 text-xs font-bold text-amber-600">★ {place.rating}{place.user_rating_count != null ? ` (${place.user_rating_count})` : ''}</span>}</span>
                {place.address && <span className="mt-2 block text-xs text-paper-500">{place.address}</span>}
                {place.price_level && <span className="mt-1 block text-xs text-paper-500">Provider price level: {String(place.price_level).replace('PRICE_LEVEL_', '')} (not an exact price)</span>}
                </button>
                {place.reviews?.[0]?.text && <p className="mt-2 line-clamp-2 text-xs text-paper-600 dark:text-paper-300">“{place.reviews[0].text}”</p>}
                {place.reviews?.[0]?.author_name && <p className="mt-1 text-[10px] text-paper-500">Review by {place.reviews[0].author_url ? <a href={place.reviews[0].author_url} target="_blank" rel="noreferrer" className="underline">{place.reviews[0].author_name}</a> : place.reviews[0].author_name}{place.reviews[0].visit_date ? ` · visited ${place.reviews[0].visit_date}` : ''}</p>}
                <span className="mt-3 flex items-center justify-between text-xs font-bold text-marigold-700 dark:text-marigold-300"><span>{place.data_source === 'database_fallback' ? 'BudgetBound database' : place.data_source === 'geoapify' ? 'Geoapify Places' : <img src="https://maps.gstatic.com/mapfiles/api-3/images/google_on_white.png" alt="Google" className="h-4 w-auto" />}</span>{(place.map_url || place.google_maps_url) && <a href={place.map_url || place.google_maps_url} target="_blank" rel="noreferrer" className="underline">Open map</a>}</span>
              </div>)}
            </div>
            {placeDiscovery.data?.weather_data_source === 'unavailable' && <p className="mt-3 text-sm text-amber-700 dark:text-amber-300">Weather data is unavailable; itinerary generation can continue without weather personalization.</p>}
          </div>
        </section>
      )}

      <LocationPickerModal
        isOpen={isMapModalOpen}
        onClose={() => setIsMapModalOpen(false)}
        onSelectLocation={(location) => {
          setStartingCity(location.name);
          setOriginCoordinates({ latitude: location.latitude, longitude: location.longitude });
          setOriginAddress(location.address || '');
        }}
        initialCity={startingCity}
      />
      <LocationPickerModal
        isOpen={isDestinationMapOpen}
        onClose={() => setIsDestinationMapOpen(false)}
        onSelectLocation={(location) => {
          setSelectedDestinationId(null);
          setSelectedDestinationName(location.name);
          setSelectedCoordinates({ latitude: location.latitude, longitude: location.longitude });
          setSelectedDestinationAddress(location.address || location.name);
          setSelectedPlaceId(null);
          setSelectedGeoapifyPlaceId(null);
        }}
        initialCity={selectedDestinationName || undefined}
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



