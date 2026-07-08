import React from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { 
  Compass, 
  MapPin, 
  Sparkles, 
  TrendingUp, 
  Wallet, 
  ShieldCheck, 
  ArrowRight,
  Star,
  Sun,
  Moon
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const { darkMode, toggleTheme } = useTheme();

  const samplePlans = [
    {
      name: 'Munnar Tea Estates',
      category: 'Nature',
      state: 'Kerala',
      days: 4,
      cost: '₹14,500',
      rating: 4.7,
      img: 'https://images.unsplash.com/photo-1593693397690-362cb9666fc2?auto=format&fit=crop&q=80&w=600',
      tag: 'Best Value'
    },
    {
      name: 'Rishikesh Adventure',
      category: 'Adventure',
      state: 'Uttarakhand',
      days: 3,
      cost: '₹9,800',
      rating: 4.6,
      img: 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?auto=format&fit=crop&q=80&w=600',
      tag: 'Popular'
    },
    {
      name: 'Varanasi Spiritual',
      category: 'Religious',
      state: 'Uttar Pradesh',
      days: 4,
      cost: '₹8,200',
      rating: 4.7,
      img: 'https://images.unsplash.com/photo-1561361513-2d000a50f0db?auto=format&fit=crop&q=80&w=600',
      tag: 'Budget Pick'
    }
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 overflow-x-hidden selection:bg-violet-500 selection:text-white transition-colors duration-200">
      
      {/* Navigation */}
      <nav className="w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between z-10 relative">
        <div className="flex items-center gap-2">
          <Wallet className="h-8 w-8 text-violet-600" />
          <span className="font-bold text-2xl tracking-tight bg-gradient-to-r from-violet-600 to-indigo-600 bg-clip-text text-transparent">
            BudgetBound
          </span>
        </div>
        <div className="flex items-center gap-4 md:gap-6">
          <button 
            onClick={toggleTheme}
            className="p-2.5 rounded-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <Link to="/login" className="text-sm font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-950 dark:hover:text-white transition-colors">
            Login
          </Link>
          <Link 
            to="/register" 
            className="text-sm font-semibold bg-violet-600 hover:bg-violet-500 text-white px-5 py-2.5 rounded-full transition-all duration-200 shadow-lg shadow-violet-600/20 hover:scale-105"
          >
            Start Planning
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 pt-16 pb-24 text-center relative">
        {/* Background Gradients */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-violet-600/5 rounded-full blur-[100px] pointer-events-none -z-10" />
        <div className="absolute top-20 left-1/3 w-[300px] h-[300px] bg-cyan-500/5 rounded-full blur-[80px] pointer-events-none -z-10" />

        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 text-xs font-semibold tracking-wide mb-8 hover:bg-slate-200 dark:hover:bg-slate-800 transition-all cursor-pointer">
          <Sparkles className="h-4 w-4 text-violet-500" />
          Budget-First Travel Planner
        </div>

        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-tight max-w-4xl mx-auto mb-6">
          Stop asking <span className="bg-gradient-to-r from-violet-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">where</span>.<br />
          Start asking <span className="bg-gradient-to-r from-cyan-600 via-purple-600 to-violet-600 bg-clip-text text-transparent">how much</span>.
        </h1>

        <p className="text-lg md:text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Input your budget, starting location, and days. BudgetBound automatically calculates lodging, transport, activities, and generates the ultimate itinerary.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link 
            to="/register" 
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-semibold px-8 py-4 rounded-full transition-all shadow-xl shadow-violet-600/35 hover:scale-105"
          >
            Create Your Plan
            <ArrowRight size={18} />
          </Link>
          <a 
            href="#how-it-works"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 font-semibold px-8 py-4 rounded-full transition-all shadow-sm"
          >
            How it works
          </a>
        </div>

        {/* Demo Preview Mockup */}
        <div className="mt-16 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 rounded-2xl p-4 shadow-2xl relative max-w-5xl mx-auto overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-t from-slate-50 dark:from-slate-900 via-transparent to-transparent z-10 pointer-events-none" />
          <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3 mb-4">
            <div className="w-3 h-3 rounded-full bg-rose-500" />
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <div className="w-3 h-3 rounded-full bg-emerald-500" />
            <div className="h-6 w-60 rounded-md bg-slate-100 dark:bg-slate-800 mx-auto text-[10px] text-slate-500 flex items-center justify-center">
              https://budgetbound.com/planner
            </div>
          </div>
          <div className="h-64 sm:h-96 w-full bg-slate-50/40 dark:bg-slate-950/40 rounded-lg flex flex-col items-center justify-center relative">
            <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#6366f1_1px,transparent_1px)] [background-size:16px_16px]" />
            <div className="relative z-10 text-center px-6">
              <Compass className="h-16 w-16 text-violet-600 mx-auto animate-bounce mb-4" />
              <h3 className="text-xl font-bold text-slate-850 dark:text-white mb-2">Deterministic Travel Engine</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md">
                Analyzing 50+ locations, calculating seasonal accommodations, rail / flight pricing, and daily dining to maximize your travel savings.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="bg-slate-100/50 dark:bg-slate-950/60 py-24 border-t border-b border-slate-200 dark:border-slate-800 transition-colors">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">How BudgetBound Works</h2>
            <p className="text-slate-600 dark:text-slate-400">Three easy steps to discover trips that match your wallet, not just your bucket list.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 rounded-2xl hover:border-violet-500/50 transition-all shadow-sm">
              <div className="h-12 w-12 rounded-xl bg-violet-600/10 text-violet-600 dark:text-violet-400 flex items-center justify-center font-bold text-xl mb-6">1</div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">Define Limits</h3>
              <p className="text-slate-655 dark:text-slate-400 text-sm leading-relaxed">
                Input your maximum budget, starting location, travel duration, and trip category (Beach, Adventure, Nature, etc.).
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 rounded-2xl hover:border-violet-500/50 transition-all shadow-sm">
              <div className="h-12 w-12 rounded-xl bg-violet-600/10 text-violet-600 dark:text-violet-400 flex items-center justify-center font-bold text-xl mb-6">2</div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">Slide to Comfort</h3>
              <p className="text-slate-655 dark:text-slate-400 text-sm leading-relaxed">
                Use the slider to balance comfort and savings. BudgetBound adjusts transport modes (Flights vs Trains) and hotels instantly.
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 rounded-2xl hover:border-violet-500/50 transition-all shadow-sm">
              <div className="h-12 w-12 rounded-xl bg-violet-600/10 text-violet-600 dark:text-violet-400 flex items-center justify-center font-bold text-xl mb-6">3</div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">Get Custom Plan</h3>
              <p className="text-slate-655 dark:text-slate-400 text-sm leading-relaxed">
                Review complete cost breakdowns, pre-calculated hidden expenses, and get a generated daily itinerary in seconds.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">Engineered for Smart Travelers</h2>
          <p className="text-slate-600 dark:text-slate-400">Everything you need to plan and track travel expenses under a single unified dashboard.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div className="flex flex-col gap-4">
            <div className="h-12 w-12 rounded-lg bg-violet-600/10 text-violet-600 dark:text-violet-400 flex items-center justify-center">
              <TrendingUp size={24} />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Interactive Budget Sliders</h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">Adjust lodging tiers, transportation modes, and activities dynamically with real-time math.</p>
          </div>

          <div className="flex flex-col gap-4">
            <div className="h-12 w-12 rounded-lg bg-violet-600/10 text-violet-600 dark:text-violet-400 flex items-center justify-center">
              <Compass size={24} />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Reverse Search Engine</h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">Submit your budget and receive the top 5 locations in India sorted by custom value and rating algorithms.</p>
          </div>

          <div className="flex flex-col gap-4">
            <div className="h-12 w-12 rounded-lg bg-violet-600/10 text-violet-600 dark:text-violet-400 flex items-center justify-center">
              <ShieldCheck size={24} />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Budget Optimizer</h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">Identify expensive line items and switch from luxury stays or flights to save 30% to 50% instantly.</p>
          </div>

          <div className="flex flex-col gap-4">
            <div className="h-12 w-12 rounded-lg bg-violet-600/10 text-violet-600 dark:text-violet-400 flex items-center justify-center">
              <MapPin size={24} />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Daily Itinerary & PDF</h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">Generate complete day-by-day sightseeing programs and download high-quality PDF reports for offline viewing.</p>
          </div>
        </div>
      </section>

      {/* Sample Plans Section */}
      <section className="bg-slate-100/50 dark:bg-slate-950/60 py-24 border-t border-slate-200 dark:border-slate-800 transition-colors">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-16">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">Sample Trip Packages</h2>
              <p className="text-slate-600 dark:text-slate-400 font-medium">Sneak peek at what BudgetBound creates for different categories.</p>
            </div>
            <Link to="/register" className="mt-4 md:mt-0 text-violet-600 dark:text-violet-400 hover:text-violet-500 font-semibold inline-flex items-center gap-2">
              Explore 50+ Indian Destinations
              <ArrowRight size={16} />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {samplePlans.map((plan, idx) => (
              <div key={idx} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden group hover:border-slate-350 dark:hover:border-slate-700 transition-all duration-300 shadow-sm">
                <div className="h-48 overflow-hidden relative">
                  <img 
                    src={plan.img} 
                    alt={plan.name} 
                    className="w-full h-full object-cover group-hover:scale-105 transition-all duration-500"
                  />
                  <span className="absolute top-4 left-4 bg-violet-600 text-white text-xs font-bold px-2.5 py-1 rounded-full">
                    {plan.tag}
                  </span>
                  <span className="absolute bottom-4 right-4 bg-slate-950/80 backdrop-blur text-white text-xs font-bold px-2.5 py-1 rounded-md">
                    {plan.category}
                  </span>
                </div>
                <div className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs text-slate-500 dark:text-slate-400 font-bold">{plan.state}</span>
                    <div className="flex items-center gap-1 text-amber-500">
                      <Star size={14} fill="currentColor" />
                      <span className="text-xs font-extrabold">{plan.rating}</span>
                    </div>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">{plan.name}</h3>
                  <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-4 mt-4">
                    <span className="text-slate-550 dark:text-slate-400 text-xs">{plan.days} Days / Person</span>
                    <span className="text-violet-600 dark:text-violet-400 font-extrabold text-lg">{plan.cost}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-24 max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">What Smart Travelers Say</h2>
          <p className="text-slate-655 dark:text-slate-400 font-medium">Loved by budget explorers, family planners, and solo adventurers.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 p-6 rounded-xl shadow-sm">
            <div className="flex items-center gap-1 text-amber-500 mb-4">
              {[...Array(5)].map((_, i) => <Star key={i} size={16} fill="currentColor" />)}
            </div>
            <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed mb-6">
              "BudgetBound saved me hours of spreadsheets! I entered ₹15,000 for my Munnar trip, and the engine correctly recommended trains and standard homestays that fit exactly."
            </p>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-violet-600/10 text-violet-600 dark:text-violet-400 flex items-center justify-center font-extrabold text-xs">NK</div>
              <div>
                <h4 className="text-slate-900 dark:text-white text-sm font-bold">Nikhil Kumar</h4>
                <span className="text-xs text-slate-500">Solo Explorer</span>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 p-6 rounded-xl shadow-sm">
            <div className="flex items-center gap-1 text-amber-500 mb-4">
              {[...Array(5)].map((_, i) => <Star key={i} size={16} fill="currentColor" />)}
            </div>
            <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed mb-6">
              "We wanted a family trip within ₹40,000. BudgetBound recommended South Goa with full daily itineraries and flight cost adjustments that fit. Absolutely fantastic!"
            </p>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-violet-600/10 text-violet-600 dark:text-violet-400 flex items-center justify-center font-extrabold text-xs">PR</div>
              <div>
                <h4 className="text-slate-900 dark:text-white text-sm font-bold">Priya Sharma</h4>
                <span className="text-xs text-slate-500">Family Planner</span>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 p-6 rounded-xl shadow-sm">
            <div className="flex items-center gap-1 text-amber-500 mb-4">
              {[...Array(5)].map((_, i) => <Star key={i} size={16} fill="currentColor" />)}
            </div>
            <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed mb-6">
              "The cost breakdown and prediction of hidden costs (local cabs, tolls) are highly accurate. I can log my live expenses and cross-reference estimated vs actual instantly."
            </p>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-violet-600/10 text-violet-600 dark:text-violet-400 flex items-center justify-center font-extrabold text-xs">AS</div>
              <div>
                <h4 className="text-slate-900 dark:text-white text-sm font-bold">Amit Sen</h4>
                <span className="text-xs text-slate-500">Weekend Trekker</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-violet-900 via-indigo-900 to-slate-950 py-20 border-t border-slate-850 dark:border-slate-800 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#00000010_1px,transparent_1px),linear-gradient(to_bottom,#00000010_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        <div className="max-w-4xl mx-auto px-6 relative z-10">
          <h2 className="text-3xl md:text-5xl font-extrabold text-white mb-6">Ready to Travel Within Limits?</h2>
          <p className="text-slate-300 max-w-xl mx-auto mb-8 text-sm md:text-base">
            Create a free account, outline your budget, and download a professional travel itinerary in less than two minutes.
          </p>
          <Link 
            to="/register" 
            className="inline-flex items-center gap-2 bg-white text-slate-900 font-bold px-8 py-4 rounded-full hover:bg-slate-100 transition-all shadow-lg hover:scale-105"
          >
            Start Planning Now
            <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800/80 py-12 text-center text-xs text-slate-500 transition-colors">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <Wallet className="h-5 w-5 text-violet-600" />
            <span className="font-bold text-base text-slate-800 dark:text-white tracking-tight">BudgetBound</span>
          </div>
          <p>© 2026 BudgetBound Travel Technology. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};
