import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { 
  Map, 
  Search, 
  Star, 
  MapPin, 
  Loader, 
  AlertCircle,
  ChevronLeft,
  ChevronRight
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
}

export const DestinationExplorer: React.FC = () => {
  const navigate = useNavigate();
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [states, setStates] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Pagination states
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 9;

  // Filters
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [state, setState] = useState('');
  const [maxBudget, setMaxBudget] = useState<number | ''>('');

  const fetchFilters = async () => {
    try {
      const [statesRes, catsRes] = await Promise.all([
        api.get('/api/destinations/states'),
        api.get('/api/destinations/categories')
      ]);
      setStates(statesRes.data);
      setCategories(catsRes.data);
    } catch (e) {
      console.error("Failed to load filter choices", e);
    }
  };

  const fetchDestinations = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/api/destinations/', {
        params: {
          search: search || undefined,
          category: category || undefined,
          state: state || undefined,
          max_budget: maxBudget || undefined,
          page: page,
          limit: limit
        }
      });
      setDestinations(response.data.destinations);
      setTotal(response.data.total);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch destinations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFilters();
  }, []);

  // Reset page to 1 whenever filters change
  useEffect(() => {
    setPage(1);
  }, [search, category, state, maxBudget]);

  // Refetch when filters or page changes
  useEffect(() => {
    fetchDestinations();
  }, [search, category, state, maxBudget, page]);

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="flex flex-col gap-8">
      
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <Map className="text-violet-600 animate-pulse" />
            Destination Explorer
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Browse through our curated list of handpicked Indian destinations with average costs and attractions.
          </p>
        </div>
        <div className="bg-violet-50 dark:bg-violet-950/40 text-violet-700 dark:text-violet-400 font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-2 border border-violet-100 dark:border-violet-900/60 self-start sm:self-center">
          <span>Total Seeded:</span>
          <span className="bg-violet-600 text-white px-2 py-0.5 rounded-full text-[10px]">{total}</span>
        </div>
      </div>

      {/* Filters Dashboard */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-4 items-center">
          
          {/* Search */}
          <div className="lg:col-span-4 relative">
            <Search className="absolute left-3.5 top-3.5 text-slate-400" size={16} />
            <input 
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search destination, description or state..."
              className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-xs focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white transition-colors"
            />
          </div>

          {/* Category selection */}
          <div className="lg:col-span-3">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white appearance-none"
            >
              <option value="">All Categories</option>
              {categories.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* State selection */}
          <div className="lg:col-span-3">
            <select
              value={state}
              onChange={(e) => setState(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white appearance-none"
            >
              <option value="">All States</option>
              {states.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Max Stay Cost per day */}
          <div className="lg:col-span-2">
            <input 
              type="number"
              value={maxBudget}
              onChange={(e) => setMaxBudget(e.target.value ? Number(e.target.value) : '')}
              placeholder="Max Stay Cost (Daily)"
              className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white transition-colors"
            />
          </div>

        </div>
      </div>

      {/* Grid List */}
      {loading && (
        <div className="min-h-[40vh] flex flex-col items-center justify-center text-slate-500 dark:text-slate-400 gap-4">
          <Loader className="h-8 w-8 text-violet-500 animate-spin" />
          <span className="text-xs font-semibold">Loading destinations...</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-600 rounded-xl flex items-center gap-2">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {!loading && destinations.length === 0 && (
        <div className="border border-dashed border-slate-200 dark:border-slate-700 rounded-2xl h-80 flex flex-col items-center justify-center text-center p-6 bg-slate-50/20 dark:bg-slate-800/10">
          <Map className="h-12 w-12 text-slate-300 dark:text-slate-600 mb-3" />
          <h3 className="text-sm font-bold text-slate-600 dark:text-slate-400 mb-1">No Matching Destinations</h3>
          <p className="text-xs text-slate-400 max-w-xs leading-normal">
            No Indian getaways fit your current search query. Try clearing your filters or widening search parameters.
          </p>
        </div>
      )}

      {!loading && destinations.length > 0 && (
        <>
          {/* Destination Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {destinations.map((dest) => (
              <div 
                key={dest.id}
                onClick={() => navigate(`/explorer/${dest.id}`)}
                className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl overflow-hidden shadow-sm hover:shadow-md hover:border-violet-500/40 cursor-pointer flex flex-col justify-between transition-all duration-200 group"
              >
                
                {/* Top banner representing category */}
                <div className="bg-slate-100 dark:bg-slate-900/60 p-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
                  <span className="text-[10px] text-violet-600 dark:text-violet-400 font-bold uppercase tracking-wider bg-violet-100 dark:bg-violet-950/40 px-2 py-0.5 rounded-full">
                    {dest.category}
                  </span>
                  
                  <div className="flex items-center gap-0.5 text-amber-500 text-xs">
                    <Star size={13} fill="currentColor" />
                    <span className="font-bold">{dest.rating}</span>
                  </div>
                </div>

                {/* Middle details */}
                <div className="p-5 flex-1 space-y-3">
                  <div className="space-y-1">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wide flex items-center gap-1">
                      <MapPin size={11} className="text-slate-400 shrink-0" />
                      {dest.state}
                    </span>
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
                      {dest.name}
                    </h3>
                  </div>

                  <p className="text-slate-500 dark:text-slate-400 text-xs line-clamp-3 leading-relaxed">
                    {dest.description}
                  </p>
                </div>

                {/* Pricing footprint */}
                <div className="px-5 py-4 border-t border-slate-100 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/20 flex justify-between items-center text-xs">
                  <div>
                    <span className="text-[9px] text-slate-400 block font-bold uppercase">Lodging / Night (Avg)</span>
                    <span className="font-bold text-slate-800 dark:text-white">₹{dest.avg_hotel_cost.toLocaleString()}</span>
                  </div>

                  <div>
                    <span className="text-[9px] text-slate-400 block font-bold uppercase">Transit Fare (Avg)</span>
                    <span className="font-bold text-slate-800 dark:text-white">₹{dest.avg_travel_cost.toLocaleString()}</span>
                  </div>
                </div>

              </div>
            ))}
          </div>

          {/* Pagination Controls */}
          <div className="flex items-center justify-between border-t border-slate-200 dark:border-slate-700 pt-6">
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              Showing <span className="font-bold text-slate-700 dark:text-white">{destinations.length}</span> of{' '}
              <span className="font-bold text-slate-700 dark:text-white">{total}</span> destinations (Page {page} of {totalPages})
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(prev => Math.max(prev - 1, 1))}
                disabled={page === 1}
                className="p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              >
                <ChevronLeft size={16} />
              </button>

              <button
                onClick={() => setPage(prev => Math.min(prev + 1, totalPages))}
                disabled={page === totalPages}
                className="p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </>
      )}

    </div>
  );
};
