import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { 
  CheckSquare, 
  Square, 
  Plus, 
  Trash2, 
  Loader, 
  CheckCircle2, 
  AlertCircle,
  Package
} from 'lucide-react';

interface PackingItem {
  id: number;
  trip_id: number;
  name: string;
  checked: boolean;
}

interface TripChecklistProps {
  tripId: number;
  readOnly?: boolean;
  initialItems?: PackingItem[];
  onChange?: () => void;
}

export const TripChecklist: React.FC<TripChecklistProps> = ({
  tripId,
  readOnly = false,
  initialItems,
  onChange
}) => {
  const [items, setItems] = useState<PackingItem[]>(initialItems || []);
  const [loading, setLoading] = useState(false);
  const [newItemName, setNewItemName] = useState('');
  const [adding, setAdding] = useState(false);

  const fetchChecklist = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/trips/${tripId}/checklist`);
      setItems(response.data);
    } catch (err) {
      console.error('Failed to fetch checklist:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!initialItems) {
      fetchChecklist();
    } else {
      setItems(initialItems);
    }
  }, [tripId, initialItems]);

  const handleToggle = async (item: PackingItem) => {
    if (readOnly) return;
    const nextChecked = !item.checked;
    
    // Optimistic update
    setItems(prev => prev.map(i => i.id === item.id ? { ...i, checked: nextChecked } : i));
    
    try {
      await api.put(`/api/trips/${tripId}/checklist/${item.id}`, {
        checked: nextChecked
      });
      if (onChange) onChange();
    } catch (err) {
      console.error(err);
      // Revert on error
      setItems(prev => prev.map(i => i.id === item.id ? { ...i, checked: !nextChecked } : i));
      alert('Failed to save checklist state.');
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newItemName.trim() || readOnly) return;
    
    try {
      setAdding(true);
      const response = await api.post(`/api/trips/${tripId}/checklist`, {
        name: newItemName.trim()
      });
      setItems(prev => [...prev, response.data]);
      setNewItemName('');
      if (onChange) onChange();
    } catch (err) {
      console.error(err);
      alert('Failed to add checklist item.');
    } finally {
      setAdding(false);
    }
  };

  const handleDeleteItem = async (itemId: number) => {
    if (readOnly) return;
    try {
      await api.delete(`/api/trips/${tripId}/checklist/${itemId}`);
      setItems(prev => prev.filter(i => i.id !== itemId));
      if (onChange) onChange();
    } catch (err) {
      console.error(err);
      alert('Failed to delete checklist item.');
    }
  };

  // Completion calculation
  const totalCount = items.length;
  const packedCount = items.filter(i => i.checked).length;
  const percentage = totalCount > 0 ? Math.round((packedCount / totalCount) * 100) : 0;

  if (loading && items.length === 0) {
    return (
      <div className="flex items-center justify-center p-6 text-paper-400 gap-2 text-xs">
        <Loader size={14} className="animate-spin text-marigold-500" />
        <span>Loading packing checklist...</span>
      </div>
    );
  }

  return (
    <div className="bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 rounded-2xl p-5 shadow-sm space-y-4">
      {/* Title */}
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-extrabold text-paper-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
          <Package size={16} className="text-marigold-500" />
          Smart Packing Checklist
        </h3>
        <span className="text-[10px] font-bold text-paper-400">
          {packedCount}/{totalCount} Items Packed
        </span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-[10px] font-extrabold text-paper-500 uppercase">
          <span>Packing Progress</span>
          <span className={percentage === 100 ? "text-emerald-500" : ""}>{percentage}% Complete</span>
        </div>
        <div className="h-2 w-full bg-paper-100 dark:bg-paper-900 rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full transition-all duration-500 ${percentage === 100 ? 'bg-emerald-500' : 'bg-marigold-600'}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Checklist items */}
      {items.length === 0 ? (
        <div className="text-center py-6 text-paper-400 text-xs italic">
          No packing items yet. Add custom ones below.
        </div>
      ) : (
        <div className="max-h-64 overflow-y-auto pr-1 space-y-2.5">
          {items.map((item) => (
            <div 
              key={item.id} 
              className={`flex items-center justify-between gap-3 text-xs p-2 rounded-xl border transition-all ${
                item.checked 
                  ? 'bg-paper-50/50 dark:bg-paper-900/10 border-paper-200 dark:border-paper-800 text-paper-400' 
                  : 'bg-paper-50 dark:bg-paper-800 border-paper-100 dark:border-paper-700/60 text-paper-700 dark:text-paper-200'
              }`}
            >
              <button
                type="button"
                disabled={readOnly}
                onClick={() => handleToggle(item)}
                className={`flex items-start gap-2.5 text-left font-medium transition-colors ${readOnly ? 'cursor-default' : 'hover:text-marigold-600'}`}
              >
                <span className="shrink-0 mt-0.5 text-marigold-500">
                  {item.checked ? <CheckSquare size={16} fill="currentColor" className="text-white dark:text-paper-800" /> : <Square size={16} />}
                </span>
                <span className={item.checked ? 'line-through' : ''}>
                  {item.name}
                </span>
              </button>

              {!readOnly && (
                <button
                  type="button"
                  onClick={() => handleDeleteItem(item.id)}
                  className="text-paper-500 hover:text-rose-500 transition-colors p-1"
                  title="Delete item"
                >
                  <Trash2 size={13} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add Custom Item */}
      {!readOnly && (
        <form onSubmit={handleAddItem} className="flex gap-2 pt-2 border-t border-paper-100 dark:border-paper-700/60">
          <input
            type="text"
            placeholder="Add custom packing item..."
            value={newItemName}
            onChange={(e) => setNewItemName(e.target.value)}
            disabled={adding}
            className="flex-1 px-3 py-2 border border-paper-200 dark:border-paper-700 rounded-xl text-xs bg-paper-50 dark:bg-paper-900 focus:outline-none focus:border-marigold-500 dark:text-white"
          />
          <button
            type="submit"
            disabled={adding || !newItemName.trim()}
            className="bg-marigold-600 hover:bg-marigold-500 text-white font-bold p-2.5 rounded-xl transition-all disabled:opacity-50 shrink-0"
          >
            {adding ? <Loader size={14} className="animate-spin" /> : <Plus size={14} />}
          </button>
        </form>
      )}
    </div>
  );
};



