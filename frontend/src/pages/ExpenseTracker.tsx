import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { 
  ArrowLeft, 
  Plus, 
  Trash2, 
  Edit3, 
  Wallet, 
  TrendingDown, 
  TrendingUp, 
  AlertTriangle, 
  Loader, 
  Calendar,
  Save,
  X
} from 'lucide-react';

interface Expense {
  id: number;
  trip_id: number;
  date: string;
  category: string;
  amount: number;
  notes: string;
}

interface CategoryDiff {
  category: string;
  estimated: number;
  actual: number;
  difference: number;
}

interface ExpenseStats {
  total_estimated: number;
  total_actual: number;
  savings: number;
  categories: CategoryDiff[];
}

interface TripDetails {
  id: number;
  destination: {
    name: string;
    state: string;
  };
  budget: number;
  total_estimated_cost: number;
}

export const ExpenseTracker: React.FC = () => {
  const { tripId } = useParams<{ tripId: string }>();
  const { darkMode } = useTheme();
  const [trip, setTrip] = useState<TripDetails | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [stats, setStats] = useState<ExpenseStats | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form states for adding/editing expenses
  const [showForm, setShowForm] = useState(false);
  const [editingExpenseId, setEditingExpenseId] = useState<number | null>(null);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [category, setCategory] = useState('Food');
  const [amount, setAmount] = useState<number>(0);
  const [notes, setNotes] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const categories = ['Transport', 'Hotel', 'Food', 'Activities', 'Shopping', 'Other'];

  const fetchData = async () => {
    try {
      setLoading(true);
      const [tripRes, expenseRes, statsRes] = await Promise.all([
        api.get(`/api/trips/${tripId}`),
        api.get(`/api/expenses/trip/${tripId}`),
        api.get(`/api/expenses/trip/${tripId}/stats`)
      ]);
      setTrip(tripRes.data);
      setExpenses(expenseRes.data);
      setStats(statsRes.data);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch expense details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tripId) {
      fetchData();
    }
  }, [tripId]);

  const handleOpenAdd = () => {
    setEditingExpenseId(null);
    setDate(new Date().toISOString().split('T')[0]);
    setCategory('Food');
    setAmount(0);
    setNotes('');
    setFormError(null);
    setShowForm(true);
  };

  const handleOpenEdit = (exp: Expense) => {
    setEditingExpenseId(exp.id);
    setDate(exp.date);
    setCategory(exp.category);
    setAmount(exp.amount);
    setNotes(exp.notes || '');
    setFormError(null);
    setShowForm(true);
  };

  const handleSaveExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (amount <= 0) {
      setFormError('Amount must be greater than 0.');
      return;
    }

    try {
      const payload = { date, category, amount, notes };
      
      if (editingExpenseId) {
        await api.put(`/api/expenses/${editingExpenseId}`, payload);
      } else {
        await api.post(`/api/expenses/?trip_id=${tripId}`, payload);
      }
      
      setShowForm(false);
      // Reload stats & table
      fetchData();
    } catch (err: any) {
      console.error(err);
      setFormError('Failed to save expense details.');
    }
  };

  const handleDeleteExpense = async (id: number) => {
    if (!window.confirm('Delete this expense entry?')) {
      return;
    }
    try {
      await api.delete(`/api/expenses/${id}`);
      fetchData();
    } catch (err) {
      console.error(err);
      alert('Failed to delete expense entry.');
    }
  };

  if (loading && !trip) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center text-slate-500 dark:text-slate-400 gap-4">
        <Loader className="h-10 w-10 text-violet-500 animate-spin" />
        <span className="text-sm font-semibold">Loading ledger details...</span>
      </div>
    );
  }

  if (error || !trip || !stats) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 rounded-2xl flex items-center gap-3">
        <AlertTriangle size={24} />
        <div>
          <h3 className="font-bold">Error loading expense ledger</h3>
          <p className="text-xs mt-0.5">{error || 'Trip details could not be retrieved.'}</p>
          <Link to="/dashboard" className="text-xs font-semibold underline mt-2 block">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const budgetPct = (stats.total_actual / trip.budget) * 100;
  
  const getHealthColor = (percent: number) => {
    if (percent <= 85) return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
    if (percent <= 100) return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
    return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
  };

  const getHealthBarColor = (percent: number) => {
    if (percent <= 85) return 'bg-emerald-500';
    if (percent <= 100) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="flex flex-col gap-8 relative">
      
      {/* Header Back navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <Link 
            to="/dashboard" 
            className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-violet-600 dark:hover:text-violet-400 uppercase tracking-widest transition-colors mb-2"
          >
            <ArrowLeft size={14} />
            Back to Dashboard
          </Link>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            Expense Tracker: {trip.destination.name}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Log your expenditures and compare actual expenses against the initial budget plan.
          </p>
        </div>
        <button 
          onClick={handleOpenAdd}
          className="inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white font-bold px-5 py-2.5 rounded-xl text-sm transition-all shadow-md shadow-violet-600/15"
        >
          <Plus size={16} />
          Log Expense
        </button>
      </div>

      {/* Stats Summary Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Allocated Budget */}
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-6 rounded-2xl shadow-sm flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-violet-100 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400 flex items-center justify-center shrink-0">
            <Wallet size={22} />
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Allocated Budget</span>
            <span className="text-xl font-extrabold text-slate-800 dark:text-white">₹{trip.budget.toLocaleString()}</span>
          </div>
        </div>

        {/* Spent Actual */}
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-6 rounded-2xl shadow-sm flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-rose-100 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0">
            <TrendingUp size={22} />
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Actual Total Spent</span>
            <span className="text-xl font-extrabold text-slate-800 dark:text-white">₹{stats.total_actual.toLocaleString()}</span>
          </div>
        </div>

        {/* Savings Remaining */}
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-6 rounded-2xl shadow-sm flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-emerald-100 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
            <TrendingDown size={22} />
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Plan Remaining Savings</span>
            <span className={`text-xl font-extrabold block ${stats.savings >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
              ₹{stats.savings.toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Progress Budget Health Bar */}
      <div className={`p-5 rounded-2xl border ${getHealthColor(budgetPct)} flex flex-col gap-2.5 shadow-sm`}>
        <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider">
          <span>Budget Health Indicator</span>
          <span>{budgetPct.toFixed(1)}% Consumed</span>
        </div>
        <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 overflow-hidden">
          <div 
            className={`h-full transition-all duration-300 ${getHealthBarColor(budgetPct)}`}
            style={{ width: `${Math.min(100, budgetPct)}%` }}
          />
        </div>
      </div>

      {/* Main split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Side: Table Ledger */}
        <div className="lg:col-span-7 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
          <h2 className="text-base font-bold text-slate-800 dark:text-white mb-6">Expense Ledger</h2>

          {expenses.length === 0 ? (
            <div className="h-64 border border-dashed border-slate-200 dark:border-slate-700 rounded-2xl flex flex-col items-center justify-center text-center p-6 bg-slate-50/50 dark:bg-slate-900/10">
              <Calendar className="h-12 w-12 text-slate-300 dark:text-slate-600 mb-3 animate-pulse" />
              <h3 className="text-sm font-bold text-slate-600 dark:text-slate-400 mb-1">No Entries Recorded</h3>
              <p className="text-xs text-slate-400 max-w-xs leading-normal">
                You haven't logged any live expenses for this trip. Click the "Log Expense" button to begin tracking.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-700 text-slate-400 font-bold uppercase tracking-wider">
                    <th className="pb-4">Date</th>
                    <th className="pb-4">Category</th>
                    <th className="pb-4">Notes</th>
                    <th className="pb-4">Amount</th>
                    <th className="pb-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60 font-medium">
                  {expenses.map((exp) => (
                    <tr key={exp.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors">
                      <td className="py-4 text-slate-500 dark:text-slate-400">{exp.date}</td>
                      <td className="py-4">
                        <span className="bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-[10px] font-bold px-2 py-0.5 rounded-full">
                          {exp.category}
                        </span>
                      </td>
                      <td className="py-4 text-slate-500 dark:text-slate-400 max-w-[150px] truncate" title={exp.notes}>
                        {exp.notes || '—'}
                      </td>
                      <td className="py-4 text-slate-800 dark:text-white font-bold">₹{exp.amount.toLocaleString()}</td>
                      <td className="py-4 text-right">
                        <div className="flex items-center justify-end gap-2.5">
                          <button 
                            onClick={() => handleOpenEdit(exp)}
                            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 hover:text-slate-700 dark:hover:text-white transition-all"
                            title="Edit"
                          >
                            <Edit3 size={13} />
                          </button>
                          <button 
                            onClick={() => handleDeleteExpense(exp.id)}
                            className="p-1.5 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/20 text-slate-500 hover:text-rose-500 dark:hover:text-rose-400 transition-all"
                            title="Delete"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right Side: Estimated vs Actual chart comparison */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-800 dark:text-white mb-6">Estimate vs Actual</h3>
            
            <div className="h-64 w-full text-xs">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.categories} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:stroke-slate-700" />
                  <XAxis dataKey="category" stroke="#94a3b8" />
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
                  <Bar name="Plan Estimate" dataKey="estimated" fill="#8b5cf6" radius={[3, 3, 0, 0]} />
                  <Bar name="Actual Spent" dataKey="actual" fill="#ef4444" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* List item savings/losses */}
            <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-700 flex flex-col gap-3 text-xs">
              <span className="font-bold text-slate-700 dark:text-slate-300 uppercase block mb-1">Difference Analysis</span>
              
              <div className="flex flex-col gap-2 font-medium">
                {stats.categories.map((cat, idx) => {
                  const isSaved = cat.difference >= 0;
                  if (cat.estimated === 0 && cat.actual === 0) return null;
                  return (
                    <div key={idx} className="flex justify-between items-center text-slate-500 dark:text-slate-400">
                      <span>{cat.category}</span>
                      <span className={isSaved ? 'text-emerald-500 font-bold' : 'text-rose-500 font-bold'}>
                        {isSaved ? `+₹${cat.difference.toLocaleString()}` : `-₹${Math.abs(cat.difference).toLocaleString()}`}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>

        </div>

      </div>

      {/* Floating Add/Edit Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-6 z-50 animate-fade-in">
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
            <button 
              onClick={() => setShowForm(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white"
            >
              <X size={18} />
            </button>

            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6">
              {editingExpenseId ? 'Edit Expense Entry' : 'Log New Expense'}
            </h3>

            {formError && (
              <p className="mb-4 text-rose-500 text-xs font-semibold bg-rose-500/10 border border-rose-500/20 p-3 rounded-lg flex items-center gap-1.5">
                <AlertTriangle size={14} />
                {formError}
              </p>
            )}

            <form onSubmit={handleSaveExpense} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Transaction Date</label>
                <input 
                  type="date"
                  required
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-violet-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Category</label>
                  <select 
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-violet-500 appearance-none"
                  >
                    {categories.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Amount (INR)</label>
                  <input 
                    type="number"
                    required
                    min={1}
                    value={amount}
                    onChange={(e) => setAmount(Number(e.target.value))}
                    placeholder="1500"
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-violet-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Description / Notes</label>
                <input 
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Dinner at beachfront shack"
                  className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-violet-500"
                />
              </div>

              <div className="flex gap-3 justify-end mt-4 border-t border-slate-100 dark:border-slate-700 pt-4">
                <button 
                  type="button" 
                  onClick={() => setShowForm(false)}
                  className="bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 text-slate-700 dark:text-white text-xs font-bold px-4 py-2.5 rounded-lg transition-all"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="bg-violet-600 hover:bg-violet-500 text-white text-xs font-bold px-4 py-2.5 rounded-lg transition-all flex items-center gap-1 shadow-md shadow-violet-500/10"
                >
                  <Save size={14} />
                  Save Entry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
