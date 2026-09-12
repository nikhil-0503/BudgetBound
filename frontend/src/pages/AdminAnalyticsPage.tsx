import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area
} from 'recharts';
import { 
  ShieldAlert, 
  Users, 
  Map, 
  TrendingUp, 
  Wallet, 
  Download, 
  Loader, 
  ChevronRight,
  TrendingDown,
  Activity,
  Heart
} from 'lucide-react';

interface SummaryData {
  total_users: number;
  total_trips: number;
  completed_trips: number;
  avg_budget: number;
  avg_savings: number;
  popular_destination: string;
  popular_category: string;
  avg_comfort: number;
  top_destinations: { name: string; count: number }[];
  monthly_creation: { month: string; count: number }[];
  monthly_expenses: { month: string; amount: number }[];
}

export const AdminAnalyticsPage: React.FC = () => {
  const { user } = useAuth();

  // All hooks MUST be declared before any conditional return (React Rules of Hooks)
  const [filter, setFilter] = useState<string>('all');
  const [data, setData] = useState<SummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/admin/analytics?time_filter=${filter}`);
      setData(response.data);
    } catch (err) {
      console.error('Failed to load admin analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch if the user is authenticated and is an admin
    if (user && user.is_admin) {
      fetchAnalytics();
    }
  }, [filter, user]);

  // Guard clause for admin authentication "” placed AFTER all hook declarations
  if (!user || !user.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleCsvExport = async () => {
    try {
      setExporting(true);
      
      const downloadUrl = `${api.defaults.baseURL || ''}/api/admin/analytics/export-csv`;
      const token = localStorage.getItem('token');
      
      // Trigger browser download by opening the window
      if (token) {
        window.open(`${downloadUrl}?token=${token}`, '_blank');
      } else {
        window.open(downloadUrl, '_blank');
      }
    } catch (err) {
      console.error(err);
      alert('Failed to generate CSV export.');
    } finally {
      setExporting(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-paper-400 gap-3">
        <Loader className="animate-spin text-marigold-500 h-8 w-8" />
        <span className="text-xs font-semibold">Compiling global travel reports...</span>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="space-y-8 max-w-6xl mx-auto pb-10"
    >
      
      {/* Header controls card */}
      <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-6 rounded-2xl shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-paper-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
            <ShieldAlert size={20} className="text-marigold-500" />
            Admin Analytics Control Dashboard
          </h2>
          <p className="text-[11px] text-paper-400 mt-0.5">
            Evaluate global creation metrics, destinations popularity, and aggregate user savings
          </p>
        </div>

        {/* Date Filter & CSV download row */}
        <div className="flex items-center gap-3">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            aria-label="Filter timeline results"
            className="px-3.5 py-2 border border-paper-200 dark:border-paper-700 rounded-xl bg-paper-50 dark:bg-paper-900 text-xs font-bold focus:outline-none dark:text-white"
          >
            <option value="all">All Time</option>
            <option value="6months">Last 6 Months</option>
            <option value="30days">Last 30 Days</option>
          </select>

          <button
            onClick={handleCsvExport}
            disabled={exporting}
            aria-label="Export reports as CSV spreadsheet"
            className="inline-flex items-center gap-1.5 bg-marigold-600 hover:bg-marigold-500 text-white font-extrabold text-[10px] px-4.5 py-2.5 rounded-xl uppercase transition-all shadow-md shrink-0"
          >
            {exporting ? <Loader size={12} className="animate-spin" /> : <Download size={12} />}
            Export CSV
          </button>
        </div>
      </div>

      {/* Aggregate Stats Cards */}
      {data && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-semibold">
          
          <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-5 rounded-2xl shadow-sm space-y-1">
            <Users size={18} className="text-marigold-500" />
            <span className="text-[9px] text-paper-400 dark:text-paper-400 uppercase font-bold block">Total Accounts</span>
            <span className="text-2xl font-extrabold text-paper-800 dark:text-white block">{data.total_users} Users</span>
          </div>

          <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-5 rounded-2xl shadow-sm space-y-1">
            <Map size={18} className="text-sky-500" />
            <span className="text-[9px] text-paper-400 dark:text-paper-400 uppercase font-bold block">Total Trips Saved</span>
            <span className="text-2xl font-extrabold text-paper-800 dark:text-white block">
              {data.total_trips} Trips <span className="text-[10px] text-emerald-500 font-bold">({data.completed_trips} Done)</span>
            </span>
          </div>

          <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-5 rounded-2xl shadow-sm space-y-1">
            <Wallet size={18} className="text-emerald-500" />
            <span className="text-[9px] text-paper-400 dark:text-paper-400 uppercase font-bold block">Average Segment Budget</span>
            <span className="text-2xl font-extrabold text-paper-800 dark:text-white block">₹{data.avg_budget.toLocaleString()}</span>
          </div>

          <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-5 rounded-2xl shadow-sm space-y-1">
            <TrendingUp size={18} className="text-rose-500" />
            <span className="text-[9px] text-paper-400 dark:text-paper-400 uppercase font-bold block">Average Savings</span>
            <span className="text-2xl font-extrabold text-emerald-500 block">₹{data.avg_savings.toLocaleString()}</span>
          </div>

        </div>
      )}

      {/* Visualizations Grid */}
      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Monthly creations area chart */}
          <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-5 rounded-2xl shadow-sm space-y-4">
            <div>
              <h3 className="text-xs font-extrabold uppercase tracking-wider text-paper-800 dark:text-white">Trip Creation Velocity</h3>
              <p className="text-[10px] text-paper-400 mt-0.5">Global itinerary generation rates grouped by month</p>
            </div>
            <div className="h-64">
              {data.monthly_creation.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-paper-400 italic">No trip history yet.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.monthly_creation}>
                    <defs>
                      <linearGradient id="colorCreation" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="#7c3aed" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="month" stroke="#94a3b8" fontSize={10} tickLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                    <Area type="monotone" dataKey="count" stroke="#7c3aed" fillOpacity={1} fill="url(#colorCreation)" strokeWidth={2} name="Trips Created" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Monthly expenditures bar chart */}
          <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-5 rounded-2xl shadow-sm space-y-4">
            <div>
              <h3 className="text-xs font-extrabold uppercase tracking-wider text-paper-800 dark:text-white">Monthly Expenditure Trajectory</h3>
              <p className="text-[10px] text-paper-400 mt-0.5">Sum of aggregate actual logged expense costs by month</p>
            </div>
            <div className="h-64">
              {data.monthly_expenses.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-paper-400 italic">No expenditures logged.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.monthly_expenses}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="month" stroke="#94a3b8" fontSize={10} tickLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} formatter={(v) => `₹${Number(v).toLocaleString()}`} />
                    <Bar dataKey="amount" fill="#0ea5e9" radius={[4, 4, 0, 0]} name="Expense Spent" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Popular destinations list bar chart */}
          <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-5 rounded-2xl shadow-sm space-y-4 lg:col-span-2">
            <div>
              <h3 className="text-xs font-extrabold uppercase tracking-wider text-paper-800 dark:text-white">Popularity Matrix (Top 10 Locations)</h3>
              <p className="text-[10px] text-paper-400 mt-0.5">Distribution count of total travel plans generated by destination</p>
            </div>
            <div className="h-72">
              {data.top_destinations.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-paper-400 italic">No plans generated.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.top_destinations} layout="vertical" margin={{ left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                    <XAxis type="number" stroke="#94a3b8" fontSize={10} tickLine={false} />
                    <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} width={80} />
                    <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                    <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} name="Planned Count" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

        </div>
      )}

      {/* Overview stats table */}
      {data && (
        <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-5 rounded-2xl shadow-sm space-y-4">
          <h3 className="text-xs font-extrabold uppercase tracking-wider text-paper-800 dark:text-white">Overview Distributions</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-xs bg-paper-50 dark:bg-paper-900/40 p-4 rounded-xl border border-paper-100 dark:border-paper-800 font-bold">
            <div className="space-y-0.5">
              <span className="text-[10px] text-paper-400 block uppercase">Most Popular Target</span>
              <span className="text-paper-800 dark:text-white">{data.popular_destination}</span>
            </div>
            <div className="space-y-0.5">
              <span className="text-[10px] text-paper-400 block uppercase">Most Popular Category</span>
              <span className="text-paper-800 dark:text-white">{data.popular_category}</span>
            </div>
            <div className="space-y-0.5">
              <span className="text-[10px] text-paper-400 block uppercase">Average Comfort standard</span>
              <span className="text-paper-800 dark:text-white">{data.avg_comfort}% Preference</span>
            </div>
            <div className="space-y-0.5">
              <span className="text-[10px] text-paper-400 block uppercase">Total Trips Logged</span>
              <span className="text-paper-800 dark:text-white">{data.total_trips} Plans</span>
            </div>
          </div>
        </div>
      )}

    </motion.div>
  );
};



