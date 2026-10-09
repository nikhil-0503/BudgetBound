import React, { useState } from 'react';
import { MapPin, Plus, X, Calendar, Users, DollarSign, Loader, Sparkles, AlertCircle } from 'lucide-react';
import api from '../services/api';

interface Stop {
  id: string;
  destination: string;
  days: number;
}

export const MultiStopPlanner: React.FC = () => {
  const [stops, setStops] = useState<Stop[]>([
    { id: '1', destination: '', days: 2 },
    { id: '2', destination: '', days: 2 }
  ]);
  const [totalBudget, setTotalBudget] = useState<number>(50000);
  const [specialRequests, setSpecialRequests] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const addStop = () => {
    if (stops.length >= 6) {
      setError('Maximum 6 stops allowed');
      return;
    }
    setStops([...stops, { id: Date.now().toString(), destination: '', days: 2 }]);
  };

  const removeStop = (id: string) => {
    if (stops.length <= 2) {
      setError('Minimum 2 stops required');
      return;
    }
    setStops(stops.filter(stop => stop.id !== id));
  };

  const updateStop = (id: string, field: 'destination' | 'days', value: string | number) => {
    setStops(stops.map(stop => 
      stop.id === id ? { ...stop, [field]: value } : stop
    ));
  };

  const handleGenerate = async () => {
    setError(null);
    
    // Validation
    const emptyDestinations = stops.filter(s => !s.destination.trim());
    if (emptyDestinations.length > 0) {
      setError('Please fill in all destination names');
      return;
    }

    const invalidDays = stops.filter(s => s.days < 1);
    if (invalidDays.length > 0) {
      setError('Each stop must have at least 1 day');
      return;
    }

    if (totalBudget < 10000) {
      setError('Minimum budget is ₹10,000');
      return;
    }

    setLoading(true);

    try {
      const response = await api.post('/api/ai/multistop-plan', {
        stops: stops.map(s => ({ destination: s.destination, days: s.days })),
        budget: totalBudget,
        special: specialRequests
      });

      setResult(response.data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to generate multi-stop plan. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!result) return;

    try {
      const response = await api.post('/api/trips/multistop', {
        trip_name: result.trip_name || 'Multi-Stop Trip',
        total_budget: totalBudget,
        total_days: stops.reduce((sum, s) => sum + s.days, 0),
        destinations_str: stops.map(s => s.destination).join(' -> '),
        raw_json: result
      });

      alert('Multi-stop trip saved successfully!');
      window.location.href = '/my-trips';
    } catch (err: any) {
      console.error(err);
      alert('Failed to save trip. Please try again.');
    }
  };

  const totalDays = stops.reduce((sum, stop) => sum + stop.days, 0);

  return (
    <div className="flex flex-col gap-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <p className="eyebrow-rule text-marigold-700 dark:text-marigold-400 text-xs font-semibold">Advanced Planning</p>
        <h1 className="font-display text-3xl font-semibold text-ink-900 dark:text-paper-50 mt-1">
          Multi-Stop Trip Planner
        </h1>
        <p className="text-sm text-paper-600 dark:text-paper-400 mt-2">
          Plan a journey across multiple destinations with AI-powered itinerary generation
        </p>
      </div>

      {error && (
        <div className="ticket bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900 p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-red-900 dark:text-red-200 font-medium">Error</p>
            <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-red-600 dark:text-red-400 hover:text-red-700">
            <X size={16} />
          </button>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Left Column - Input Form */}
        <div className="flex flex-col gap-6">
          {/* Stops Configuration */}
          <div className="ticket p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-lg font-semibold text-ink-900 dark:text-paper-50">
                <MapPin className="inline h-5 w-5 mr-2 text-marigold-600" />
                Route Stops
              </h2>
              <span className="text-xs text-paper-600 dark:text-paper-400">
                {stops.length}/6 stops
              </span>
            </div>

            <div className="space-y-4">
              {stops.map((stop, index) => (
                <div key={stop.id} className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-marigold-100 dark:bg-marigold-900 flex items-center justify-center text-marigold-700 dark:text-marigold-300 font-semibold text-sm">
                    {index + 1}
                  </div>
                  
                  <input
                    type="text"
                    placeholder="e.g., Paris, Goa, Bangkok"
                    value={stop.destination}
                    onChange={(e) => updateStop(stop.id, 'destination', e.target.value)}
                    className="flex-1 bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-lg px-3 py-2 text-sm text-paper-900 dark:text-white focus:outline-none focus:border-marigold-500"
                  />
                  
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min="1"
                      max="30"
                      value={stop.days}
                      onChange={(e) => updateStop(stop.id, 'days', parseInt(e.target.value) || 1)}
                      className="w-16 bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-lg px-2 py-2 text-sm text-paper-900 dark:text-white focus:outline-none focus:border-marigold-500"
                    />
                    <span className="text-xs text-paper-600 dark:text-paper-400">days</span>
                  </div>

                  {stops.length > 2 && (
                    <button
                      onClick={() => removeStop(stop.id)}
                      className="text-red-600 hover:text-red-700 dark:text-red-400"
                    >
                      <X size={18} />
                    </button>
                  )}
                </div>
              ))}
            </div>

            {stops.length < 6 && (
              <button
                onClick={addStop}
                className="w-full mt-4 py-2 border-2 border-dashed border-paper-300 dark:border-paper-700 rounded-lg text-sm text-paper-600 dark:text-paper-400 hover:border-marigold-500 hover:text-marigold-600 dark:hover:text-marigold-400 transition-colors flex items-center justify-center gap-2"
              >
                <Plus size={16} />
                Add Another Stop
              </button>
            )}
          </div>

          {/* Budget & Details */}
          <div className="ticket p-6">
            <h2 className="font-display text-lg font-semibold text-ink-900 dark:text-paper-50 mb-4">
              <DollarSign className="inline h-5 w-5 mr-2 text-marigold-600" />
              Budget & Preferences
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-paper-600 dark:text-paper-400 mb-2">
                  Total Budget (₹)
                </label>
                <input
                  type="number"
                  min="10000"
                  step="1000"
                  value={totalBudget}
                  onChange={(e) => setTotalBudget(parseInt(e.target.value) || 10000)}
                  className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-lg px-4 py-3 text-sm text-paper-900 dark:text-white focus:outline-none focus:border-marigold-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-paper-600 dark:text-paper-400 mb-2">
                  Special Requests (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g., vegetarian food, budget hotels, adventure activities..."
                  value={specialRequests}
                  onChange={(e) => setSpecialRequests(e.target.value)}
                  className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-lg px-4 py-3 text-sm text-paper-900 dark:text-white focus:outline-none focus:border-marigold-500 resize-none"
                />
              </div>
            </div>
          </div>

          {/* Summary */}
          <div className="ticket bg-marigold-50 dark:bg-marigold-950/20 border-marigold-200 dark:border-marigold-900 p-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-xs text-paper-600 dark:text-paper-400 mb-1">Stops</p>
                <p className="text-xl font-bold text-marigold-700 dark:text-marigold-300">{stops.length}</p>
              </div>
              <div>
                <p className="text-xs text-paper-600 dark:text-paper-400 mb-1">Total Days</p>
                <p className="text-xl font-bold text-marigold-700 dark:text-marigold-300">{totalDays}</p>
              </div>
              <div>
                <p className="text-xs text-paper-600 dark:text-paper-400 mb-1">Budget</p>
                <p className="text-xl font-bold text-marigold-700 dark:text-marigold-300">₹{totalBudget.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full btn-primary py-4 text-base font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
          >
            {loading ? (
              <>
                <Loader className="animate-spin" size={20} />
                Generating AI Plan...
              </>
            ) : (
              <>
                <Sparkles size={20} />
                Generate Multi-Stop Plan
              </>
            )}
          </button>
        </div>

        {/* Right Column - Results */}
        <div className="flex flex-col gap-6">
          {!result && !loading && (
            <div className="ticket p-12 flex flex-col items-center justify-center text-center h-full">
              <MapPin className="h-16 w-16 text-paper-300 dark:text-paper-700 mb-4" />
              <h3 className="font-display text-lg font-semibold text-paper-600 dark:text-paper-400 mb-2">
                No Plan Yet
              </h3>
              <p className="text-sm text-paper-500 dark:text-paper-500">
                Configure your stops and click "Generate Multi-Stop Plan" to see AI-powered recommendations
              </p>
            </div>
          )}

          {loading && (
            <div className="ticket p-12 flex flex-col items-center justify-center text-center h-full">
              <Loader className="h-12 w-12 text-marigold-600 animate-spin mb-4" />
              <h3 className="font-display text-lg font-semibold text-paper-900 dark:text-paper-50 mb-2">
                Creating Your Journey...
              </h3>
              <p className="text-sm text-paper-600 dark:text-paper-400">
                AI is planning the perfect multi-stop itinerary for you
              </p>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <div className="ticket p-6">
                <h2 className="font-display text-xl font-semibold text-ink-900 dark:text-paper-50 mb-2">
                  {result.trip_name || 'Your Multi-Stop Journey'}
                </h2>
                <p className="text-sm text-paper-600 dark:text-paper-400 mb-4">
                  {result.summary || 'AI-generated multi-stop itinerary'}
                </p>

                {result.stops && result.stops.length > 0 && (
                  <div className="space-y-3 mt-6">
                    {result.stops.map((stop: any, index: number) => (
                      <div key={index} className="bg-paper-50 dark:bg-paper-900 rounded-lg p-4">
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-marigold-600 text-white flex items-center justify-center font-semibold text-sm">
                            {index + 1}
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold text-paper-900 dark:text-white mb-1">
                              {stop.destination || stops[index]?.destination}
                            </h3>
                            <p className="text-xs text-paper-600 dark:text-paper-400 mb-2">
                              {stop.days || stops[index]?.days} days • Est. ₹{stop.estimated_cost?.toLocaleString() || 'TBD'}
                            </p>
                            {stop.highlights && (
                              <ul className="text-xs text-paper-700 dark:text-paper-300 space-y-1">
                                {stop.highlights.slice(0, 3).map((highlight: string, i: number) => (
                                  <li key={i}>• {highlight}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="mt-6 pt-6 border-t border-paper-200 dark:border-paper-700">
                  <div className="flex justify-between items-center text-sm mb-2">
                    <span className="text-paper-600 dark:text-paper-400">Total Estimated Cost</span>
                    <span className="font-semibold text-paper-900 dark:text-white">
                      ₹{result.total_estimated_cost?.toLocaleString() || totalBudget.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-paper-600 dark:text-paper-400">Budget Balance</span>
                    <span className={`font-semibold ${
                      (result.total_estimated_cost || 0) <= totalBudget 
                        ? 'text-green-600 dark:text-green-400' 
                        : 'text-red-600 dark:text-red-400'
                    }`}>
                      ₹{(totalBudget - (result.total_estimated_cost || 0)).toLocaleString()}
                    </span>
                  </div>
                </div>

                <button
                  onClick={handleSave}
                  className="w-full btn-primary mt-6 py-3"
                >
                  Save Trip Plan
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
