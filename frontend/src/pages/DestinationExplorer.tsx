import React, { useEffect, useState } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { TripFlowGuide } from '../components/TripFlowGuide';
import { 
  Map, 
  Search, 
  Star, 
  MapPin, 
  Loader, 
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Zap
} from 'lucide-react';

interface LiveDestination {
  place_id: string;
  name: string;
  address: string;
  locality: string;
  administrative_area: string;
  latitude: number;
  longitude: number;
  types: string[];
  categories: string[];
  rating: number | null;
  user_rating_count: number | null;
  data_source: string;
}

export const DestinationExplorer: React.FC = () => {
  usePageTitle('Explore Destinations | BudgetBound');
  const navigate = useNavigate();
  const [destinations, setDestinations] = useState<LiveDestination[]>([]);
  const [categories] = useState<string[]>([
    'Nature',
    'Adventure',
    'Beach',
    'Religious',
    'City Exploration',
    'Family',
    'Romantic'
  ]);
  
  const [loading, setLoading] = useState(false);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Pagination states
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 9;

  // Filters
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('Nature');

  const fetchDestinations = async () => {
    setLoading(true);
    setError(null);
    try {
      let response;
      
      // If search is provided, use text search; otherwise use category browse
      if (search.trim()) {
        response = await api.get('/api/destinations-live/search', {
          params: {
            q: search,
            limit: limit * page,  // Load incrementally
            category: category || undefined
          }
        });
        setDestinations(response.data.results || []);
        setTotal(response.data.count || 0);
        setPage(1);  // Reset pagination for text search
      } else {
        // Browse by category
        response = await api.get('/api/destinations-live/explore', {
          params: {
            category: category,
            page: page,
            limit: limit,
            search: undefined
          }
        });
        setDestinations(response.data.destinations || []);
        setTotal(response.data.total || 0);
      }
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.data?.detail || 
        'Failed to fetch live destinations. Please try again.'
      );
      setDestinations([]);
      setTotal(0);
    } finally {
      setLoading(false);
      setLoadingInitial(false);
    }
  };

  // Initial load with default category
  useEffect(() => {
    fetchDestinations();
  }, []);

  // When category changes (and no search), refetch
  useEffect(() => {
    if (!search.trim()) {
      setPage(1);
      fetchDestinations();
    }
  }, [category]);

  // When search changes, refetch
  useEffect(() => {
    if (search.trim() !== '') {
      const timer = setTimeout(() => {
        setPage(1);
        fetchDestinations();
      }, 500);  // Debounce search
      return () => clearTimeout(timer);
    }
  }, [search]);

  // When page changes, refetch
  useEffect(() => {
    if (!search.trim()) {
      fetchDestinations();
    }
  }, [page]);

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="flex flex-col gap-8">
      
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-paper-900 dark:text-white flex items-center gap-2">
            <Map className="text-marigold-600 animate-pulse" />
            Live Destination Explorer
          </h1>
          <p className="text-sm text-paper-500 dark:text-paper-400 mt-1">
            Discover real Indian destinations powered by live Geoapify data. Search, explore, and find your perfect getaway.
          </p>
        </div>
        <div className="bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-2 border border-blue-100 dark:border-blue-900/60 self-start sm:self-center">
          <Zap size={14} />
          <span>Live Data</span>
        </div>
      </div>

      <TripFlowGuide
        eyebrow="Discover in real-time"
        title="Live Destination Explorer now powered by Geoapify"
        description="Browse destinations across India using live geographic data. Search for places by name, explore by travel type (Nature, Adventure, Beach, etc.), and see real coordinates, ratings, and addresses from Geoapify."
        ctaLabel="Search or browse by category"
        steps={[
          { title: 'Browse by category', description: 'Select Nature, Adventure, Beach, or other travel types to see matching destinations.' },
          { title: 'Search by name', description: 'Type a destination name or address to find it instantly using live data.' },
          { title: 'View details', description: 'Click any destination to see more info, nearby attractions, and coordinates.' }
        ]}
      />

      {/* Filters Dashboard */}
      <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-5 shadow-sm">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-4 items-center">
          
          {/* Search */}
          <div className="lg:col-span-7 relative">
            <Search className="absolute left-3.5 top-3.5 text-paper-400" size={16} />
            <input 
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search destination name, address, or city..."
              className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl pl-10 pr-4 py-2.5 text-xs focus:outline-none focus:border-marigold-500 text-paper-900 dark:text-white transition-colors"
            />
          </div>

          {/* Category selection */}
          <div className="lg:col-span-5">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-marigold-500 text-paper-900 dark:text-white appearance-none"
            >
              {categories.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

        </div>
      </div>

      {/* Grid List */}
      {(loading && loadingInitial) && (
        <div className="min-h-[40vh] flex flex-col items-center justify-center text-paper-500 dark:text-paper-400 gap-4">
          <Loader className="h-8 w-8 text-marigold-500 animate-spin" />
          <span className="text-xs font-semibold">Loading live destinations...</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-600 rounded-xl flex items-start gap-3">
          <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-sm mb-1">Unable to load destinations</p>
            <p className="text-xs">{error}</p>
          </div>
          <button
            onClick={() => fetchDestinations()}
            className="text-xs font-semibold text-rose-700 hover:text-rose-900 whitespace-nowrap ml-4"
          >
            Retry
          </button>
        </div>
      )}

      {!loadingInitial && destinations.length === 0 && !error && (
        <div className="border border-dashed border-paper-200 dark:border-paper-700 rounded-2xl h-80 flex flex-col items-center justify-center text-center p-6 bg-paper-50/20 dark:bg-paper-800/10">
          <Map className="h-12 w-12 text-paper-300 dark:text-paper-600 mb-3" />
          <h3 className="text-sm font-bold text-paper-600 dark:text-paper-400 mb-1">No Destinations Found</h3>
          <p className="text-xs text-paper-400 max-w-xs leading-normal">
            Try adjusting your search or category filters. If searching by name, make sure the destination exists in India.
          </p>
        </div>
      )}

      {!loadingInitial && destinations.length > 0 && (
        <>
          {/* Destination Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {destinations.map((dest) => (
              <button 
                key={dest.place_id}
                onClick={() => {
                  // Navigate to unified detail view with query parameters for live destinations
                  const params = new URLSearchParams({
                    source: 'live',
                    name: dest.name,
                    address: dest.address || '',
                    state: dest.administrative_area || '',
                    lat: dest.latitude.toString(),
                    lon: dest.longitude.toString(),
                    rating: (dest.rating?.toString() || ''),
                    reviews: (dest.user_rating_count?.toString() || ''),
                    category
                  });
                  navigate(`/explorer/detail/${dest.place_id}?${params.toString()}`);
                }}
                className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl overflow-hidden shadow-sm hover:shadow-md hover:border-marigold-500/40 flex flex-col justify-between transition-all duration-200 group cursor-pointer text-left"
              >
                
                {/* Top banner */}
                <div className="bg-paper-100 dark:bg-paper-900/60 p-4 border-b border-paper-100 dark:border-paper-700 flex justify-between items-center">
                  <span className="text-[10px] text-blue-600 dark:text-blue-400 font-bold uppercase tracking-wider bg-blue-100 dark:bg-blue-950/40 px-2 py-0.5 rounded-full">
                    Geoapify
                  </span>
                  
                  {dest.rating && (
                    <div className="flex items-center gap-0.5 text-amber-500 text-xs">
                      <Star size={13} fill="currentColor" />
                      <span className="font-bold">{dest.rating.toFixed(1)}</span>
                    </div>
                  )}
                </div>

                {/* Middle details */}
                <div className="p-5 flex-1 space-y-3">
                  <div className="space-y-1">
                    {dest.administrative_area && (
                      <span className="text-[10px] text-paper-400 font-bold uppercase tracking-wide flex items-center gap-1">
                        <MapPin size={11} className="text-paper-400 shrink-0" />
                        {dest.administrative_area}
                      </span>
                    )}
                    <h3 className="text-lg font-bold text-paper-900 dark:text-white group-hover:text-marigold-600 dark:group-hover:text-marigold-400 transition-colors">
                      {dest.name}
                    </h3>
                  </div>

                  <p className="text-paper-500 dark:text-paper-400 text-xs line-clamp-2 leading-relaxed">
                    {dest.address || dest.locality || 'Location details'}
                  </p>

                  {dest.user_rating_count && (
                    <span className="text-[10px] text-paper-400">
                      {dest.user_rating_count} reviews
                    </span>
                  )}
                </div>

                {/* Coordinates footer */}
                <div className="px-5 py-3 border-t border-paper-100 dark:border-paper-700 bg-paper-50/50 dark:bg-paper-900/20 flex justify-between items-center text-xs">
                  <div className="text-[9px] text-paper-500">
                    <span className="block font-bold uppercase">Coordinates</span>
                    <span className="font-mono">{dest.latitude.toFixed(2)}, {dest.longitude.toFixed(2)}</span>
                  </div>
                  <div className="text-[9px] text-paper-400">
                    Live Data
                  </div>
                </div>

              </button>
            ))}
          </div>

          {/* Pagination Controls */}
          {total > limit && !search.trim() && (
            <div className="flex items-center justify-between border-t border-paper-200 dark:border-paper-700 pt-6">
              <span className="text-xs text-paper-500 dark:text-paper-400 font-medium">
                Showing <span className="font-bold text-paper-700 dark:text-white">{(page - 1) * limit + destinations.length}</span> of{' '}
                <span className="font-bold text-paper-700 dark:text-white">{total}</span> destinations (Page {page} of {totalPages})
              </span>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(prev => Math.max(prev - 1, 1))}
                  disabled={page === 1}
                  className="p-2 rounded-xl border border-paper-200 dark:border-paper-700 bg-paper-50 dark:bg-paper-800 text-paper-600 dark:text-paper-300 hover:bg-paper-50 dark:hover:bg-paper-700/50 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronLeft size={16} />
                </button>

                <button
                  onClick={() => setPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={page === totalPages}
                  className="p-2 rounded-xl border border-paper-200 dark:border-paper-700 bg-paper-50 dark:bg-paper-800 text-paper-600 dark:text-paper-300 hover:bg-paper-50 dark:hover:bg-paper-700/50 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronRight size={16} />
                </button>

              </div>
            </div>
          )}
        </>
      )}

    </div>
  );
};




