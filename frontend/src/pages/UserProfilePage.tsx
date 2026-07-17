import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import api from '../services/api';
import { motion } from 'framer-motion';
import { 
  User, 
  Settings, 
  MapPin, 
  Wallet, 
  Sparkles, 
  Sliders, 
  Check, 
  Loader, 
  Calendar, 
  Heart,
  TrendingUp,
  Award
} from 'lucide-react';

interface ProfileStats {
  trips_completed: number;
  total_budget_planned: number;
  total_savings: number;
  favorite_trip_type: string;
}

export const UserProfilePage: React.FC = () => {
  const { user, updateUser } = useAuth();
  const { darkMode, toggleTheme } = useTheme();
  
  const [stats, setStats] = useState<ProfileStats>({
    trips_completed: 0,
    total_budget_planned: 0,
    total_savings: 0,
    favorite_trip_type: '—'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  // Form Fields State
  const [name, setName] = useState('');
  const [photoUrl, setPhotoUrl] = useState('');
  const [defaultBudget, setDefaultBudget] = useState(20000);
  const [preferredTravelStyle, setPreferredTravelStyle] = useState('Nature');
  const [preferredComfortLevel, setPreferredComfortLevel] = useState(50);
  const [defaultStartingCity, setDefaultStartingCity] = useState('Bangalore');
  const [preferredTheme, setPreferredTheme] = useState('light');

  const sampleAvatars = [
    'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&h=150&q=80', // Male Dev
    'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&h=150&q=80', // Female Explorer
    'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?auto=format&fit=crop&w=150&h=150&q=80', // Traveler Guy
    'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=150&h=150&q=80'  // Backpacker Girl
  ];

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/auth/profile');
      const u = response.data.user;
      setStats(response.data.stats);

      // Populate forms
      setName(u.name || '');
      setPhotoUrl(u.photo_url || '');
      setDefaultBudget(u.default_budget || 20000);
      setPreferredTravelStyle(u.preferred_travel_style || 'Nature');
      setPreferredComfortLevel(u.preferred_comfort_level || 50);
      setDefaultStartingCity(u.default_starting_city || 'Bangalore');
      setPreferredTheme(u.preferred_theme || 'light');
    } catch (err) {
      console.error('Failed to load profile details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setSuccess(false);
      
      const response = await api.put('/api/auth/profile', {
        name,
        photo_url: photoUrl,
        default_budget: Number(defaultBudget),
        preferred_travel_style: preferredTravelStyle,
        preferred_comfort_level: preferredComfortLevel,
        default_starting_city: defaultStartingCity,
        preferred_theme: preferredTheme
      });

      // Synchronize with AuthContext
      updateUser(response.data);
      
      // Update local theme state immediately if mismatch
      if (preferredTheme === 'dark' && !darkMode) {
        toggleTheme();
      } else if (preferredTheme === 'light' && darkMode) {
        toggleTheme();
      }

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error(err);
      alert('Failed to update preference settings.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3">
        <Loader className="animate-spin text-violet-500 h-8 w-8" />
        <span className="text-xs font-semibold">Synchronizing profile configurations...</span>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="max-w-4xl mx-auto space-y-8"
    >
      
      {/* Profile Header Title Card */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-6 rounded-2xl shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4.5">
          <div className="shrink-0">
            {photoUrl ? (
              <img 
                src={photoUrl} 
                alt="Profile" 
                className="h-16 w-16 rounded-full object-cover border-2 border-violet-500 shadow-md" 
              />
            ) : (
              <div className="h-16 w-16 rounded-full bg-violet-100 dark:bg-violet-950 flex items-center justify-center text-violet-600 dark:text-violet-400 font-extrabold text-2xl uppercase">
                {user?.name ? user.name[0] : 'T'}
              </div>
            )}
          </div>
          <div>
            <h2 className="text-xl font-extrabold text-slate-850 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <Settings size={20} className="text-violet-500" />
              Settings & Preference Manager
            </h2>
            <span className="text-[10px] text-slate-400 font-bold block uppercase mt-0.5">
              Member Since: {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
            </span>
          </div>
        </div>
      </div>

      {/* Aggregate Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4.5 rounded-2xl shadow-sm text-center space-y-1">
          <Award size={18} className="text-violet-500 mx-auto" />
          <span className="text-[9px] font-bold text-slate-450 uppercase block">Completed Trips</span>
          <span className="font-extrabold text-slate-850 dark:text-white text-base">{stats.trips_completed} Completed</span>
        </div>

        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4.5 rounded-2xl shadow-sm text-center space-y-1">
          <Wallet size={18} className="text-sky-500 mx-auto" />
          <span className="text-[9px] font-bold text-slate-450 uppercase block">Total Planned</span>
          <span className="font-extrabold text-slate-850 dark:text-white text-base">₹{stats.total_budget_planned.toLocaleString()}</span>
        </div>

        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4.5 rounded-2xl shadow-sm text-center space-y-1">
          <TrendingUp size={18} className="text-emerald-500 mx-auto" />
          <span className="text-[9px] font-bold text-slate-450 uppercase block">Total Savings</span>
          <span className="font-extrabold text-emerald-500 text-base">₹{stats.total_savings.toLocaleString()}</span>
        </div>

        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4.5 rounded-2xl shadow-sm text-center space-y-1">
          <Heart size={18} className="text-rose-500 mx-auto" />
          <span className="text-[9px] font-bold text-slate-450 uppercase block">Favorite Style</span>
          <span className="font-extrabold text-slate-850 dark:text-white text-base">{stats.favorite_trip_type}</span>
        </div>

      </div>

      {/* Main Settings Form */}
      <form onSubmit={handleProfileSave} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm space-y-6">
        
        {/* Row 1: Profile basic */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
          <div className="space-y-1.5">
            <label id="display-name-label" className="block text-slate-400 font-bold uppercase tracking-wide text-[10px]">Your Display Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              aria-labelledby="display-name-label"
              className="w-full px-3.5 py-2.5 border border-slate-200 dark:border-slate-700 rounded-xl bg-slate-50 dark:bg-slate-900 focus:outline-none focus:border-violet-500 dark:text-white"
            />
          </div>

          <div className="space-y-1.5">
            <label id="email-label" className="block text-slate-400 font-bold uppercase tracking-wide text-[10px]">Email Address (Read-only)</label>
            <input
              type="email"
              value={user?.email || ''}
              disabled
              aria-labelledby="email-label"
              className="w-full px-3.5 py-2.5 border border-slate-150 dark:border-slate-800/80 rounded-xl bg-slate-100/50 dark:bg-slate-950/40 text-slate-400 select-none cursor-not-allowed"
            />
          </div>
        </div>

        {/* Row 2: Avatar select */}
        <div className="space-y-2">
          <label id="avatar-label" className="block text-slate-400 font-bold uppercase tracking-wide text-[10px]">Choose Profile Avatar</label>
          <div className="flex flex-wrap gap-4 items-center">
            {sampleAvatars.map((url, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setPhotoUrl(url)}
                aria-label={`Select Avatar Option ${idx + 1}`}
                className={`h-14 w-14 rounded-full overflow-hidden border-2 transition-all shrink-0 ${photoUrl === url ? 'border-violet-600 scale-105 shadow-md shadow-violet-500/10' : 'border-transparent opacity-80 hover:opacity-100'}`}
              >
                <img src={url} alt={`Option ${idx + 1}`} className="h-full w-full object-cover" />
              </button>
            ))}
            <input
              type="text"
              placeholder="Or enter custom avatar photo URL..."
              value={photoUrl}
              onChange={(e) => setPhotoUrl(e.target.value)}
              aria-labelledby="avatar-label"
              className="flex-1 min-w-[200px] px-3.5 py-2.5 border border-slate-200 dark:border-slate-700 rounded-xl text-xs bg-slate-50 dark:bg-slate-900 focus:outline-none focus:border-violet-500 dark:text-white"
            />
          </div>
        </div>

        {/* Row 3: Defaults preferences */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs">
          
          <div className="space-y-1.5">
            <label id="starting-city-label" className="block text-slate-400 font-bold uppercase tracking-wide text-[10px]">Default starting City</label>
            <div className="relative">
              <MapPin size={14} className="absolute left-3.5 top-3.5 text-slate-400" />
              <input
                type="text"
                value={defaultStartingCity}
                onChange={(e) => setDefaultStartingCity(e.target.value)}
                required
                aria-labelledby="starting-city-label"
                className="w-full pl-9 pr-3.5 py-2.5 border border-slate-200 dark:border-slate-700 rounded-xl bg-slate-50 dark:bg-slate-900 focus:outline-none focus:border-violet-500 dark:text-white"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label id="default-budget-label" className="block text-slate-400 font-bold uppercase tracking-wide text-[10px]">Default Target Budget (INR)</label>
            <div className="relative">
              <Wallet size={14} className="absolute left-3.5 top-3.5 text-slate-400" />
              <input
                type="number"
                value={defaultBudget}
                onChange={(e) => setDefaultBudget(Number(e.target.value))}
                required
                min={1000}
                step={1000}
                aria-labelledby="default-budget-label"
                className="w-full pl-9 pr-3.5 py-2.5 border border-slate-200 dark:border-slate-700 rounded-xl bg-slate-50 dark:bg-slate-900 focus:outline-none focus:border-violet-500 dark:text-white"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label id="preferred-style-label" className="block text-slate-400 font-bold uppercase tracking-wide text-[10px]">Preferred Style</label>
            <div className="relative">
              <Sparkles size={14} className="absolute left-3.5 top-3.5 text-slate-400" />
              <select
                value={preferredTravelStyle}
                onChange={(e) => setPreferredTravelStyle(e.target.value)}
                aria-labelledby="preferred-style-label"
                className="w-full pl-9 pr-3.5 py-2.5 border border-slate-200 dark:border-slate-700 rounded-xl bg-slate-50 dark:bg-slate-900 focus:outline-none focus:border-violet-500 dark:text-white"
              >
                {['Nature', 'Adventure', 'Family', 'Religious', 'Beach', 'City Exploration', 'Romantic', 'Solo'].map((style) => (
                  <option key={style} value={style}>{style}</option>
                ))}
              </select>
            </div>
          </div>

        </div>

        {/* Row 4: Theme and Comfort preference */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
          
          <div className="space-y-1.5">
            <label id="comfort-label" className="block text-slate-400 font-bold uppercase tracking-wide text-[10px]">Comfort level Preference ({preferredComfortLevel} / 100)</label>
            <div className="flex gap-4 items-center pt-2">
              <Sliders size={16} className="text-violet-500 shrink-0" />
              <input
                type="range"
                min={0}
                max={100}
                value={preferredComfortLevel}
                onChange={(e) => setPreferredComfortLevel(Number(e.target.value))}
                aria-labelledby="comfort-label"
                className="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-violet-600"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label id="preferred-theme-label" className="block text-slate-400 font-bold uppercase tracking-wide text-[10px]">Preferred System Theme</label>
            <select
              value={preferredTheme}
              onChange={(e) => setPreferredTheme(e.target.value)}
              aria-labelledby="preferred-theme-label"
              className="w-full px-3.5 py-2.5 border border-slate-200 dark:border-slate-700 rounded-xl bg-slate-50 dark:bg-slate-900 focus:outline-none focus:border-violet-500 dark:text-white font-bold"
            >
              <option value="light">Light Theme Mode</option>
              <option value="dark">Dark Theme Mode</option>
            </select>
          </div>

        </div>

        {/* Action button */}
        <div className="flex justify-end pt-3 border-t border-slate-100 dark:border-slate-700">
          <button
            type="submit"
            disabled={saving}
            className="bg-violet-600 hover:bg-violet-500 text-white font-extrabold text-[11px] px-6 py-3 rounded-xl uppercase transition-all shadow-md flex items-center gap-1.5"
          >
            {saving ? <Loader size={13} className="animate-spin" /> : (success ? <Check size={13} className="text-emerald-350" /> : null)}
            {saving ? 'Saving preferences...' : (success ? 'Saved successfully!' : 'Save Preferences')}
          </button>
        </div>

      </form>

    </motion.div>
  );
};
