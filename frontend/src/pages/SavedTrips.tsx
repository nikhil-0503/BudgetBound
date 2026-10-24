import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import api from '../services/api';
import { 
  Search, 
  ArrowUpDown, 
  Briefcase, 
  Calendar, 
  Wallet, 
  TrendingUp, 
  TrendingDown, 
  Download, 
  Trash2, 
  Copy, 
  Edit3, 
  Eye, 
  AlertCircle, 
  Loader, 
  X,
  Compass,
  ArrowRight,
  Share2,
  CloudSun,
  Receipt
} from 'lucide-react';
import { ShareModal } from '../components/ShareModal';
import { EmptyState, SkeletonCard } from '../components/FeedbackStates';

interface Destination {
  id: number;
  name: string;
  state: string;
  category: string;
  weather_intelligence?: {
    current_season: string;
    season_rating: string;
  };
}

interface Trip {
  id: number;
  budget: number;
  days: number;
  travelers_count: number;
  travel_type: string;
  comfort_score: number;
  total_estimated_cost: number;
  status: string;
  start_date?: string;
  created_at: string;
  destination: Destination;
  actual_spending?: number;
  savings?: number;
  is_public?: boolean;
  share_token?: string | null;
}

export const SavedTrips: React.FC = () => {
  usePageTitle('My Trips | BudgetBound');
  const navigate = useNavigate();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingTripId, setDownloadingTripId] = useState<number | null>(null);

  // Search & Filters state
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('newest');

  // Edit Modal state
  const [editingTrip, setEditingTrip] = useState<Trip | null>(null);
  const [editBudget, setEditBudget] = useState(20000);
  const [editDays, setEditDays] = useState(4);
  const [editStartDate, setEditStartDate] = useState('');
  const [editStatus, setEditStatus] = useState('Planned');
  const [editTravelers, setEditTravelers] = useState(1);
  const [editType, setEditType] = useState('Nature');
  const [editComfort, setEditComfort] = useState(50);
  const [updating, setUpdating] = useState(false);
  const [activeShareTrip, setActiveShareTrip] = useState<Trip | null>(null);

  const fetchTrips = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/trips/');
      setTrips(response.data);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch your saved trip logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrips();
  }, []);

  const handleDelete = async (tripId: number) => {
    if (!window.confirm('Are you sure you want to permanently delete this travel plan? All logged expenses and itinerary logs will be deleted.')) {
      return;
    }
    try {
      await api.delete(`/api/trips/${tripId}`);
      setTrips(prev => prev.filter(t => t.id !== tripId));
    } catch (err) {
      console.error(err);
      alert('Failed to delete trip.');
    }
  };

  const handleDuplicate = async (tripId: number) => {
    try {
      setLoading(true);
      await api.post(`/api/trips/${tripId}/duplicate`);
      await fetchTrips();
    } catch (err) {
      console.error(err);
      alert('Failed to duplicate trip.');
      setLoading(false);
    }
  };

  const handleDownloadPDF = async (tripId: number, destName: string) => {
  const handleDownloadPDF = async (tripId: number, destName: string) => {
    setDownloadingTripId(tripId);
    try {
      const response = await api.get(`/api/trips/${tripId}/pdf`, {
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
      link.setAttribute('download', `budgetbound_${destName.replace(/\s+/g, '_').toLowerCase()}.pdf`);
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
      setDownloadingTripId(null);
    }
  };
  };

  const openEditModal = (trip: Trip) => {
    setEditingTrip(trip);
    setEditBudget(trip.budget);
    setEditDays(trip.days);
    setEditStartDate(trip.start_date || '');
    setEditStatus(trip.status);
    setEditTravelers(trip.travelers_count);
    setEditType(trip.travel_type);
    setEditComfort(trip.comfort_score);
  };

  const handleSaveEdit = async () => {
    if (!editingTrip) return;
    try {
      setUpdating(true);
      const response = await api.put(`/api/trips/${editingTrip.id}`, {
        budget: editBudget,
        days: editDays,
        start_date: editStartDate || null,
        status: editStatus,
        travelers_count: editTravelers,
        travel_type: editType,
        comfort_score: editComfort
      });
      
      // Update local state list
      setTrips(prev => prev.map(t => t.id === editingTrip.id ? response.data : t));
      setEditingTrip(null);
    } catch (err) {
      console.error(err);
      alert('Failed to update trip.');
    } finally {
      setUpdating(false);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'Draft':
        return 'bg-paper-100 text-paper-700 dark:bg-paper-900/50 dark:text-paper-400 border border-paper-200 dark:border-paper-800';
      case 'Planned':
        return 'bg-blue-50 text-blue-700 dark:bg-blue-950/20 dark:text-blue-400 border border-blue-100 dark:border-blue-900/30';
      case 'In Progress':
        return 'bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-400 border border-amber-100 dark:border-amber-900/30';
      case 'Completed':
        return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/30';
      case 'Cancelled':
        return 'bg-rose-50 text-rose-700 dark:bg-rose-950/20 dark:text-rose-400 border border-rose-100 dark:border-rose-900/30';
      default:
        return 'bg-paper-100 text-paper-700';
    }
  };

  // Filter & Sort computation
  const filteredTrips = trips.filter(trip => {
    const search = searchTerm.toLowerCase();
    // Safely access destination properties
    const destName = trip.destination?.name || "Unknown";
    const destState = trip.destination?.state || "";
    const travelType = trip.travel_type || "";
    
    return (
      destName.toLowerCase().includes(search) ||
      destState.toLowerCase().includes(search) ||
      travelType.toLowerCase().includes(search)
    );
  });

  const sortedTrips = [...filteredTrips].sort((a, b) => {
    switch (sortBy) {
      case 'newest':
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      case 'oldest':
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      case 'highest_budget':
        return b.budget - a.budget;
      case 'lowest_budget':
        return a.budget - b.budget;
      case 'dest_name':
        const nameA = a.destination?.name || "";
        const nameB = b.destination?.name || "";
        return nameA.localeCompare(nameB);
      default:
        return 0;
    }
  });

  if (loading && trips.length === 0) {
    return (
      <div className="space-y-8 max-w-6xl mx-auto p-6 md:p-10 animate-pulse">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2 w-1/3">
            <div className="h-4 bg-paper-200 dark:bg-paper-700 rounded-md w-1/2" />
            <div className="h-6 bg-paper-200 dark:bg-paper-700 rounded-md w-3/4" />
          </div>
          <div className="h-10 bg-paper-200 dark:bg-paper-700 rounded-md w-1/4" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="space-y-8 relative"
    >
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-marigold-600 dark:text-marigold-400 uppercase tracking-widest">Travel History</span>
          <h1 className="text-3xl font-extrabold text-paper-900 dark:text-white mt-1">My Saved Trips</h1>
          <p className="text-sm text-paper-500 dark:text-paper-400">
            View, duplicate, edit, or track expenses for all your finalized travel plans.
          </p>
        </div>
        <Link 
          to="/planner"
          className="inline-flex items-center gap-2 bg-marigold-600 hover:bg-marigold-500 text-white font-bold px-5 py-2.5 rounded-xl text-sm transition-all shadow-md shadow-marigold-600/15"
        >
          Plan New Destination
        </Link>
      </div>

      {/* Search & Sort Panel */}
      <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-4 rounded-2xl shadow-sm flex flex-col sm:flex-row gap-4 justify-between items-center">
        {/* Search */}
        <div className="relative w-full sm:max-w-xs">
          <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-paper-400 pointer-events-none">
            <Search size={16} />
          </span>
          <input
            type="text"
            placeholder="Search by destination..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-paper-200 dark:border-paper-700 rounded-xl text-xs bg-paper-50 dark:bg-paper-900 focus:outline-none focus:border-marigold-500 dark:focus:border-marigold-500 dark:text-white transition-all"
          />
        </div>

        {/* Sort dropdown */}
        <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
          <ArrowUpDown size={14} className="text-paper-400" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl text-xs px-3 py-2 text-paper-600 dark:text-paper-300 font-bold focus:outline-none transition-all"
          >
            <option value="newest">Sort: Newest</option>
            <option value="oldest">Sort: Oldest</option>
            <option value="highest_budget">Sort: Highest Budget</option>
            <option value="lowest_budget">Sort: Lowest Budget</option>
            <option value="dest_name">Sort: Destination Name</option>
          </select>
        </div>
      </div>

      {/* Trips Grid list */}
      {sortedTrips.length === 0 ? (
        <EmptyState
          icon={<Compass size={24} />}
          title="No Saved Trips Found"
          description="Create or generate budget-allocated schedules to populate this log ledger list. You can start planning or discovery from the Planner."
          actionLabel="Plan a Trip Now"
          onAction={() => navigate('/planner')}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedTrips.map((trip) => {
            const actualSpent = trip.actual_spending || 0.0;
            const savings = trip.savings || 0.0;
            
            return (
              <div 
                key={trip.id} 
                className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
              >
                {/* Image / Destination details */}
                <div className="p-5 border-b border-paper-100 dark:border-paper-700 flex justify-between items-start">
                  <div>
                    <span className="text-[9px] text-paper-400 font-bold uppercase tracking-wider block">{trip.destination?.state || "Unknown"}</span>
                    <h3 className="text-lg font-extrabold text-paper-900 dark:text-white mt-0.5">{trip.destination?.name || "Unknown Destination"}</h3>
                    <div className="flex gap-2 items-center mt-1">
                      <span className="text-[10px] bg-paper-100 dark:bg-paper-900 text-paper-500 dark:text-paper-400 px-1.5 py-0.2 rounded font-semibold uppercase">
                        {trip.travel_type}
                      </span>
                      <span className="text-[9px] text-paper-400 font-bold uppercase tracking-wide">
                        {trip.days} Days / {trip.travelers_count} Travelers
                      </span>
                    </div>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${getStatusBadgeClass(trip.status)}`}>
                    {trip.status}
                  </span>
                </div>

                {/* Travel Date */}
                <div className="px-5 py-3.5 bg-paper-50/50 dark:bg-paper-900/10 border-b border-paper-100 dark:border-paper-700/60 flex items-center gap-2 text-xs text-paper-500 dark:text-paper-400">
                  <Calendar size={14} className="text-marigold-500 shrink-0" />
                  <span className="font-medium">
                    {trip.start_date ? `Starts: ${trip.start_date}` : 'Planned dates not set'}
                  </span>
                </div>

                {/* Weather Quick Badge */}
                {trip.destination?.weather_intelligence && (
                  <div className="px-5 py-2.5 bg-paper-50/20 dark:bg-paper-900/5 border-b border-paper-100 dark:border-paper-700/60 flex items-center justify-between text-[11px]">
                    <span className="text-paper-400 font-semibold flex items-center gap-1">
                      <CloudSun size={13} className="text-marigold-500" />
                      Season: {trip.destination.weather_intelligence.current_season}
                    </span>
                    <span className={`font-bold px-2 py-0.5 rounded-full text-[9px] border ${
                      trip.destination.weather_intelligence.season_rating === 'Excellent' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400 border-emerald-200' :
                      trip.destination.weather_intelligence.season_rating === 'Good' ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-400 border-blue-200' :
                      trip.destination.weather_intelligence.season_rating === 'Fair' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400 border-amber-200' :
                      'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400 border-rose-200'
                    }`}>
                      {trip.destination.weather_intelligence.season_rating}
                    </span>
                  </div>
                )}

                {/* Costs Summary Grid */}
                <div className="p-5 grid grid-cols-2 gap-4 text-xs border-b border-paper-100 dark:border-paper-700/60 bg-paper-50 dark:bg-paper-800">
                  <div className="space-y-0.5">
                    <span className="text-paper-400 block font-semibold">Total Target Budget</span>
                    <span className="font-extrabold text-paper-800 dark:text-white">₹{trip.budget.toLocaleString()}</span>
                  </div>
                  <div className="space-y-0.5">
                    <span className="text-paper-400 block font-semibold">Estimated Cost</span>
                    <span className="font-extrabold text-paper-700 dark:text-paper-300">₹{trip.total_estimated_cost.toLocaleString()}</span>
                  </div>
                  <div className="space-y-0.5">
                    <span className="text-paper-400 block font-semibold">Actual Spending</span>
                    <span className="font-extrabold text-rose-500">₹{actualSpent.toLocaleString()}</span>
                  </div>
                  <div className="space-y-0.5">
                    <span className="text-paper-400 block font-semibold">Trip Savings</span>
                    <span className="font-extrabold text-emerald-500">₹{savings.toLocaleString()}</span>
                  </div>
                </div>

                {/* Interactive Actions Footer */}
                <div className="p-3 bg-paper-50/50 dark:bg-paper-900/15 flex items-center justify-between gap-1">
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => navigate(`/planner?tripId=${trip.id}`)}
                      className="p-2 bg-paper-50 dark:bg-paper-700 rounded-xl hover:bg-paper-100 dark:hover:bg-paper-600 text-paper-700 dark:text-white transition-all shadow-sm border border-paper-200 dark:border-paper-700"
                      title="View Planner Details"
                    >
                      <Eye size={13} />
                    </button>
                    <button
                      onClick={() => navigate(`/expenses/${trip.id}`)}
                      className="p-2 bg-paper-50 dark:bg-paper-700 rounded-xl hover:bg-paper-100 dark:hover:bg-paper-600 text-paper-700 dark:text-white transition-all shadow-sm border border-paper-200 dark:border-paper-700"
                      title="Manage Expenses"
                    >
                      <Receipt size={13} />
                    </button>
                    <button
                      onClick={() => openEditModal(trip)}
                      className="p-2 bg-paper-50 dark:bg-paper-700 rounded-xl hover:bg-paper-100 dark:hover:bg-paper-600 text-paper-700 dark:text-white transition-all shadow-sm border border-paper-200 dark:border-paper-700"
                      title="Edit Basic Metadata"
                    >
                      <Edit3 size={13} />
                    </button>
                    <button
                      onClick={() => handleDuplicate(trip.id)}
                      className="p-2 bg-paper-50 dark:bg-paper-700 rounded-xl hover:bg-paper-100 dark:hover:bg-paper-600 text-paper-700 dark:text-white transition-all shadow-sm border border-paper-200 dark:border-paper-700"
                      title="Duplicate Trip"
                    >
                      <Copy size={13} />
                    </button>
                    <button
                      onClick={() => setActiveShareTrip(trip)}
                      className="p-2 bg-paper-50 dark:bg-paper-700 rounded-xl hover:bg-paper-100 dark:hover:bg-paper-600 text-paper-700 dark:text-white transition-all shadow-sm border border-paper-200 dark:border-paper-700"
                      title="Share Trip Plan"
                    >
                      <Share2 size={13} />
                    </button>
                    <button
                      onClick={() => handleDownloadPDF(trip.id, trip.destination.name)}
                      disabled={downloadingTripId === trip.id}
                      className="p-2 bg-paper-50 dark:bg-paper-700 rounded-xl hover:bg-paper-100 dark:hover:bg-paper-600 text-paper-700 dark:text-white transition-all shadow-sm border border-paper-200 dark:border-paper-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Download PDF"
                    >
                      {downloadingTripId === trip.id ? <Loader size={13} className="animate-spin" /> : <Download size={13} />}
                    </button>
                  </div>

                  <button
                    onClick={() => handleDelete(trip.id)}
                    className="p-2 rounded-xl bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/20 dark:hover:bg-rose-900/30 text-rose-600 dark:text-rose-400 transition-all border border-rose-100/50 dark:border-rose-900/10"
                    title="Delete Plan"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Edit Trip Modal Popup */}
      {editingTrip && (
        <div className="fixed inset-0 bg-paper-900/60 backdrop-blur-sm flex items-center justify-center p-6 z-50 animate-fade-in">
          <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
            <button 
              onClick={() => setEditingTrip(null)}
              className="absolute top-4 right-4 text-paper-400 hover:text-paper-600 dark:hover:text-white focus:outline-none"
            >
              <X size={18} />
            </button>

            <h3 className="font-extrabold text-base text-paper-900 dark:text-white mb-4">
              Edit Trip: {editingTrip.destination.name}
            </h3>

            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-paper-500 font-bold mb-1.5 uppercase tracking-wide">Target Budget (INR)</label>
                <input
                  type="number"
                  value={editBudget}
                  onChange={(e) => setEditBudget(Number(e.target.value))}
                  className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2.5 bg-paper-50 dark:bg-paper-900 dark:text-white focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-paper-500 font-bold mb-1.5 uppercase tracking-wide">Duration (Days)</label>
                  <input
                    type="number"
                    value={editDays}
                    onChange={(e) => setEditDays(Number(e.target.value))}
                    className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2.5 bg-paper-50 dark:bg-paper-900 dark:text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-paper-500 font-bold mb-1.5 uppercase tracking-wide">Travelers</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={editTravelers}
                    onChange={(e) => setEditTravelers(parseInt(e.target.value) || 1)}
                    className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2.5 bg-paper-50 dark:bg-paper-900 dark:text-white focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-paper-500 font-bold mb-1.5 uppercase tracking-wide">Travel Date</label>
                  <input
                    type="date"
                    value={editStartDate}
                    onChange={(e) => setEditStartDate(e.target.value)}
                    className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2.5 bg-paper-50 dark:bg-paper-900 dark:text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-paper-500 font-bold mb-1.5 uppercase tracking-wide">Trip Lifecycle</label>
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value)}
                    className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2.5 bg-paper-50 dark:bg-paper-900 dark:text-white focus:outline-none font-bold"
                  >
                    {["Draft", "Planned", "In Progress", "Completed", "Cancelled"].map((st) => (
                      <option key={st} value={st}>{st}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-paper-500 font-bold mb-1.5 uppercase tracking-wide">Travel Style</label>
                  <select
                    value={editType}
                    onChange={(e) => setEditType(e.target.value)}
                    className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2.5 bg-paper-50 dark:bg-paper-900 dark:text-white focus:outline-none font-bold"
                  >
                    {['Nature', 'Adventure', 'Family', 'Religious', 'Beach', 'City Exploration', 'Romantic', 'Solo'].map((st) => (
                      <option key={st} value={st}>{st}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-paper-500 font-bold mb-1.5 uppercase tracking-wide">Comfort Score (0-100)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={editComfort}
                    onChange={(e) => setEditComfort(Number(e.target.value))}
                    className="w-full border border-paper-200 dark:border-paper-700 rounded-xl p-2.5 bg-paper-50 dark:bg-paper-900 dark:text-white focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                type="button"
                onClick={() => setEditingTrip(null)}
                className="px-4 py-2 border border-paper-200 dark:border-paper-700 rounded-xl font-bold text-xs text-paper-500 hover:text-paper-800 dark:hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveEdit}
                disabled={updating}
                className="px-4 py-2 bg-marigold-600 hover:bg-marigold-500 text-white font-bold rounded-xl text-xs transition-colors"
              >
                {updating ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {activeShareTrip && (
        <ShareModal
          tripId={activeShareTrip.id}
          isPublic={activeShareTrip.is_public || false}
          shareToken={activeShareTrip.share_token || null}
          onClose={() => setActiveShareTrip(null)}
          onUpdate={(updatedTrip) => {
            setTrips(prev => prev.map(t => t.id === activeShareTrip.id ? {
              ...t,
              is_public: updatedTrip.is_public,
              share_token: updatedTrip.share_token
            } : t));
            setActiveShareTrip(null);
          }}
        />
      )}
    </motion.div>
  );
};



