import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import {
  Sparkles,
  MessageSquare,
  Compass,
  Shuffle,
  HelpCircle,
  Loader,
  AlertCircle,
  Send,
  User,
  Bot,
  MapPin,
  Plus,
  Trash2,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface SavedTrip {
  id: number;
  destination: {
    name: string;
  };
  budget: number;
  total_estimated_cost: number;
}

export const AICompanion: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'chat' | 'planner' | 'regenerator' | 'explain' | 'multistop'>('chat');
  const [savedTrips, setSavedTrips] = useState<SavedTrip[]>([]);

  // Error overlay popup state
  const [showAIErrorModal, setShowAIErrorModal] = useState(false);
  const [modalMessage, setModalMessage] = useState('');

  // 1. Chat Assistant states
  const [chatMessages, setChatMessages] = useState<Array<{ sender: 'user' | 'bot'; text: string }>>([
    { sender: 'bot', text: 'Hello! I am your BudgetBound AI Companion. Ask me anything about planning trips, local cuisines, or saving tips!' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // 2. Personalized Planner states
  const [prefKeywords, setPrefKeywords] = useState('');
  const [prefBudget, setPrefBudget] = useState(25000);
  const [prefDays, setPrefDays] = useState(5);
  const [prefSpecial, setPrefSpecial] = useState('');
  const [planningLoading, setPlanningLoading] = useState(false);
  const [plannedResult, setPlannedResult] = useState<any | null>(null);

  // 3. Trip Regenerator states
  const [regenTripId, setRegenTripId] = useState('');
  const [regenInstruction, setRegenInstruction] = useState('');
  const [regeneratingLoading, setRegeneratingLoading] = useState(false);
  const [regeneratedResult, setRegeneratedResult] = useState<any | null>(null);
  const [applyingRegen, setApplyingRegen] = useState(false);

  // 4. Explainability states
  const [explainTripId, setExplainTripId] = useState('');
  const [explainingLoading, setExplainingLoading] = useState(false);
  const [explanationText, setExplanationText] = useState<string | null>(null);

  // Fetch saved trips for dropdowns on mount
  useEffect(() => {
    const fetchTrips = async () => {
      try {
        const response = await api.get('/api/trips/');
        setSavedTrips(response.data);
        if (response.data.length > 0) {
          setRegenTripId(response.data[0].id.toString());
          setExplainTripId(response.data[0].id.toString());
        }
      } catch (e) {
        console.error("Failed to load user trips", e);
      }
    };

    fetchTrips();
  }, []);

  const triggerAIError = (message: string) => {
    setModalMessage(message);
    setShowAIErrorModal(true);
  };

  // Submit Handlers (All capture service unavailable messages from API)
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userMsg = chatInput;
    const updatedMessages: Array<{ sender: 'user' | 'bot'; text: string }> = [...chatMessages, { sender: 'user', text: userMsg }];
    setChatMessages(updatedMessages);
    setChatInput('');
    setChatLoading(true);

    try {
      const apiMessages = updatedMessages.map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.text
      }));
      const response = await api.post('/api/ai/chat', { messages: apiMessages });
      setChatMessages(prev => [...prev, { sender: 'bot', text: response.data.reply }]);
    } catch (err: any) {
      console.error(err);
      const errMsg = err.response?.data?.detail || "AI service not connected yet. This feature will be available after API integration.";
      setChatMessages(prev => [...prev, { sender: 'bot', text: errMsg }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handlePlannerSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPlanningLoading(true);
    setPlannedResult(null);
    try {
      const response = await api.post('/api/ai/personalized-plan', {
        preferences: {
          keywords: prefKeywords,
          budget: prefBudget,
          days: prefDays,
          special: prefSpecial
        }
      });
      setPlannedResult(response.data);
    } catch (err: any) {
      console.error(err);
      triggerAIError(err.response?.data?.detail || "AI service not connected yet. API integration pending.");
    } finally {
      setPlanningLoading(false);
    }
  };

  const handleRegenerateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regenTripId) return;
    setRegeneratingLoading(true);
    setRegeneratedResult(null);
    try {
      const response = await api.post('/api/ai/regenerate', {
        trip_id: Number(regenTripId),
        instruction: regenInstruction
      });
      setRegeneratedResult(response.data);
    } catch (err: any) {
      console.error(err);
      triggerAIError(err.response?.data?.detail || "AI service not connected yet. API integration pending.");
    } finally {
      setRegeneratingLoading(false);
    }
  };

  const handleApplyRegen = async () => {
    if (!regenTripId || !regeneratedResult) return;
    setApplyingRegen(true);
    try {
      await api.put(`/api/trips/${regenTripId}`, regeneratedResult);
      alert('Trip schedule and budget regenerated successfully!');
      setRegeneratedResult(null);
      setRegenInstruction('');
      navigate(`/expenses/${regenTripId}`);
    } catch (err) {
      console.error(err);
      alert('Failed to apply regeneration update.');
    } finally {
      setApplyingRegen(false);
    }
  };

  const handleExplainSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!explainTripId) return;
    setExplainingLoading(true);
    setExplanationText(null);
    try {
      const response = await api.post('/api/ai/explain', {
        trip_id: Number(explainTripId)
      });
      setExplanationText(response.data.explanation);
    } catch (err: any) {
      console.error(err);
      triggerAIError(err.response?.data?.detail || "AI service not connected yet. API integration pending.");
    } finally {
      setExplainingLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-8 relative">

      {/* Title */}
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
          <Sparkles className="text-violet-600" />
          AI Copilot Workspace
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Supercharge your travel planning with our LLM modules. Explore personalized planners, chat buddies, and itinerary explainers.
        </p>
      </div>

      {/* Tabs Row */}
      <div className="flex border-b border-slate-200 dark:border-slate-700 overflow-x-auto gap-4 scrollbar-thin scrollbar-thumb-slate-200">

        <button
          onClick={() => setActiveTab('chat')}
          className={`flex items-center gap-2 pb-4 text-xs font-bold uppercase tracking-wider border-b-2 transition-all focus:outline-none shrink-0 ${activeTab === 'chat'
            ? 'border-violet-600 text-violet-600 dark:text-violet-400 dark:border-violet-400'
            : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
            }`}
        >
          <MessageSquare size={16} />
          AI Chat Assistant
        </button>

        <button
          onClick={() => setActiveTab('planner')}
          className={`flex items-center gap-2 pb-4 text-xs font-bold uppercase tracking-wider border-b-2 transition-all focus:outline-none shrink-0 ${activeTab === 'planner'
            ? 'border-violet-600 text-violet-600 dark:text-violet-400 dark:border-violet-400'
            : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
            }`}
        >
          <Compass size={16} />
          AI Personalized Planner
        </button>

        <button
          onClick={() => setActiveTab('regenerator')}
          className={`flex items-center gap-2 pb-4 text-xs font-bold uppercase tracking-wider border-b-2 transition-all focus:outline-none shrink-0 ${activeTab === 'regenerator'
            ? 'border-violet-600 text-violet-600 dark:text-violet-400 dark:border-violet-400'
            : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
            }`}
        >
          <Shuffle size={16} />
          AI Trip Regenerator
        </button>

        <button
          onClick={() => setActiveTab('explain')}
          className={`flex items-center gap-2 pb-4 text-xs font-bold uppercase tracking-wider border-b-2 transition-all focus:outline-none shrink-0 ${activeTab === 'explain'
            ? 'border-violet-600 text-violet-600 dark:text-violet-400 dark:border-violet-400'
            : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
            }`}
        >
          <HelpCircle size={16} />
          AI Explainability
        </button>
      </div>

      {/* Tab Panels */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm min-h-[400px] flex flex-col">

        {/* Panel 1: Chat Assistant */}
        {activeTab === 'chat' && (
          <div className="flex-1 flex flex-col justify-between h-[500px]">
            {/* Messages Display */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 text-xs no-scrollbar">
              {chatMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-3 max-w-[80%] ${msg.sender === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
                    }`}
                >
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 font-bold ${msg.sender === 'user'
                    ? 'bg-violet-100 dark:bg-violet-950 text-violet-600 dark:text-violet-400'
                    : 'bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400'
                    }`}>
                    {msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                  </div>

                  <div className={`p-4 rounded-2xl leading-relaxed border ${msg.sender === 'user'
                    ? 'bg-violet-600 border-violet-600 text-white rounded-tr-none'
                    : 'bg-slate-50 dark:bg-slate-900/60 border-slate-200 dark:border-slate-700/60 text-slate-700 dark:text-slate-300 rounded-tl-none'
                    }`}>
                    {msg.text}
                  </div>
                </div>
              ))}

              {chatLoading && (
                <div className="flex items-start gap-3 mr-auto max-w-[80%]">
                  <div className="h-8 w-8 rounded-full bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 flex items-center justify-center shrink-0">
                    <Loader size={14} className="animate-spin" />
                  </div>
                  <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-700/60 text-slate-400 rounded-tl-none">
                    Analyzing routes...
                  </div>
                </div>
              )}
            </div>

            {/* Input Bar */}
            <form onSubmit={handleChatSubmit} className="border-t border-slate-100 dark:border-slate-700 pt-4 flex gap-3">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask about destination recommendations, hotel buffers or general hacks..."
                className="flex-1 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3.5 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-violet-500"
              />
              <button
                type="submit"
                disabled={chatLoading}
                className="bg-violet-600 hover:bg-violet-500 text-white p-3.5 rounded-xl transition-all shadow-md shadow-violet-500/10 shrink-0"
              >
                <Send size={16} />
              </button>
            </form>
          </div>
        )}

        {/* Panel 2: Personalized Planner */}
        {activeTab === 'planner' && (
          <div className="flex-1 flex flex-col max-w-2xl mx-auto w-full py-4 justify-center">
            <div className="text-center mb-8">
              <Compass className="h-10 w-10 text-violet-500 mx-auto mb-2 animate-bounce" />
              <h3 className="text-base font-bold text-slate-800 dark:text-white">Custom OpenAI Personalized Planner</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 leading-normal">
                Bypass database seeding limits and ask our AI to create custom schedules for anywhere in the world.
              </p>
            </div>

            <form onSubmit={handlePlannerSubmit} className="flex flex-col gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Destination Stays / Keywords</label>
                <input
                  type="text"
                  required
                  value={prefKeywords}
                  onChange={(e) => setPrefKeywords(e.target.value)}
                  placeholder="e.g. Kashmir, Backwaters, Ladakh glaciers"
                  className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-violet-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Max Budget (INR)</label>
                  <input
                    type="number"
                    required
                    value={prefBudget}
                    onChange={(e) => setPrefBudget(Number(e.target.value))}
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-violet-500"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Days Limit</label>
                  <input
                    type="number"
                    required
                    value={prefDays}
                    onChange={(e) => setPrefDays(Number(e.target.value))}
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-violet-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Special Stays / Dietary Needs</label>
                <textarea
                  value={prefSpecial}
                  onChange={(e) => setPrefSpecial(e.target.value)}
                  placeholder="e.g. Vegetarian food only, wheelchair accessible paths, focus on history museums."
                  rows={3}
                  className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-violet-500 resize-none leading-relaxed"
                />
              </div>

              <button
                type="submit"
                disabled={planningLoading}
                className="w-full mt-2 inline-flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold py-3.5 rounded-xl text-xs transition-all shadow-md shadow-violet-500/10"
              >
                {planningLoading ? <Loader size={16} className="animate-spin" /> : null}
                Generate Custom Itinerary
              </button>
            </form>

            {plannedResult && (
              <div className="mt-8 border-t border-slate-150 dark:border-slate-700/60 pt-6 animate-fade-in">
                <div className="bg-slate-50 dark:bg-slate-900/30 border border-slate-200 dark:border-slate-700 rounded-2xl p-6">
                  <h4 className="text-lg font-bold text-violet-600 dark:text-violet-400 mb-1">{plannedResult.plan_name}</h4>
                  <p className="text-xs text-slate-400 mb-4">Estimated Total Expense: <strong className="text-slate-800 dark:text-slate-200">₹{plannedResult.estimated_cost?.toLocaleString()}</strong></p>
                  <p className="text-xs text-slate-600 dark:text-slate-350 leading-relaxed mb-6 bg-white dark:bg-slate-850 p-4 rounded-xl border border-slate-150 dark:border-slate-700">{plannedResult.summary}</p>

                  <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Planned Schedule</h5>
                  <div className="space-y-4">
                    {plannedResult.days?.map((day: any) => (
                      <div key={day.day_number} className="bg-white dark:bg-slate-850 border border-slate-150 dark:border-slate-700 rounded-xl p-4">
                        <div className="font-bold text-xs text-slate-805 dark:text-slate-200 mb-2 pb-1 border-b border-slate-100 dark:border-slate-700">
                          Day {day.day_number} - {day.description}
                        </div>
                        <div className="space-y-2">
                          {day.activities?.map((act: any, aIdx: number) => (
                            <div key={aIdx} className="flex justify-between items-center text-xs">
                              <span className="text-slate-400 font-semibold w-16">{act.time}</span>
                              <span className="text-slate-700 dark:text-slate-300 flex-1 px-2">{act.title}</span>
                              <span className="text-slate-500 font-bold">₹{act.cost}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Panel 3: Trip Regenerator */}
        {activeTab === 'regenerator' && (
          <div className="flex-1 flex flex-col max-w-2xl mx-auto w-full py-4 justify-center">
            <div className="text-center mb-8">
              <Shuffle className="h-10 w-10 text-violet-500 mx-auto mb-2 animate-spin-slow" />
              <h3 className="text-base font-bold text-slate-800 dark:text-white">AI Trip Regenerator</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 leading-normal">
                Optimize or completely reschedule an existing trip using natural language commands.
              </p>
            </div>

            {savedTrips.length === 0 ? (
              <div className="text-center py-6 text-xs text-slate-400 font-medium bg-slate-50 dark:bg-slate-900/35 border border-dashed border-slate-200 dark:border-slate-700 rounded-xl p-6">
                No trips logged in history. Plan a trip before simulating regeneration.
              </div>
            ) : (
              <form onSubmit={handleRegenerateSubmit} className="flex flex-col gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Select Target Trip</label>
                  <select
                    value={regenTripId}
                    onChange={(e) => setRegenTripId(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-violet-500 appearance-none"
                  >
                    {savedTrips.map(t => (
                      <option key={t.id} value={t.id}>
                        {t.destination.name} (Budget: ₹{t.budget.toLocaleString()} — Cost: ₹{t.total_estimated_cost.toLocaleString()})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Regeneration Prompt / Commands</label>
                  <textarea
                    required
                    value={regenInstruction}
                    onChange={(e) => setRegenInstruction(e.target.value)}
                    placeholder="e.g. Make it nature-heavy. Replace flights with trains to save money. Add a free trekking activity on Day 3."
                    rows={4}
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-violet-500 resize-none leading-relaxed"
                  />
                </div>

                <button
                  type="submit"
                  disabled={regeneratingLoading}
                  className="w-full mt-2 inline-flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold py-3.5 rounded-xl text-xs transition-all shadow-md shadow-violet-500/10"
                >
                  {regeneratingLoading ? <Loader size={16} className="animate-spin" /> : null}
                  Regenerate Trip Schedule
                </button>
              </form>
            )}

            {regeneratedResult && (
              <div className="mt-8 border-t border-slate-150 dark:border-slate-700/60 pt-6 animate-fade-in font-sans">
                <div className="bg-slate-50 dark:bg-slate-900/30 border border-slate-200 dark:border-slate-700 rounded-2xl p-6">
                  <h4 className="text-xs font-bold text-slate-800 dark:text-white mb-4">Proposed Itinerary & Allocation Changes</h4>

                  <div className="grid grid-cols-2 gap-4 mb-6 bg-white dark:bg-slate-850 p-4 rounded-xl border border-slate-150 dark:border-slate-700">
                    <div>
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Estimated Accommodation</p>
                      <p className="text-xs font-bold text-slate-800 dark:text-slate-200">₹{regeneratedResult.costs?.hotel_cost?.toLocaleString()} ({regeneratedResult.costs?.hotel_tier})</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Estimated Transit</p>
                      <p className="text-xs font-bold text-slate-800 dark:text-slate-200">₹{regeneratedResult.costs?.transport_cost?.toLocaleString()} ({regeneratedResult.costs?.transport_mode})</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Activity Cost</p>
                      <p className="text-xs font-bold text-slate-800 dark:text-slate-200">₹{regeneratedResult.costs?.activities_cost?.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-400 font-bold uppercase">New Total Cost</p>
                      <p className="text-xs font-bold text-violet-600 dark:text-violet-400">₹{regeneratedResult.costs?.total_estimated_cost?.toLocaleString()}</p>
                    </div>
                  </div>

                  <h5 className="text-[10px] font-bold text-slate-400 uppercase mb-3">New Proposed Itinerary Days</h5>
                  <div className="space-y-4 mb-6">
                    {regeneratedResult.itineraries?.map((day: any) => (
                      <div key={day.day_number} className="bg-white dark:bg-slate-850 border border-slate-150 dark:border-slate-700 rounded-xl p-4">
                        <div className="font-bold text-xs text-slate-850 dark:text-slate-200 mb-2 pb-1 border-b border-slate-100 dark:border-slate-700">
                          Day {day.day_number} - {day.description}
                        </div>
                        <div className="space-y-2">
                          {day.activities?.map((act: any, aIdx: number) => (
                            <div key={aIdx} className="flex justify-between items-center text-xs">
                              <span className="text-slate-400 font-semibold w-16">{act.time}</span>
                              <span className="text-slate-700 dark:text-slate-350 flex-1 px-2">{act.title}</span>
                              <span className="text-slate-505 font-bold">₹{act.cost}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  <button
                    onClick={handleApplyRegen}
                    disabled={applyingRegen}
                    className="w-full inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl text-xs transition-all shadow-md shadow-emerald-500/10"
                  >
                    {applyingRegen ? <Loader size={14} className="animate-spin" /> : null}
                    Apply Regeneration to Trip
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Panel 4: Explainability */}
        {activeTab === 'explain' && (
          <div className="flex-1 flex flex-col max-w-2xl mx-auto w-full py-4 justify-center">
            <div className="text-center mb-8">
              <HelpCircle className="h-10 w-10 text-violet-500 mx-auto mb-2 animate-pulse" />
              <h3 className="text-base font-bold text-slate-800 dark:text-white">AI Itinerary Explainability</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 leading-normal">
                Want to know why the engine selected a certain resort tier, dining budget or local transit mode? Ask our AI for transparency.
              </p>
            </div>

            {savedTrips.length === 0 ? (
              <div className="text-center py-6 text-xs text-slate-400 font-medium bg-slate-50 dark:bg-slate-900/35 border border-dashed border-slate-200 dark:border-slate-700 rounded-xl p-6">
                No trips logged in history. Plan a trip before simulating budget explanation.
              </div>
            ) : (
              <form onSubmit={handleExplainSubmit} className="flex flex-col gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Select Trip to Analyze</label>
                  <select
                    value={explainTripId}
                    onChange={(e) => setExplainTripId(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-violet-500 appearance-none"
                  >
                    {savedTrips.map(t => (
                      <option key={t.id} value={t.id}>
                        {t.destination.name} (Budget: ₹{t.budget.toLocaleString()})
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={explainingLoading}
                  className="w-full mt-2 inline-flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold py-3.5 rounded-xl text-xs transition-all shadow-md shadow-violet-500/10"
                >
                  {explainingLoading ? <Loader size={16} className="animate-spin" /> : null}
                  Analyze Budget Selections
                </button>
              </form>
            )}

            {explanationText && (
              <div className="mt-8 border-t border-slate-150 dark:border-slate-700/60 pt-6 animate-fade-in font-sans">
                <div className="bg-slate-50 dark:bg-slate-900/30 border border-slate-200 dark:border-slate-700 rounded-2xl p-6">
                  <h4 className="text-sm font-bold text-slate-800 dark:text-white mb-4">Budget Selection Analysis</h4>
                  <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-150 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap font-sans">
                    {explanationText}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

      </div>

      {/* Floating Error Dialog Overlay for AI integration placeholders */}
      {showAIErrorModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-6 z-50 animate-fade-in">
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl w-full max-w-sm p-6 shadow-2xl relative text-center">

            <AlertCircle className="h-12 w-12 text-rose-500 mx-auto mb-4 animate-bounce" />

            <h3 className="text-base font-extrabold text-slate-900 dark:text-white mb-2">API Connection Pending</h3>

            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-6">
              {modalMessage}
            </p>

            <button
              onClick={() => setShowAIErrorModal(false)}
              className="w-full bg-slate-900 hover:bg-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 text-white font-bold py-2.5 rounded-xl text-xs transition-all"
            >
              Acknowledge
            </button>
          </div>
        </div>
      )}

    </div>
  );
};
