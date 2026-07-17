import React from 'react';
import { 
  Plane, 
  Building, 
  Utensils, 
  Camera, 
  Clock, 
  Compass, 
  ChevronDown, 
  ChevronUp,
  MapPin,
  Car
} from 'lucide-react';

interface Activity {
  time: string;
  title: string;
  cost: number;
  duration?: string;
  category?: string;
}

interface ItineraryDay {
  day_number: number;
  description?: string;
  activities: Activity[];
}

interface TimelineItineraryProps {
  itineraries: ItineraryDay[];
  expandedDays: Record<number, boolean>;
  toggleDay: (dayNumber: number) => void;
  className?: string;
}

export const TimelineItinerary: React.FC<TimelineItineraryProps> = ({
  itineraries,
  expandedDays,
  toggleDay,
  className = '',
}) => {

  const getCategoryIcon = (category?: string, title: string = '') => {
    const term = (category || title).toLowerCase();
    if (term.includes('hotel') || term.includes('stay') || term.includes('check-in') || term.includes('accommodation')) {
      return { icon: <Building size={14} />, bg: 'bg-amber-100 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400' };
    }
    if (term.includes('lunch') || term.includes('dinner') || term.includes('food') || term.includes('breakfast') || term.includes('eat') || term.includes('restaurant')) {
      return { icon: <Utensils size={14} />, bg: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400' };
    }
    if (term.includes('flight') || term.includes('train') || term.includes('arrival') || term.includes('departure') || term.includes('travel') || term.includes('cab')) {
      return { icon: <Plane size={14} />, bg: 'bg-blue-100 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400' };
    }
    return { icon: <Camera size={14} />, bg: 'bg-violet-100 text-violet-600 dark:bg-violet-950/40 dark:text-violet-400' };
  };

  const formatActivityTime = (timeStr: string) => {
    if (timeStr === 'Morning') return '08:00';
    if (timeStr === 'Afternoon') return '13:00';
    if (timeStr === 'Evening') return '17:00';
    if (timeStr === 'Night') return '20:00';
    return timeStr;
  };

  return (
    <div className={`space-y-4 w-full ${className}`}>
      {itineraries.map((day) => {
        const isOpen = !!expandedDays[day.day_number];
        return (
          <div 
            key={day.day_number} 
            className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl overflow-hidden shadow-sm transition-all hover:shadow"
          >
            {/* Header Accordion Button */}
            <button
              type="button"
              onClick={() => toggleDay(day.day_number)}
              className="w-full flex items-center justify-between p-4 bg-slate-50/50 dark:bg-slate-900/10 text-left font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-300 focus:outline-none"
            >
              <div className="flex items-center gap-2">
                <span className="h-6 w-6 rounded-lg bg-violet-100 dark:bg-violet-950/50 text-violet-600 dark:text-violet-400 flex items-center justify-center font-extrabold text-[10px]">
                  {day.day_number}
                </span>
                <span>Day {day.day_number} Timeline</span>
              </div>
              {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>

            {/* Expanded Day Details */}
            {isOpen && (
              <div className="p-5 border-t border-slate-100 dark:border-slate-700/60 flex flex-col gap-4">
                {day.description && (
                  <p className="text-slate-500 dark:text-slate-400 text-xs italic leading-relaxed border-l-2 border-violet-400 pl-3">
                    {day.description}
                  </p>
                )}

                {/* Vertical Timeline Thread */}
                <div className="relative pl-6 space-y-6 mt-2">
                  {/* Vertical Connection Line */}
                  <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-slate-200 dark:bg-slate-700" />

                  {day.activities.map((act, actIdx) => {
                    const formattedTime = formatActivityTime(act.time);
                    const { icon, bg } = getCategoryIcon(act.category, act.title);
                    const duration = act.duration || "2.0h";
                    const costStr = act.cost > 0 ? `₹${act.cost.toLocaleString()}` : 'Included / Free';

                    return (
                      <div key={actIdx} className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs group">
                        
                        {/* Timeline Node Point */}
                        <div className={`absolute -left-6 transform -translate-x-[1px] h-6.5 w-6.5 rounded-full ${bg} flex items-center justify-center border-4 border-white dark:border-slate-800 shadow-sm shrink-0 z-10`}>
                          {icon}
                        </div>

                        {/* Title & Timing Info */}
                        <div className="flex flex-col gap-1 sm:max-w-[70%]">
                          <div className="flex items-center gap-2">
                            <span className="font-extrabold text-[10px] tracking-wider text-slate-400 dark:text-slate-500 flex items-center gap-1 uppercase">
                              <Clock size={11} />
                              {formattedTime}
                            </span>
                            <span className="text-[9px] font-bold px-1.5 py-0.2 bg-slate-100 dark:bg-slate-900 text-slate-500 dark:text-slate-400 rounded">
                              {duration}
                            </span>
                          </div>
                          <span className="text-slate-800 dark:text-white font-bold leading-normal text-xs group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
                            {act.title}
                          </span>
                        </div>

                        {/* Budget Tag info */}
                        <div className="self-start sm:self-center font-bold text-[10px] bg-slate-50 dark:bg-slate-900 border border-slate-150 dark:border-slate-800 text-slate-600 dark:text-slate-400 px-3 py-1 rounded-xl whitespace-nowrap">
                          {costStr}
                        </div>

                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
