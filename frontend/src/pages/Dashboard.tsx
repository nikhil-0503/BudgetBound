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
  Loader,
  Download
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

  const [downloadingTripId, setDownloadingTripId] = useState<number | null>(null);

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

  const handleDownloadPDF = async (tripId: number, destName: string) => {
    setDownloadingTripId(tripId);
    try {
      const response = await api.get(`/api/trips/${tripId}/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `budgetbound_${destName.replace(/\s+/g, '_').toLowerCase()}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download PDF:', err);
    } finally {
      setDownloadingTripId(null);
    }
  };

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
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-paper-500 dark:text-paper-400 gap-4">
        <Loader className="h-10 w-10 text-marigold-500 animate-spin" />
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
  const COLORS = ['#E8A33D', '#1F6F63', '#9B3A5B', '#10b981', '#f59e0b', '#B04066'];

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
          <p className="eyebrow-rule text-marigold-700 dark:text-marigold-400 text-xs font-semibold">Travel hub</p>
          <h1 className="font-display text-3xl font-semibold text-ink-900 dark:text-paper-50 mt-1">
            Welcome back, {user?.name || 'Explorer'}
          </h1>
        </div>
        <Link
          to="/planner"
          className="inline-flex items-center gap-2 bg-marigold-500 hover:bg-marigold-400 text-ink-950 font-semibold px-5 py-2.5 rounded-xl text-sm transition-all"
        >
          <PlusCircle size={16} />
          Plan new trip
        </Link>
      </div>

      {/* Core Stats Cards — ticket stubs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">

        {/* Total Trips */}
        <div className="ticket p-5 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-paper-500 dark:text-paper-400 font-medium">Total trips</span>
            <h3 className="font-num text-3xl font-semibold text-ink-900 dark:text-paper-50">{stats.total_trips}</h3>
          </div>
          <div className="h-11 w-11 rounded-full bg-marigold-100 dark:bg-marigold-950/40 text-marigold-600 dark:text-marigold-400 flex items-center justify-center">
            <Compass size={22} />
          </div>
        </div>

        {/* Planned Budget */}
        <div className="ticket p-5 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-paper-500 dark:text-paper-400 font-medium">Allocated budget</span>
            <h3 className="font-num text-2xl font-semibold text-ink-900 dark:text-paper-50">₹{stats.planned_budget.toLocaleString('en-IN')}</h3>
          </div>
          <div className="h-11 w-11 rounded-full bg-petrol-100 dark:bg-petrol-950/40 text-petrol-600 dark:text-petrol-400 flex items-center justify-center">
            <Wallet size={22} />
          </div>
        </div>

        {/* Actual Expenses */}
        <div className="ticket p-5 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-paper-500 dark:text-paper-400 font-medium">Spent so far</span>
            <h3 className="font-num text-2xl font-semibold text-ink-900 dark:text-paper-50">₹{stats.actual_expenses.toLocaleString('en-IN')}</h3>
          </div>
          <div className="h-11 w-11 rounded-full bg-berry-100 dark:bg-berry-950/40 text-berry-600 dark:text-berry-400 flex items-center justify-center">
            <TrendingUp size={22} />
          </div>
        </div>

        {/* Savings */}
        <div className="ticket p-5 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-paper-500 dark:text-paper-400 font-medium">Calculated savings</span>
            <h3 className="font-num text-2xl font-semibold text-ink-900 dark:text-paper-50">₹{stats.savings.toLocaleString('en-IN')}</h3>
          </div>
          <div className="h-11 w-11 rounded-full bg-emerald-100 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
            <Percent size={22} />
          </div>
        </div>
      </div>

      {/* Status Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-6">
        {/* Planned */}
        <div className="ticket p-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] text-paper-500 dark:text-paper-400 font-medium block">Planned</span>
            <h4 className="font-num text-xl font-semibold text-ink-900 dark:text-paper-50 mt-0.5">{stats.trips_planned || 0}</h4>
          </div>
          <div className="h-8 w-8 rounded-full bg-petrol-100 dark:bg-petrol-950/40 text-petrol-700 dark:text-petrol-400 flex items-center justify-center font-num text-[10px] font-semibold">
            PL
          </div>
        </div>
        {/* In Progress */}
        <div className="ticket p-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] text-paper-500 dark:text-paper-400 font-medium block">In progress</span>
            <h4 className="font-num text-xl font-semibold text-ink-900 dark:text-paper-50 mt-0.5">{stats.trips_in_progress || 0}</h4>
          </div>
          <div className="h-8 w-8 rounded-full bg-marigold-100 dark:bg-marigold-950/40 text-marigold-700 dark:text-marigold-400 flex items-center justify-center font-num text-[10px] font-semibold">
            IP
          </div>
        </div>
        {/* Completed */}
        <div className="ticket p-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] text-paper-500 dark:text-paper-400 font-medium block">Completed</span>
            <h4 className="font-num text-xl font-semibold text-ink-900 dark:text-paper-50 mt-0.5">{stats.trips_completed || 0}</h4>
          </div>
          <div className="h-8 w-8 rounded-full bg-emerald-100 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 flex items-center justify-center font-num text-[10px] font-semibold">
            CO
          </div>
        </div>
        {/* Cancelled */}
        <div className="ticket p-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] text-paper-500 dark:text-paper-400 font-medium block">Cancelled</span>
            <h4 className="font-num text-xl font-semibold text-ink-900 dark:text-paper-50 mt-0.5">{stats.trips_cancelled || 0}</h4>
          </div>
          <div className="h-8 w-8 rounded-full bg-berry-100 dark:bg-berry-950/40 text-berry-700 dark:text-berry-400 flex items-center justify-center font-num text-[10px] font-semibold">
            CA
          </div>
        </div>
        {/* Draft */}
        <div className="ticket p-4 flex items-center justify-between col-span-2 lg:col-span-1">
          <div>
            <span className="text-[11px] text-paper-500 dark:text-paper-400 font-medium block">Drafts</span>
            <h4 className="font-num text-xl font-semibold text-ink-900 dark:text-paper-50 mt-0.5">{stats.trips_draft || 0}</h4>
          </div>
          <div className="h-8 w-8 rounded-full bg-paper-200 dark:bg-paper-900 text-paper-600 dark:text-paper-400 flex items-center justify-center font-num text-[10px] font-semibold">
            DR
          </div>
        </div>
      </div>

      {/* Latest Trip Budget Health & Predictions Forecast */}
      {stats.total_trips > 0 && latestTripDetails && latestTripStats && (
        <div className="ticket p-6 flex flex-col gap-6">
          <div className="pb-3">
            <h2 className="font-display text-lg font-semibold text-ink-900 dark:text-paper-50">
              Latest forecast: {latestTripDetails.destination.name}
            </h2>
            <p className="text-xs text-paper-500 dark:text-paper-400 mt-0.5">Budget health and predictions for your upcoming trip</p>
          </div>
          <div className="ticket-perforation !mx-0" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <BudgetHealthMeter
              budget={latestTripDetails.budget}
              estimatedCost={latestTripDetails.total_estimated_cost}
              actualExpenses={latestTripStats.total_actual}
              className="w-full bg-paper-50 dark:bg-ink-800 border border-paper-300 dark:border-ink-600"
            />

            {/* Predictions widget */}
            <div className="bg-paper-50 dark:bg-ink-800 border border-paper-300 dark:border-ink-600 rounded-2xl p-6 flex flex-col justify-between gap-4">
              <div>
                <h3 className="font-semibold text-sm text-ink-900 dark:text-paper-50">
                  Live financial forecast
                </h3>
                <p className="text-[11px] text-paper-500 dark:text-paper-400 mt-0.5">Real-time spend pacing and projections</p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="space-y-0.5">
                  <span className="text-paper-500 dark:text-paper-400 font-medium block">Remaining budget</span>
                  <span className={`font-num font-semibold ${latestTripStats.remaining_budget >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
                    ₹{latestTripStats.remaining_budget ? latestTripStats.remaining_budget.toLocaleString('en-IN') : '0'}
                  </span>
                </div>

                <div className="space-y-0.5">
                  <span className="text-paper-500 dark:text-paper-400 font-medium block">Current burn rate</span>
                  <span className="font-num font-semibold text-ink-800 dark:text-paper-200">
                    ₹{latestTripStats.daily_burn_rate ? latestTripStats.daily_burn_rate.toLocaleString(undefined, { maximumFractionDigits: 1 }) : '0'}/day
                  </span>
                </div>

                <div className="space-y-0.5">
                  <span className="text-paper-500 dark:text-paper-400 font-medium block">Projected spend</span>
                  <span className="font-num font-semibold text-ink-800 dark:text-paper-200">
                    ₹{latestTripStats.projected_final_spend ? latestTripStats.projected_final_spend.toLocaleString('en-IN') : '0'}
                  </span>
                </div>

                <div className="space-y-0.5">
                  <span className="text-paper-500 dark:text-paper-400 font-medium block">Forecast status</span>
                  <span className={`inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-full mt-1 ${
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
        <div className="ticket border-dashed p-12 text-center flex flex-col items-center justify-center">
          <Compass className="h-16 w-16 text-paper-400 dark:text-paper-600 mb-6" />
          <h3 className="font-display text-xl font-semibold text-ink-900 dark:text-paper-50 mb-2">Your travel log is empty</h3>
          <p className="text-sm text-paper-600 dark:text-paper-400 max-w-md mb-8 leading-relaxed">
            Create your first itinerary with the budget allocator to map out transport, stays, and local sights.
          </p>
          <Link
            to="/planner"
            className="inline-flex items-center gap-2 bg-marigold-500 hover:bg-marigold-400 text-ink-950 font-semibold px-8 py-3.5 rounded-xl transition-all"
          >
            Create your first plan
            <ArrowRight size={18} />
          </Link>
        </div>
      ) : (
        /* Charts & Table Columns */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

          {/* Left Panel: Budget Chart & Trips list */}
          <div className="lg:col-span-8 flex flex-col gap-8">

            {/* Chart 1: Budget Usage */}
            <div className="ticket p-6">
              <h3 className="font-display text-base font-semibold text-ink-900 dark:text-paper-50 mb-6">Budget vs. cost comparison</h3>
              <div className="h-72 w-full text-xs">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.budget_usage_chart} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:stroke-paper-700" />
                    <XAxis dataKey="name" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip
                      contentStyle={{
                        background: darkMode ? '#14231f' : 'rgba(251,250,245,0.95)',
                        border: darkMode ? '1px solid #1a3733' : '1px solid #d9d5bc',
                        color: darkMode ? '#f3f1e4' : '#10120f',
                        borderRadius: '12px'
                      }}
                      itemStyle={{
                        color: darkMode ? '#f3f1e4' : '#10120f'
                      }}
                    />
                    <Legend wrapperStyle={{ paddingTop: '10px' }} />
                    <Bar name="Target Budget" dataKey="budget" fill="#1F6F63" radius={[4, 4, 0, 0]} />
                    <Bar name="Estimated Cost" dataKey="estimated" fill="#E8A33D" radius={[4, 4, 0, 0]} />
                    <Bar name="Actual Expenses" dataKey="actual" fill="#9B3A5B" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Recent Trips Table */}
            <div className="ticket p-6">
              <h3 className="font-display text-base font-semibold text-ink-900 dark:text-paper-50 mb-6">Recent travel plans</h3>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-paper-200 dark:border-paper-700 text-paper-500 dark:text-paper-400 font-medium">
                      <th className="pb-4">Destination</th>
                      <th className="pb-4">Budget</th>
                      <th className="pb-4">Est. cost</th>
                      <th className="pb-4">Duration</th>
                      <th className="pb-4">Category</th>
                      <th className="pb-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-paper-200 dark:divide-paper-700/60 font-medium">
                    {stats.recent_trips.map((trip) => (
                      <tr key={trip.id} className="hover:bg-paper-100/60 dark:hover:bg-ink-800/40 transition-colors">
                        <td className="py-4">
                          <div className="flex flex-col">
                            <span className="font-semibold text-ink-900 dark:text-paper-50">{trip.destination}</span>
                            <span className="text-[10px] text-paper-500 dark:text-paper-400">{trip.state}</span>
                          </div>
                        </td>
                        <td className="py-4 font-num text-paper-700 dark:text-paper-300">₹{trip.budget.toLocaleString('en-IN')}</td>
                        <td className="py-4 font-num text-ink-900 dark:text-paper-50 font-semibold">₹{trip.estimated_cost.toLocaleString('en-IN')}</td>
                        <td className="py-4 text-paper-600 dark:text-paper-400">{trip.days} days</td>
                        <td className="py-4">
                          <span className="bg-marigold-100 dark:bg-marigold-950/40 text-marigold-700 dark:text-marigold-400 text-[10px] font-semibold px-2 py-0.5 rounded-full">
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
                              className="p-2 rounded-lg bg-paper-50 hover:bg-paper-100 dark:bg-paper-700/40 dark:hover:bg-paper-700 text-paper-600 dark:text-paper-300 transition-all"
                              title="View Details / Re-simulate"
                            >
                              <Eye size={14} />
                            </button>

                            <button
                              onClick={() => handleDownloadPDF(trip.id, trip.destination)}
                              disabled={downloadingTripId === trip.id}
                              className="p-2 rounded-lg bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/20 dark:hover:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 transition-all disabled:opacity-50"
                              title="Download Itinerary PDF"
                            >
                              {downloadingTripId === trip.id ? (
                                <Loader size={14} className="animate-spin" />
                              ) : (
                                <Download size={14} />
                              )}
                            </button>

                            <button
                              onClick={() => navigate(`/expenses/${trip.id}`)}
                              className="p-2 rounded-lg bg-marigold-50 hover:bg-marigold-100 dark:bg-marigold-950/20 dark:hover:bg-marigold-900/30 text-marigold-600 dark:text-marigold-400 transition-all font-bold"
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
            <div className="ticket p-6">
              <h3 className="font-display text-base font-semibold text-ink-900 dark:text-paper-50 mb-6">Expense distribution</h3>

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
                        background: darkMode ? '#14231f' : 'rgba(251,250,245,0.95)',
                        border: darkMode ? '1px solid #1a3733' : '1px solid #d9d5bc',
                        color: darkMode ? '#f3f1e4' : '#10120f',
                        borderRadius: '12px'
                      }}
                      itemStyle={{
                        color: darkMode ? '#f3f1e4' : '#10120f'
                      }}
                      formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Spent']}
                    />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Legend Summary */}
              {stats.actual_expenses > 0 && (
                <div className="mt-4 pt-4 ticket-perforation !mx-0 pt-6 flex flex-col gap-2.5 text-[11px] text-paper-500 dark:text-paper-400">
                  <span className="font-semibold text-paper-700 dark:text-paper-300">Expense summary</span>
                  <div className="flex justify-between items-center">
                    <span>Average trip spent</span>
                    <span className="font-num font-semibold text-ink-900 dark:text-paper-50">₹{(stats.actual_expenses / stats.total_trips).toFixed(0)}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Upcoming Trips List */}
            <div className="ticket p-6">
              <h3 className="font-display text-base font-semibold text-ink-900 dark:text-paper-50 mb-4">Upcoming trips</h3>

              {(!stats.upcoming_trips || stats.upcoming_trips.length === 0) ? (
                <p className="text-xs text-paper-500 dark:text-paper-400 italic">No upcoming planned trips found.</p>
              ) : (
                <div className="flex flex-col gap-3">
                  {stats.upcoming_trips.map((trip) => (
                    <div
                      key={trip.id}
                      onClick={() => navigate(`/planner?tripId=${trip.id}`)}
                      className="p-3 bg-paper-100/60 dark:bg-ink-800/50 hover:bg-paper-200/60 dark:hover:bg-ink-800 border border-paper-200 dark:border-ink-600 rounded-xl flex justify-between items-center cursor-pointer transition-all hover:translate-x-1"
                    >
                      <div className="flex flex-col gap-0.5">
                        <span className="font-semibold text-xs text-ink-900 dark:text-paper-50">{trip.destination}</span>
                        <span className="text-[10px] text-paper-500 dark:text-paper-400">
                          {trip.start_date ? `Starts ${trip.start_date}` : `${trip.days} days / ${trip.category}`}
                        </span>
                      </div>
                      <div className="text-right flex flex-col items-end gap-1">
                        <span className="text-[10px] font-num font-semibold text-ink-900 dark:text-paper-50">₹{trip.budget.toLocaleString('en-IN')}</span>
                        <span className="text-[9px] font-semibold px-1.5 py-0.5 bg-petrol-100 dark:bg-petrol-950/30 text-petrol-700 dark:text-petrol-400 rounded">
                          {trip.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Tips Box */}
            <div className="bg-ink-900 dark:bg-ink-950 text-paper-50 rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-marigold-500/15 rounded-full blur-xl pointer-events-none" />
              <h3 className="text-sm font-semibold flex items-center gap-1.5 mb-3 text-marigold-400">
                <AlertCircle size={15} />
                Budget planner tip
              </h3>
              <p className="text-xs text-paper-300 leading-relaxed">
                Move your comfort slider below 30 to cut costs: it switches transport to sleeper trains and stays to local homestays, dropping the baseline trip cost by more than 45%.
              </p>
            </div>

          </div>

        </div>
      )}

    </motion.div>
  );
};



