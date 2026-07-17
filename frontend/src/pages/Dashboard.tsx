import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { BudgetHealthMeter } from '../components/BudgetHealthMeter';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  Legend 
} from 'recharts';
import { 
  Wallet, 
  Compass, 
  TrendingUp, 
  Trash2, 
  ArrowRight, 
  AlertCircle, 
  Eye, 
  PlusCircle, 
  Percent, 
  Loader 
} from 'lucide-react';

interface RecentTrip {
  id: number;
  destination: string;
  state: string;
  budget: number;
  estimated_cost: number;
  days: number;
  category: string;
  date: string;
  status?: string;
  start_date?: string;
}

interface BudgetUsagePoint {
  name: string;
  budget: number;
  estimated: number;
  actual: number;
}

interface CategoryExpensePoint {
  name: string;
  value: number;
}

interface DashboardStats {
  total_trips: number;
  planned_budget: number;
  actual_expenses: number;
  savings: number;
  trips_planned: number;
  trips_in_progress: number;
  trips_completed: number;
  trips_cancelled: number;
  trips_draft: number;
  recent_trips: RecentTrip[];
  upcoming_trips: RecentTrip[];
  budget_usage_chart: BudgetUsagePoint[];
  category_chart: CategoryExpensePoint[];
}

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { darkMode } = useTheme();
  const navigate = useNavigate();
  
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [latestTripStats, setLatestTripStats] = useState<any | null>(null);
  const [latestTripDetails, setLatestTripDetails] = useState<any | null>(null);

  const fetchLatestTripData = async (tripId: number) => {
    try {
      const [detailsRes, statsRes] = await Promise.all([
        api.get(`/api/trips/${tripId}`),
        api.get(`/api/expenses/trip/${tripId}/stats`)
      ]);
      setLatestTripDetails(detailsRes.data);
      setLatestTripStats(statsRes.data);
    } catch (err) {
      console.error("Failed to load latest trip details for dashboard forecast:", err);
    }
  };

  // Fetch Dashboard Stats on load
  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/dashboard/stats');
      setStats(response.data);
      if (response.data.recent_trips && response.data.recent_trips.length > 0) {
        await fetchLatestTripData(response.data.recent_trips[0].id);
      }
    } catch (err: any) {
      console.error(err);
      setError('Failed to load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleDeleteTrip = async (tripId: number) => {
    if (!window.confirm('Are you sure you want to delete this trip? All logged expenses and itineraries will be permanently removed.')) {
      return;
    }

    try {
      await api.delete(`/api/trips/${tripId}`);
      // Refresh statistics
      fetchStats();
    } catch (err: any) {
      console.error(err);
      alert('Failed to delete trip.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-slate-500 dark:text-slate-400 gap-4">
        <Loader className="h-10 w-10 text-violet-500 animate-spin" />
        <span className="text-sm font-semibold">Analyzing your travel dashboard...</span>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 rounded-2xl flex items-center gap-3">
        <AlertCircle size={24} />
        <div>
          <h3 className="font-bold">Error loading dashboard</h3>
          <p className="text-xs mt-0.5">{error || 'Something went wrong.'}</p>
        </div>
      </div>
    );
  }

  // Visual Colors for Charts
  const COLORS = ['#6d28d9', '#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="flex flex-col gap-8"
    >
      
      {/* Welcome header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-violet-600 dark:text-violet-400 uppercase tracking-widest">Travel Hub</span>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white mt-1">
            Welcome Back, {user?.name || 'Explorer'}!
          </h1>
        </div>
        <Link 
          to="/planner"
          className="inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white font-bold px-5 py-2.5 rounded-xl text-sm transition-all shadow-md shadow-violet-600/15"
        >
          <PlusCircle size={16} />
          Plan New Trip
        </Link>
      </div>

      {/* Core Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Total Trips */}
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-6 rounded-2xl shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 font-bold uppercase">Total Trips</span>
            <h3 className="text-3xl font-extrabold text-slate-900 dark:text-white">{stats.total_trips}</h3>
          </div>
          <div className="h-12 w-12 rounded-xl bg-violet-100 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400 flex items-center justify-center">
            <Compass size={24} />
          </div>
        </div>

        {/* Planned Budget */}
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-6 rounded-2xl shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 font-bold uppercase">Allocated Budget</span>
            <h3 className="text-2xl font-extrabold text-slate-900 dark:text-white">₹{stats.planned_budget.toLocaleString()}</h3>
          </div>
          <div className="h-12 w-12 rounded-xl bg-indigo-100 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
            <Wallet size={24} />
          </div>
        </div>

        {/* Actual Expenses */}
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-6 rounded-2xl shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 font-bold uppercase">Spent So Far</span>
            <h3 className="text-2xl font-extrabold text-slate-900 dark:text-white">₹{stats.actual_expenses.toLocaleString()}</h3>
          </div>
          <div className="h-12 w-12 rounded-xl bg-rose-100 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 flex items-center justify-center">
            <TrendingUp size={24} />
          </div>
        </div>

        {/* Savings */}
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-6 rounded-2xl shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 font-bold uppercase">Calculated Savings</span>
            <h3 className="text-2xl font-extrabold text-slate-900 dark:text-white">₹{stats.savings.toLocaleString()}</h3>
          </div>
          <div className="h-12 w-12 rounded-xl bg-emerald-100 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
            <Percent size={24} />
          </div>
        </div>
      </div>

      {/* Status Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-6">
        {/* Planned */}
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-xl shadow-sm flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 font-bold block uppercase">Planned</span>
            <h4 className="text-xl font-extrabold text-slate-900 dark:text-white mt-0.5">{stats.trips_planned || 0}</h4>
          </div>
          <div className="h-8 w-8 rounded-lg bg-blue-100 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-[10px]">
            PL
          </div>
        </div>
        {/* In Progress */}
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-xl shadow-sm flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 font-bold block uppercase">In Progress</span>
            <h4 className="text-xl font-extrabold text-slate-900 dark:text-white mt-0.5">{stats.trips_in_progress || 0}</h4>
          </div>
          <div className="h-8 w-8 rounded-lg bg-amber-100 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 flex items-center justify-center font-bold text-[10px]">
            IP
          </div>
        </div>
        {/* Completed */}
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-xl shadow-sm flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 font-bold block uppercase">Completed</span>
            <h4 className="text-xl font-extrabold text-slate-900 dark:text-white mt-0.5">{stats.trips_completed || 0}</h4>
          </div>
          <div className="h-8 w-8 rounded-lg bg-emerald-100 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-[10px]">
            CO
          </div>
        </div>
        {/* Cancelled */}
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-xl shadow-sm flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 font-bold block uppercase">Cancelled</span>
            <h4 className="text-xl font-extrabold text-slate-900 dark:text-white mt-0.5">{stats.trips_cancelled || 0}</h4>
          </div>
          <div className="h-8 w-8 rounded-lg bg-rose-100 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 flex items-center justify-center font-bold text-[10px]">
            CA
          </div>
        </div>
        {/* Draft */}
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-xl shadow-sm flex items-center justify-between col-span-2 lg:col-span-1">
          <div>
            <span className="text-[10px] text-slate-400 font-bold block uppercase">Drafts</span>
            <h4 className="text-xl font-extrabold text-slate-900 dark:text-white mt-0.5">{stats.trips_draft || 0}</h4>
          </div>
          <div className="h-8 w-8 rounded-lg bg-slate-100 dark:bg-slate-900 text-slate-500 dark:text-slate-400 flex items-center justify-center font-bold text-[10px]">
            DR
          </div>
        </div>
      </div>

      {/* Latest Trip Budget Health & Predictions Forecast */}
      {stats.total_trips > 0 && latestTripDetails && latestTripStats && (
        <div className="bg-slate-50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-700 rounded-3xl p-6 flex flex-col gap-6 shadow-sm animate-fade-in">
          <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
            <h2 className="text-base font-extrabold text-slate-800 dark:text-white uppercase tracking-wider">
              Latest Travel Forecast: {latestTripDetails.destination.name}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">Budget health and predictions for your upcoming trip</p>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <BudgetHealthMeter
              budget={latestTripDetails.budget}
              estimatedCost={latestTripDetails.total_estimated_cost}
              actualExpenses={latestTripStats.total_actual}
              className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
            
            {/* Predictions widget */}
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm flex flex-col justify-between gap-4">
              <div>
                <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-800 dark:text-white">
                  Live Financial Forecast
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">Real-time spend pacing and projections</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="space-y-0.5">
                  <span className="text-slate-400 dark:text-slate-500 font-semibold block">Remaining Budget</span>
                  <span className={`font-bold ${latestTripStats.remaining_budget >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                    ₹{latestTripStats.remaining_budget ? latestTripStats.remaining_budget.toLocaleString() : '0'}
                  </span>
                </div>
                
                <div className="space-y-0.5">
                  <span className="text-slate-400 dark:text-slate-500 font-semibold block">Current Burn Rate</span>
                  <span className="font-bold text-slate-700 dark:text-slate-300">
                    ₹{latestTripStats.daily_burn_rate ? latestTripStats.daily_burn_rate.toLocaleString(undefined, { maximumFractionDigits: 1 }) : '0'}/day
                  </span>
                </div>
                
                <div className="space-y-0.5">
                  <span className="text-slate-400 dark:text-slate-500 font-semibold block">Projected Spend</span>
                  <span className="font-bold text-slate-700 dark:text-slate-300">
                    ₹{latestTripStats.projected_final_spend ? latestTripStats.projected_final_spend.toLocaleString() : '0'}
                  </span>
                </div>
                
                <div className="space-y-0.5">
                  <span className="text-slate-400 dark:text-slate-500 font-semibold block">Forecast Status</span>
                  <span className={`inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full mt-1 ${
                    latestTripStats.prediction_status === "Likely to stay within budget"
                      ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400'
                      : 'bg-rose-100 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400'
                  }`}>
                    {latestTripStats.prediction_status || 'Pacing okay'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {stats.total_trips === 0 ? (
        /* Empty State */
        <div className="bg-white dark:bg-slate-800 border border-dashed border-slate-200 dark:border-slate-700 rounded-3xl p-12 text-center shadow-sm flex flex-col items-center justify-center">
          <Compass className="h-20 w-20 text-slate-300 dark:text-slate-600 mb-6 animate-spin-slow" />
          <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Your Travel Log is Empty</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mb-8 leading-relaxed">
            Create your first travel itinerary using our budget allocator slider tool to map transport, accommodations, and local sights.
          </p>
          <Link 
            to="/planner"
            className="inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white font-bold px-8 py-3.5 rounded-xl transition-all shadow-lg shadow-violet-600/15"
          >
            Create Your First Plan
            <ArrowRight size={18} />
          </Link>
        </div>
      ) : (
        /* Charts & Table Columns */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Panel: Budget Chart & Trips list */}
          <div className="lg:col-span-8 flex flex-col gap-8">
            
            {/* Chart 1: Budget Usage */}
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
              <h3 className="text-base font-bold text-slate-800 dark:text-white mb-6">Budget vs Cost Comparison</h3>
              <div className="h-72 w-full text-xs">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.budget_usage_chart} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:stroke-slate-700" />
                    <XAxis dataKey="name" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip 
                      contentStyle={{ 
                        background: darkMode ? '#1e293b' : 'rgba(255,255,255,0.9)', 
                        border: darkMode ? '1px solid #475569' : '1px solid #cbd5e1',
                        color: darkMode ? '#f8fafc' : '#0f172a',
                        borderRadius: '12px' 
                      }} 
                      itemStyle={{
                        color: darkMode ? '#f8fafc' : '#0f172a'
                      }}
                    />
                    <Legend wrapperStyle={{ paddingTop: '10px' }} />
                    <Bar name="Target Budget" dataKey="budget" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                    <Bar name="Estimated Cost" dataKey="estimated" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    <Bar name="Actual Expenses" dataKey="actual" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Recent Trips Table */}
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
              <h3 className="text-base font-bold text-slate-800 dark:text-white mb-6">Recent Travel Plans</h3>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-100 dark:border-slate-700 text-slate-400 font-bold uppercase tracking-wider">
                      <th className="pb-4">Destination</th>
                      <th className="pb-4">Budget</th>
                      <th className="pb-4">Est. Cost</th>
                      <th className="pb-4">Duration</th>
                      <th className="pb-4">Category</th>
                      <th className="pb-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60 font-medium">
                    {stats.recent_trips.map((trip) => (
                      <tr key={trip.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors">
                        <td className="py-4">
                          <div className="flex flex-col">
                            <span className="font-bold text-slate-800 dark:text-white">{trip.destination}</span>
                            <span className="text-[10px] text-slate-400">{trip.state}</span>
                          </div>
                        </td>
                        <td className="py-4 text-slate-600 dark:text-slate-300">₹{trip.budget.toLocaleString()}</td>
                        <td className="py-4 text-slate-900 dark:text-white font-semibold">₹{trip.estimated_cost.toLocaleString()}</td>
                        <td className="py-4 text-slate-500 dark:text-slate-400">{trip.days} Days</td>
                        <td className="py-4">
                          <span className="bg-violet-100 dark:bg-violet-950/40 text-violet-700 dark:text-violet-400 text-[10px] font-bold px-2 py-0.5 rounded-full">
                            {trip.category}
                          </span>
                        </td>
                        <td className="py-4 text-right">
                          <div className="flex items-center justify-end gap-2.5">
                            <button 
                              onClick={() => {
                                // Prefecture prefills to planner
                                sessionStorage.setItem('prefilled_planner', JSON.stringify({
                                  startingCity: 'Your City',
                                  budget: trip.budget,
                                  days: trip.days,
                                  travelType: trip.category,
                                  travelersCount: 1,
                                  destName: trip.destination
                                }));
                                navigate('/planner');
                              }}
                              className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 dark:bg-slate-700/40 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-all"
                              title="View Details / Re-simulate"
                            >
                              <Eye size={14} />
                            </button>

                            <button 
                              onClick={() => navigate(`/expenses/${trip.id}`)}
                              className="p-2 rounded-lg bg-violet-50 hover:bg-violet-100 dark:bg-violet-950/20 dark:hover:bg-violet-900/30 text-violet-600 dark:text-violet-400 transition-all font-bold"
                              title="Expenses Tracker"
                            >
                              Track
                            </button>

                            <button 
                              onClick={() => navigate(`/optimizer/${trip.id}`)}
                              className="p-2 rounded-lg bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/20 dark:hover:bg-amber-900/30 text-amber-600 dark:text-amber-400 transition-all font-bold"
                              title="Optimizer"
                            >
                              Optimize
                            </button>

                            <button 
                              onClick={() => handleDeleteTrip(trip.id)}
                              className="p-2 rounded-lg bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/20 dark:hover:bg-rose-900/30 text-rose-600 dark:text-rose-400 transition-all"
                              title="Delete Plan"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

          </div>

          {/* Right Panel: Expense Category Breakdown */}
          <div className="lg:col-span-4 flex flex-col gap-8">
            
            {/* Pie Chart: Expense Categories */}
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
              <h3 className="text-base font-bold text-slate-800 dark:text-white mb-6">Expense Distribution</h3>
              
              <div className="h-64 w-full text-xs">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={stats.category_chart}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {stats.category_chart.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ 
                        background: darkMode ? '#1e293b' : 'rgba(255,255,255,0.9)', 
                        border: darkMode ? '1px solid #475569' : '1px solid #cbd5e1',
                        color: darkMode ? '#f8fafc' : '#0f172a',
                        borderRadius: '12px' 
                      }}
                      itemStyle={{
                        color: darkMode ? '#f8fafc' : '#0f172a'
                      }}
                      formatter={(value) => [`₹${Number(value).toLocaleString()}`, 'Spent']}
                    />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Legend Summary */}
              {stats.actual_expenses > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700 flex flex-col gap-2.5 text-[11px] text-slate-500 dark:text-slate-400">
                  <span className="font-bold text-slate-700 dark:text-slate-300 uppercase">Expense Summary</span>
                  <div className="flex justify-between items-center">
                    <span>Average trip spent:</span>
                    <span className="font-bold text-slate-900 dark:text-white">₹{(stats.actual_expenses / stats.total_trips).toFixed(0)}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Upcoming Trips List */}
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
              <h3 className="text-sm font-extrabold text-slate-800 dark:text-white mb-4 uppercase tracking-wider">Upcoming Trips</h3>
              
              {(!stats.upcoming_trips || stats.upcoming_trips.length === 0) ? (
                <p className="text-xs text-slate-400 italic">No upcoming planned trips found.</p>
              ) : (
                <div className="flex flex-col gap-3">
                  {stats.upcoming_trips.map((trip) => (
                    <div 
                      key={trip.id} 
                      onClick={() => navigate(`/planner?tripId=${trip.id}`)}
                      className="p-3 bg-slate-50 dark:bg-slate-900/50 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-150 dark:border-slate-700 rounded-xl flex justify-between items-center cursor-pointer transition-all hover:translate-x-1"
                    >
                      <div className="flex flex-col gap-0.5">
                        <span className="font-bold text-xs text-slate-800 dark:text-white">{trip.destination}</span>
                        <span className="text-[10px] text-slate-400">
                          {trip.start_date ? `Starts: ${trip.start_date}` : `${trip.days} Days / ${trip.category}`}
                        </span>
                      </div>
                      <div className="text-right flex flex-col items-end gap-1">
                        <span className="text-[10px] font-bold text-slate-800 dark:text-white">₹{trip.budget.toLocaleString()}</span>
                        <span className="text-[9px] font-bold px-1.5 py-0.2 bg-blue-50 dark:bg-blue-950/20 text-blue-600 dark:text-blue-450 rounded">
                          {trip.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Tips Box */}
            <div className="bg-slate-900 dark:bg-slate-950 text-white rounded-2xl p-6 shadow-md relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-violet-600/20 rounded-full blur-xl pointer-events-none" />
              <h3 className="text-sm font-bold flex items-center gap-1.5 mb-3 text-violet-300 uppercase tracking-wide">
                <AlertCircle size={15} />
                Budget Planner Tip
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Reduce expenses by sliding your comfort settings below 30. This switches transportation to sleeper rails and housing to locally hosted homestays, cutting baseline trip cost by over 45%.
              </p>
            </div>

          </div>

        </div>
      )}

    </motion.div>
  );
};
