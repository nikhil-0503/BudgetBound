import React from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { useTheme } from '../context/ThemeContext';
import {
  Compass,
  MapPin,
  TrendingUp,
  Wallet,
  ShieldCheck,
  ArrowRight,
  Star,
  Sun,
  Moon
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  usePageTitle('BudgetBound - Travel Budget Planner');
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

  const receiptLines = [
    { label: 'Sleeper train, Bengaluru → Munnar', amount: 1450 },
    { label: 'Homestay, 3 nights', amount: 5100 },
    { label: 'Local transit & tea-estate entry', amount: 1800 },
    { label: 'Meals, 4 days', amount: 2600 },
    { label: 'Emergency reserve (hidden costs)', amount: 1100 },
  ];
  const receiptTotal = receiptLines.reduce((s, l) => s + l.amount, 0);

  return (
    <div className="min-h-screen bg-paper-100 dark:bg-ink-950 text-ink-900 dark:text-paper-100 overflow-x-hidden selection:bg-marigold-400 selection:text-ink-950 transition-colors duration-200">

      {/* Navigation */}
      <nav className="w-full max-w-6xl mx-auto px-6 py-6 flex items-center justify-between relative">
        <div className="flex items-center gap-2">
          <Wallet className="h-7 w-7 text-marigold-600" />
          <span className="font-display font-semibold text-2xl tracking-tight text-ink-900 dark:text-paper-50">
            BudgetBound
          </span>
        </div>
        <div className="flex items-center gap-4 md:gap-6">
          <button
            onClick={toggleTheme}
            className="p-2.5 rounded-full border border-paper-300 dark:border-ink-700 bg-paper-50 dark:bg-ink-900 text-paper-600 dark:text-paper-300 hover:bg-paper-200 dark:hover:bg-ink-800 transition-colors"
            title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <Link to="/login" className="text-sm font-medium text-paper-700 dark:text-paper-300 hover:text-ink-950 dark:hover:text-white transition-colors">
            Log in
          </Link>
          <Link
            to="/register"
            className="text-sm font-semibold bg-marigold-500 hover:bg-marigold-400 text-ink-950 px-5 py-2.5 rounded-full transition-all duration-200"
          >
            Start planning
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-24 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        <div>
          <p className="eyebrow-rule text-marigold-700 dark:text-marigold-400 text-sm font-semibold mb-6">
            A trip planner that starts with your wallet
          </p>
          <h1 className="font-display text-4xl md:text-5xl font-semibold leading-[1.1] text-ink-900 dark:text-paper-50 mb-6">
            Tell us what you can spend. We'll tell you where that takes you.
          </h1>
          <p className="text-base md:text-lg text-paper-700 dark:text-paper-300 max-w-lg mb-10 leading-relaxed">
            Most planners ask where you want to go, then break the news about the cost. BudgetBound works the other way: give us a budget, a starting city, and how many days you have, and we build the itinerary — lodging, transit, food, and the hidden costs — to fit inside it.
          </p>

          <div className="flex flex-col sm:flex-row items-start gap-4 mb-10">
            <Link
              to="/register"
              className="inline-flex items-center justify-center gap-2 bg-marigold-500 hover:bg-marigold-400 text-ink-950 font-semibold px-7 py-3.5 rounded-full transition-all"
            >
              Plan your first trip
              <ArrowRight size={18} />
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex items-center justify-center gap-2 border border-paper-300 dark:border-ink-600 text-paper-700 dark:text-paper-200 font-semibold px-7 py-3.5 rounded-full hover:bg-paper-200/60 dark:hover:bg-ink-800 transition-all"
            >
              See how it works
            </a>
          </div>

          <div className="flex items-center gap-2 text-amber-500">
            {[...Array(5)].map((_, i) => <Star key={i} size={15} fill="currentColor" />)}
            <span className="text-xs text-paper-600 dark:text-paper-400 font-medium ml-1">Rated 4.7 by budget travelers across India</span>
          </div>
        </div>

        {/* Receipt mockup — the product's core idea, made literal */}
        <div className="relative mx-auto w-full max-w-sm">
          <div className="absolute -inset-x-4 top-6 h-full bg-petrol-600/10 dark:bg-petrol-500/10 rounded-2xl -z-10 rotate-2" />
          <div className="ticket p-0 shadow-lg">
            <div className="px-6 pt-6 pb-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-paper-500 dark:text-paper-400">Munnar, Kerala</span>
                <span className="text-xs font-num text-paper-500 dark:text-paper-400">4 days</span>
              </div>
              <h3 className="font-display text-lg font-semibold text-ink-900 dark:text-paper-50">Trip cost breakdown</h3>
            </div>
            <div className="ticket-perforation" />
            <div className="px-6 py-5 flex flex-col gap-3">
              {receiptLines.map((line) => (
                <div key={line.label} className="flex items-baseline justify-between gap-4 text-sm">
                  <span className="text-paper-700 dark:text-paper-300">{line.label}</span>
                  <span className="font-num text-ink-800 dark:text-paper-100 shrink-0">₹{line.amount.toLocaleString('en-IN')}</span>
                </div>
              ))}
            </div>
            <div className="ticket-perforation" />
            <div className="px-6 py-5 flex items-center justify-between">
              <span className="text-sm font-semibold text-ink-900 dark:text-paper-50">Total, within budget</span>
              <span className="font-num text-xl font-semibold text-petrol-700 dark:text-petrol-400">₹{receiptTotal.toLocaleString('en-IN')}</span>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="bg-paper-50 dark:bg-ink-900 py-24 border-t border-b border-paper-300 dark:border-ink-700 transition-colors">
        <div className="max-w-6xl mx-auto px-6">
          <div className="max-w-2xl mb-16">
            <h2 className="font-display text-3xl md:text-4xl font-semibold text-ink-900 dark:text-paper-50 mb-4">Three steps, in order</h2>
            <p className="text-paper-700 dark:text-paper-400">No mood boards, no browsing — just the constraints that decide a real trip.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-paper-300 dark:bg-ink-700 rounded-2xl overflow-hidden border border-paper-300 dark:border-ink-700">
            <div className="bg-paper-50 dark:bg-ink-900 p-8">
              <span className="font-display text-3xl text-marigold-600 dark:text-marigold-400">01</span>
              <h3 className="text-lg font-semibold text-ink-900 dark:text-paper-50 mt-4 mb-3">Set your limits</h3>
              <p className="text-paper-700 dark:text-paper-400 text-sm leading-relaxed">
                Your maximum budget, starting city, how many days you have, and the kind of trip — beach, adventure, nature, religious, and more.
              </p>
            </div>

            <div className="bg-paper-50 dark:bg-ink-900 p-8">
              <span className="font-display text-3xl text-marigold-600 dark:text-marigold-400">02</span>
              <h3 className="text-lg font-semibold text-ink-900 dark:text-paper-50 mt-4 mb-3">Slide toward comfort</h3>
              <p className="text-paper-700 dark:text-paper-400 text-sm leading-relaxed">
                One slider trades savings for comfort. Move it and watch trains become flights, and homestays become hotels, instantly.
              </p>
            </div>

            <div className="bg-paper-50 dark:bg-ink-900 p-8">
              <span className="font-display text-3xl text-marigold-600 dark:text-marigold-400">03</span>
              <h3 className="text-lg font-semibold text-ink-900 dark:text-paper-50 mt-4 mb-3">Get your plan</h3>
              <p className="text-paper-700 dark:text-paper-400 text-sm leading-relaxed">
                A full cost breakdown, hidden expenses accounted for, and a day-by-day itinerary — ready to save or take offline as a PDF.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 max-w-6xl mx-auto px-6">
        <div className="max-w-2xl mb-16">
          <h2 className="font-display text-3xl md:text-4xl font-semibold text-ink-900 dark:text-paper-50 mb-4">What's actually in the tool</h2>
          <p className="text-paper-700 dark:text-paper-400">Everything needed to plan a trip and keep it on budget once you're there.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div className="flex flex-col gap-4">
            <TrendingUp size={22} className="text-marigold-600 dark:text-marigold-400" />
            <h3 className="text-base font-semibold text-ink-900 dark:text-paper-50">Live budget sliders</h3>
            <p className="text-paper-700 dark:text-paper-400 text-sm leading-relaxed">Adjust lodging tier, transport mode, and activities, and see the total update in real time.</p>
          </div>

          <div className="flex flex-col gap-4">
            <Compass size={22} className="text-marigold-600 dark:text-marigold-400" />
            <h3 className="text-base font-semibold text-ink-900 dark:text-paper-50">Reverse search</h3>
            <p className="text-paper-700 dark:text-paper-400 text-sm leading-relaxed">Enter your budget alone and get back the five Indian destinations that fit it best.</p>
          </div>

          <div className="flex flex-col gap-4">
            <ShieldCheck size={22} className="text-marigold-600 dark:text-marigold-400" />
            <h3 className="text-base font-semibold text-ink-900 dark:text-paper-50">Budget optimizer</h3>
            <p className="text-paper-700 dark:text-paper-400 text-sm leading-relaxed">Flags the most expensive line items and suggests swaps that can cut 30–50% off the total.</p>
          </div>

          <div className="flex flex-col gap-4">
            <MapPin size={22} className="text-marigold-600 dark:text-marigold-400" />
            <h3 className="text-base font-semibold text-ink-900 dark:text-paper-50">Day-by-day PDF</h3>
            <p className="text-paper-700 dark:text-paper-400 text-sm leading-relaxed">A full sightseeing schedule you can download and carry with you, no signal required.</p>
          </div>
        </div>
      </section>

      {/* Sample Plans Section */}
      <section className="bg-paper-50 dark:bg-ink-900 py-24 border-t border-paper-300 dark:border-ink-700 transition-colors">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-4">
            <div>
              <h2 className="font-display text-3xl md:text-4xl font-semibold text-ink-900 dark:text-paper-50 mb-4">A few sample trips</h2>
              <p className="text-paper-700 dark:text-paper-400">What BudgetBound builds for a few different budgets and trip styles.</p>
            </div>
            <Link to="/register" className="text-marigold-700 dark:text-marigold-400 hover:text-marigold-600 font-semibold inline-flex items-center gap-2 shrink-0">
              See 50+ Indian destinations
              <ArrowRight size={16} />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {samplePlans.map((plan, idx) => (
              <div key={idx} className="ticket p-0 overflow-hidden group">
                <div className="h-44 overflow-hidden relative">
                  <img
                    src={plan.img}
                    alt={plan.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-all duration-500"
                  />
                  <span className="absolute top-4 left-4 bg-marigold-500 text-ink-950 text-xs font-semibold px-2.5 py-1 rounded-full">
                    {plan.tag}
                  </span>
                  <span className="absolute bottom-4 right-4 bg-ink-950/80 backdrop-blur text-white text-xs font-semibold px-2.5 py-1 rounded-md">
                    {plan.category}
                  </span>
                </div>
                <div className="ticket-perforation" />
                <div className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs text-paper-500 dark:text-paper-400 font-semibold">{plan.state}</span>
                    <div className="flex items-center gap-1 text-amber-500">
                      <Star size={14} fill="currentColor" />
                      <span className="text-xs font-num font-semibold">{plan.rating}</span>
                    </div>
                  </div>
                  <h3 className="text-lg font-semibold text-ink-900 dark:text-paper-50 mb-3">{plan.name}</h3>
                  <div className="flex items-center justify-between pt-3 border-t border-paper-200 dark:border-ink-700">
                    <span className="text-paper-600 dark:text-paper-400 text-xs">{plan.days} days / person</span>
                    <span className="font-num text-petrol-700 dark:text-petrol-400 font-semibold text-lg">{plan.cost}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-24 max-w-6xl mx-auto px-6">
        <div className="max-w-2xl mb-16">
          <h2 className="font-display text-3xl md:text-4xl font-semibold text-ink-900 dark:text-paper-50 mb-4">From people who've used it</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { quote: "I entered ₹15,000 for a Munnar trip and the engine correctly recommended trains and homestays that fit exactly. Saved me hours of spreadsheets.", name: 'Nikhil Kumar', role: 'Solo explorer', initials: 'NK' },
            { quote: "We wanted a family trip under ₹40,000. It suggested South Goa with a full itinerary and flight costs that actually fit our budget.", name: 'Priya Sharma', role: 'Family planner', initials: 'PR' },
            { quote: "The hidden-cost predictions — local cabs, tolls — are accurate. I log expenses as I go and compare them against the estimate instantly.", name: 'Amit Sen', role: 'Weekend trekker', initials: 'AS' },
          ].map((t) => (
            <div key={t.name} className="ticket p-6">
              <div className="flex items-center gap-1 text-amber-500 mb-4">
                {[...Array(5)].map((_, i) => <Star key={i} size={15} fill="currentColor" />)}
              </div>
              <p className="text-paper-700 dark:text-paper-300 text-sm leading-relaxed mb-6">{t.quote}</p>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-marigold-100 dark:bg-marigold-950/50 text-marigold-700 dark:text-marigold-400 flex items-center justify-center font-display font-semibold text-xs">{t.initials}</div>
                <div>
                  <h4 className="text-ink-900 dark:text-paper-50 text-sm font-semibold">{t.name}</h4>
                  <span className="text-xs text-paper-500">{t.role}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-ink-900 dark:bg-ink-950 py-20 border-t border-ink-800 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff08_1px,transparent_1px),linear-gradient(to_bottom,#ffffff08_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        <div className="max-w-3xl mx-auto px-6 relative z-10">
          <h2 className="font-display text-3xl md:text-5xl font-semibold text-paper-50 mb-6">Ready to travel within limits?</h2>
          <p className="text-paper-300 max-w-xl mx-auto mb-8 text-sm md:text-base">
            Create a free account, set a budget, and have a full itinerary in under two minutes.
          </p>
          <Link
            to="/register"
            className="inline-flex items-center gap-2 bg-marigold-500 hover:bg-marigold-400 text-ink-950 font-semibold px-8 py-4 rounded-full transition-all"
          >
            Start planning now
            <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-paper-50 dark:bg-ink-950 border-t border-paper-300 dark:border-ink-800 py-12 text-center text-xs text-paper-500 transition-colors">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <Wallet className="h-5 w-5 text-marigold-600" />
            <span className="font-display font-semibold text-base text-ink-800 dark:text-paper-50 tracking-tight">BudgetBound</span>
          </div>
          <p>© 2026 BudgetBound Travel Technology. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};
