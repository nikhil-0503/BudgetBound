import React, { useEffect, useState } from 'react';
import { MapPin, Plus, Trash2, ChevronDown, ChevronUp, Loader, Map as MapIcon, Download, Save, Check } from 'lucide-react';
import api from '../services/api';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for leaflet default maker icon missing in react-leaflet
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

type RouteCoordinate = [number, number];

const RouteBounds: React.FC<{ coordinates: RouteCoordinate[] }> = ({ coordinates }) => {
    const map = useMap();

    useEffect(() => {
        if (coordinates.length === 1) {
            map.setView(coordinates[0], 10);
            return;
        }
        if (coordinates.length > 1) {
            map.fitBounds(coordinates, { padding: [48, 48], maxZoom: 9 });
        }
    }, [coordinates, map]);

    return null;
};

export const MultiStopPlanner: React.FC = () => {
    const [multiStops, setMultiStops] = useState([{ destination: '', days: 2 }, { destination: '', days: 2 }]);
    const [multiBudget, setMultiBudget] = useState<number>(30000);
    const [multiSpecial, setMultiSpecial] = useState('');
    const [multiStopLoading, setMultiStopLoading] = useState(false);
    const [multiStopResult, setMultiStopResult] = useState<any>(null);
    const [expandedLegs, setExpandedLegs] = useState<Set<number>>(new Set([0]));
    const [isSaving, setIsSaving] = useState(false);
    const [isSaved, setIsSaved] = useState(false);

    const addStop = () => {
        if (multiStops.length < 6) {
            setMultiStops([...multiStops, { destination: '', days: 2 }]);
        }
    };

    const removeStop = (idx: number) => {
        if (multiStops.length > 2) {
            setMultiStops(multiStops.filter((_, i) => i !== idx));
        }
    };

    const updateStop = (idx: number, field: string, val: any) => {
        const updated = [...multiStops];
        updated[idx] = { ...updated[idx], [field]: val };
        setMultiStops(updated);
    };

    const handleMultiStopSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (multiStops.some(s => !s.destination.trim())) return;
        setMultiStopLoading(true);
        setMultiStopResult(null);
        setIsSaved(false);

        try {
            const res = await api.post('/api/ai/multistop-plan', {
                stops: multiStops,
                budget: multiBudget,
                special_requests: multiSpecial
            });
            setMultiStopResult(res.data);
            // Expand all legs by default on load
            const allIndexes = new Set(res.data.legs.map((_: any, i: number) => i));
            setExpandedLegs(allIndexes as Set<number>);
        } catch (error) {
            console.error('Failed to plan multi-stop journey:', error);
            alert('Failed to generate journey. Please try again.');
        } finally {
            setMultiStopLoading(false);
        }
    };

    const toggleLeg = (idx: number) => {
        const next = new Set(expandedLegs);
        if (next.has(idx)) next.delete(idx);
        else next.add(idx);
        setExpandedLegs(next);
    };

    const handlePrint = () => {
        window.print();
    };

    const handleSave = async () => {
        if (!multiStopResult) return;
        setIsSaving(true);
        try {
            await api.post('/api/trips/multistop/save', {
                trip_name: multiStopResult.trip_name,
                total_budget: multiStopResult.total_estimated_cost,
                total_days: multiStops.reduce((t, s) => t + s.days, 0),
                destinations_str: multiStops.map(s => s.destination).join(' → '),
                raw_json: multiStopResult
            });
            setIsSaved(true);
        } catch (err) {
            console.error('Failed to save trip:', err);
            alert('Failed to save trip. Please try again.');
        } finally {
            setIsSaving(false);
        }
    };

    // Helper to extract polyline coordinates
    const routeCoordinates: RouteCoordinate[] = (multiStopResult?.legs ?? [])
        .filter((leg: any) => Number.isFinite(leg.coordinates?.lat) && Number.isFinite(leg.coordinates?.lng))
        .map((leg: any) => [leg.coordinates.lat, leg.coordinates.lng]);

    return (
        <div className="max-w-6xl mx-auto flex flex-col gap-8 pb-10">

            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200 dark:border-slate-700/60 pb-6 print:hidden">
                <div>
                    <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
                        <span className="p-2.5 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400 rounded-2xl">
                            <MapIcon size={24} />
                        </span>
                        Multi-Stop Planner
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-2 max-w-2xl text-sm leading-relaxed">
                        Design a complex journey across multiple destinations. Our AI will optimize the budget, allocate days proportionally, and generate a continuous itinerary seamlessly linking each stop.
                    </p>
                </div>
            </div>

            <div className="flex flex-col xl:flex-row gap-8">

                {/* Left Column: Form */}
                <div className="w-full xl:w-[400px] shrink-0 print:hidden">
                    <form onSubmit={handleMultiStopSubmit} className="flex flex-col gap-5 bg-white dark:bg-slate-800 p-6 rounded-3xl border border-slate-200 dark:border-slate-700 shadow-sm sticky top-24">

                        {/* Dynamic Stop List */}
                        <div className="flex flex-col gap-3">
                            <div className="flex items-center justify-between">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Destinations ({multiStops.length}/6)</label>
                                <button
                                    type="button"
                                    onClick={addStop}
                                    disabled={multiStops.length >= 6}
                                    className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 hover:text-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                                >
                                    <Plus size={12} /> Add Stop
                                </button>
                            </div>

                            {/* Route preview chips */}
                            <div className="flex flex-wrap items-center gap-1 mb-1">
                                {multiStops.map((s, idx) => (
                                    <React.Fragment key={idx}>
                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-[10px] font-semibold border border-emerald-200 dark:border-emerald-800">
                                            <MapPin size={9} />
                                            {s.destination || `Stop ${idx + 1}`}
                                        </span>
                                        {idx < multiStops.length - 1 && (
                                            <span className="text-slate-300 dark:text-slate-600 text-xs">→</span>
                                        )}
                                    </React.Fragment>
                                ))}
                            </div>

                            {multiStops.map((stop, idx) => (
                                <div key={idx} className="flex items-center gap-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3">
                                    <div className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold shrink-0">
                                        {idx + 1}
                                    </div>
                                    <input
                                        type="text"
                                        required
                                        value={stop.destination}
                                        onChange={e => updateStop(idx, 'destination', e.target.value)}
                                        placeholder={`Destination ${idx + 1}`}
                                        className="flex-1 w-full min-w-0 bg-transparent text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none"
                                    />
                                    <div className="flex items-center gap-1 shrink-0">
                                        <input
                                            type="number"
                                            min={1}
                                            max={14}
                                            required
                                            value={stop.days}
                                            onChange={e => updateStop(idx, 'days', Math.max(1, Number(e.target.value)))}
                                            className="w-12 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg px-2 py-1 text-xs text-center text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                                        />
                                        <span className="text-[10px] text-slate-400">d</span>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => removeStop(idx)}
                                        disabled={multiStops.length <= 2}
                                        className="text-slate-300 dark:text-slate-600 hover:text-rose-500 dark:hover:text-rose-400 disabled:opacity-20 disabled:cursor-not-allowed transition-colors shrink-0"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            ))}
                        </div>

                        <hr className="border-slate-100 dark:border-slate-700/60 my-2" />

                        {/* Budget + Special */}
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Total Budget</label>
                                <div className="relative">
                                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm font-semibold">₹</span>
                                    <input
                                        type="number"
                                        required
                                        value={multiBudget}
                                        onChange={e => setMultiBudget(Number(e.target.value))}
                                        className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-7 pr-4 py-3 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 font-bold"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Total Days</label>
                                <div className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center">
                                    {multiStops.reduce((t, s) => t + s.days, 0)} Days
                                </div>
                            </div>
                        </div>

                        <div>
                            <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Special Requests / Dietary Needs</label>
                            <textarea
                                value={multiSpecial}
                                onChange={e => setMultiSpecial(e.target.value)}
                                placeholder="e.g. Vegetarian food, prefer trains, beachside."
                                rows={2}
                                className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 resize-none leading-relaxed"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={multiStopLoading}
                            className="w-full mt-2 inline-flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold py-3.5 rounded-xl text-sm transition-all shadow-md shadow-emerald-500/20"
                        >
                            {multiStopLoading ? <Loader size={18} className="animate-spin" /> : <MapPin size={16} />}
                            {multiStopLoading ? 'Generating Journey...' : 'Plan Multi-Stop Journey'}
                        </button>
                    </form>
                </div>

                {/* Right Column: Results & Map */}
                <div className="flex-1 w-full min-w-0">
                    {!multiStopResult && !multiStopLoading && (
                        <div className="flex flex-col items-center justify-center h-full py-20 px-6 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-3xl text-center print:hidden">
                            <div className="w-20 h-20 bg-slate-50 dark:bg-slate-800 rounded-full flex items-center justify-center mb-6 text-slate-300 dark:text-slate-600">
                                <MapIcon size={40} />
                            </div>
                            <h3 className="text-xl font-bold text-slate-700 dark:text-slate-200 mb-2">Ready to explore?</h3>
                            <p className="text-slate-400 max-w-sm text-sm leading-relaxed">
                                Add your destinations on the left, set your budget, and hit plan to generate an intelligent, connected itinerary.
                            </p>
                        </div>
                    )}

                    {multiStopLoading && (
                        <div className="flex flex-col items-center justify-center h-full py-32 text-center print:hidden">
                            <Loader size={48} className="animate-spin text-emerald-500 mb-6" />
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2 animate-pulse">Designing your route...</h3>
                            <p className="text-sm text-slate-500 dark:text-slate-400">Calculating travel times, optimizing budgets, and finding local highlights.</p>
                        </div>
                    )}

                    {multiStopResult && (
                        <div className="animate-fade-in w-full space-y-6">

                            {/* Grand Total Banner */}
                            <div className="bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-700 rounded-3xl p-6 md:p-8 text-white shadow-xl shadow-emerald-900/10 flex flex-col md:flex-row md:items-center justify-between gap-6 print:shadow-none print:text-black print:bg-none print:bg-white print:border-2 print:border-emerald-600">
                                <div>
                                    <p className="text-xs font-black uppercase tracking-widest opacity-80 mb-1.5 print:text-emerald-700">Multi-Destination Route</p>
                                    <h2 className="text-2xl md:text-3xl font-black leading-tight mb-4">{multiStopResult.trip_name}</h2>
                                    <div className="flex flex-wrap gap-2">
                                        {multiStopResult.legs?.map((leg: any, idx: number) => (
                                            <span key={idx} className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full bg-white/20 print:bg-emerald-100 font-bold print:text-emerald-900">
                                                <MapPin size={12} />{leg.destination} ({leg.days}d)
                                            </span>
                                        ))}
                                    </div>
                                </div>
                                <div className="md:text-right shrink-0 bg-white/10 print:bg-transparent print:border print:border-slate-200 px-6 py-4 rounded-2xl">
                                    <p className="text-[10px] font-bold uppercase tracking-wider opacity-80 mb-1 print:text-slate-500">Estimated Total</p>
                                    <p className="text-4xl font-black">₹{multiStopResult.total_estimated_cost?.toLocaleString()}</p>
                                </div>
                            </div>

                            {/* Action Bar */}
                            <div className="flex items-center justify-end gap-3 print:hidden">
                                <button
                                    onClick={handleSave}
                                    disabled={isSaving || isSaved}
                                    className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all shadow-sm ${isSaved
                                        ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300 pointer-events-none'
                                        : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'
                                        }`}
                                >
                                    {isSaving ? <Loader size={16} className="animate-spin" /> : isSaved ? <Check size={16} /> : <Save size={16} />}
                                    {isSaving ? 'Saving...' : isSaved ? 'Saved to Profile' : 'Save to My Trips'}
                                </button>
                                <button
                                    onClick={handlePrint}
                                    className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 dark:bg-slate-700 text-white text-sm font-bold hover:bg-slate-800 dark:hover:bg-slate-600 transition-colors shadow-sm"
                                >
                                    <Download size={16} /> Export PDF
                                </button>
                            </div>

                            {/* Interactive Route Map */}
                            {routeCoordinates && routeCoordinates.length > 0 && (
                                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-3xl overflow-hidden shadow-sm h-[350px] relative z-10 print:h-[400px]">
                                    <MapContainer
                                        center={routeCoordinates[0]}
                                        zoom={8}
                                        style={{ height: '100%', width: '100%' }}
                                        scrollWheelZoom={false}
                                    >
                                        <TileLayer
                                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                                            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                                        />
                                        <RouteBounds coordinates={routeCoordinates} />
                                        {multiStopResult.legs.map((leg: any, idx: number) => {
                                            if (!Number.isFinite(leg.coordinates?.lat) || !Number.isFinite(leg.coordinates?.lng)) return null;
                                            return (
                                                <Marker key={idx} position={[leg.coordinates.lat, leg.coordinates.lng]}>
                                                    <Popup className="font-sans">
                                                        <div className="text-center">
                                                            <p className="font-bold text-sm text-slate-900">{leg.destination}</p>
                                                            <p className="text-xs text-slate-500">Stop {idx + 1} ({leg.days} days)</p>
                                                        </div>
                                                    </Popup>
                                                </Marker>
                                            );
                                        })}
                                        {routeCoordinates.length > 1 && (
                                            <Polyline
                                                positions={routeCoordinates}
                                                pathOptions={{ color: '#059669', weight: 4, opacity: 0.7, dashArray: '8, 8' }}
                                            />
                                        )}
                                    </MapContainer>

                                    <div className="absolute top-4 left-4 z-[1000] bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm border border-slate-200 dark:border-slate-700 px-4 py-2 rounded-xl shadow-sm text-xs font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2 print:hidden">
                                        <MapIcon size={14} className="text-emerald-500" /> Map Route Validation
                                    </div>
                                </div>
                            )}

                            {/* Smart Packing List */}
                            {multiStopResult.packing_list && multiStopResult.packing_list.length > 0 && (
                                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-3xl p-6 shadow-sm">
                                    <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                                        <span className="text-violet-500">🎒</span> AI Smart Packing Checklist
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        {multiStopResult.packing_list.map((item: string, idx: number) => (
                                            <div key={idx} className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-100 dark:border-slate-700/50">
                                                <div className="w-5 h-5 rounded border-2 border-slate-300 dark:border-slate-600 flex-shrink-0 print:border-black" />
                                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{item}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Per-leg itinerary accordion */}
                            <div className="space-y-6">
                                {multiStopResult.legs?.map((leg: any, legIdx: number) => (
                                    <React.Fragment key={legIdx}>
                                        <div className="bg-white dark:bg-slate-800 border-2 border-slate-200 dark:border-slate-700 rounded-3xl overflow-hidden shadow-sm print:break-inside-avoid print:border-slate-300">
                                            {/* Leg header */}
                                            <button
                                                type="button"
                                                onClick={() => toggleLeg(legIdx)}
                                                className="w-full flex items-center justify-between px-6 py-5 text-left hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors print:pointer-events-none"
                                            >
                                                <div className="flex items-center gap-4">
                                                    <div className="w-10 h-10 rounded-2xl bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-sm font-black shrink-0 print:border print:border-emerald-200">
                                                        {legIdx + 1}
                                                    </div>
                                                    <div>
                                                        <p className="text-lg font-black text-slate-900 dark:text-white tracking-tight">{leg.destination}</p>
                                                        <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mt-1">{leg.days} day{leg.days !== 1 ? 's' : ''} · ₹{leg.estimated_cost?.toLocaleString()}</p>
                                                    </div>
                                                </div>
                                                <div className="print:hidden">
                                                    {expandedLegs.has(legIdx) ? <ChevronUp size={20} className="text-slate-400" /> : <ChevronDown size={20} className="text-slate-400" />}
                                                </div>
                                            </button>

                                            {/* Leg expanded body */}
                                            {(expandedLegs.has(legIdx) || window.matchMedia('print').matches) && (
                                                <div className="border-t border-slate-100 dark:border-slate-700/60 px-6 pb-6 pt-5 space-y-6">

                                                    {/* Best time tip */}
                                                    {leg.best_time_tip && (
                                                        <div className="flex items-start gap-3 bg-amber-50 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/30 rounded-2xl p-4">
                                                            <span className="text-amber-500 text-lg shrink-0">💡</span>
                                                            <p className="text-xs text-amber-900 dark:text-amber-200 leading-relaxed font-medium">{leg.best_time_tip}</p>
                                                        </div>
                                                    )}

                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                        {/* Highlights */}
                                                        {leg.highlights?.length > 0 && (
                                                            <div>
                                                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Must-See Highlights</p>
                                                                <div className="flex flex-wrap gap-2">
                                                                    {leg.highlights.map((h: string, hIdx: number) => (
                                                                        <span key={hIdx} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-violet-50 dark:bg-violet-900/20 border border-violet-100 dark:border-violet-800/30 text-xs font-bold text-violet-700 dark:text-violet-300">
                                                                            ✦ {h}
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        )}

                                                        {/* Must-try food */}
                                                        {leg.must_try_food?.length > 0 && (
                                                            <div>
                                                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Must-Try Food</p>
                                                                <div className="flex flex-wrap gap-2">
                                                                    {leg.must_try_food.map((f: string, fIdx: number) => (
                                                                        <span key={fIdx} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-orange-50 dark:bg-orange-900/20 border border-orange-100 dark:border-orange-800/30 text-xs font-bold text-orange-700 dark:text-orange-300">
                                                                            🍽 {f}
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>

                                                    <hr className="border-slate-100 dark:border-slate-700/60 !my-6" />

                                                    {/* Day-by-day itinerary */}
                                                    <div>
                                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Daily Itinerary</p>
                                                        <div className="space-y-4">
                                                            {leg.itinerary?.map((day: any) => (
                                                                <div key={day.day_number} className="bg-slate-50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-700/50 rounded-2xl overflow-hidden print:border-slate-300">
                                                                    {/* Day header */}
                                                                    <div className="bg-slate-100 dark:bg-slate-800/80 px-5 py-3 flex flex-col md:flex-row md:items-center gap-2 print:bg-slate-100">
                                                                        <span className="text-xs font-black text-slate-800 dark:text-white uppercase tracking-wider shrink-0 bg-white dark:bg-slate-700 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-600 print:border-black">
                                                                            Day {day.day_number}
                                                                        </span>
                                                                        <span className="text-xs font-bold text-slate-600 dark:text-slate-300">{day.description}</span>
                                                                    </div>
                                                                    <div className="divide-y divide-slate-100 dark:divide-slate-700/50">
                                                                        {day.activities?.map((act: any, aIdx: number) => (
                                                                            <div key={aIdx} className="px-5 py-4">
                                                                                <div className="flex justify-between items-start">
                                                                                    <div className="flex gap-4 min-w-0">
                                                                                        <span className="text-[10px] font-black uppercase tracking-wider text-emerald-600 dark:text-emerald-400 w-16 shrink-0 pt-0.5">{act.time}</span>
                                                                                        <div>
                                                                                            <span className="text-sm font-bold text-slate-900 dark:text-slate-100">{act.title}</span>
                                                                                            {act.notes && (
                                                                                                <p className="text-xs text-slate-500 dark:text-slate-400 font-medium leading-relaxed mt-1.5">{act.notes}</p>
                                                                                            )}
                                                                                        </div>
                                                                                    </div>
                                                                                    <span className="text-xs font-black text-slate-400 dark:text-slate-500 shrink-0 ml-4 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-lg">
                                                                                        {act.cost > 0 ? `₹${Number(act.cost).toLocaleString()}` : 'Free'}
                                                                                    </span>
                                                                                </div>
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

                                        {/* Transit bridge to next stop */}
                                        {leg.travel_to_next && legIdx < multiStopResult.legs.length - 1 && (
                                            <div className="flex items-center gap-4 px-6 py-2 print:break-inside-avoid">
                                                <div className="flex-1 h-0.5 border-t-2 border-dashed border-slate-200 dark:border-slate-700" />
                                                <div className="flex items-center gap-2.5 bg-slate-100 dark:bg-slate-800 border-2 border-slate-200 dark:border-slate-700 rounded-full px-5 py-2 shrink-0 shadow-sm print:border-slate-300">
                                                    <span className="text-sm">{leg.travel_to_next.mode === 'Flight' ? '✈️' : leg.travel_to_next.mode === 'Train' ? '🚆' : leg.travel_to_next.mode === 'Bus' ? '🚌' : '🚗'}</span>
                                                    <span className="text-xs font-black text-slate-700 dark:text-slate-200 uppercase tracking-widest">{leg.travel_to_next.mode}</span>
                                                    <span className="text-xs text-slate-300 dark:text-slate-600">|</span>
                                                    <span className="text-xs font-bold text-slate-500 dark:text-slate-400">{leg.travel_to_next.duration}</span>
                                                    {leg.travel_to_next.approx_cost > 0 && (
                                                        <><span className="text-xs text-slate-300 dark:text-slate-600">|</span>
                                                            <span className="text-xs font-black text-emerald-600 dark:text-emerald-400">~₹{Number(leg.travel_to_next.approx_cost).toLocaleString()}</span></>
                                                    )}
                                                </div>
                                                <div className="flex-1 h-0.5 border-t-2 border-dashed border-slate-200 dark:border-slate-700" />
                                            </div>
                                        )}
                                    </React.Fragment>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Dynamic print styles injected for PDF export */}
            <style>{`
        @media print {
          @page { size: landscape; margin: 1cm; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; background-color: white !important; }
          /* Hide app sidebar/header */
          header, aside, .sidebar-overlay { display: none !important; }
          main { margin: 0 !important; padding: 0 !important; }
        }
      `}</style>
        </div>
    );
};
