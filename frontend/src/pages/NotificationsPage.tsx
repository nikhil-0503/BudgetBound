import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { EmptyState, SkeletonList } from '../components/FeedbackStates';
import { 
  Bell, 
  Check, 
  Trash2, 
  Calendar, 
  AlertTriangle, 
  Package, 
  Share2, 
  FileText, 
  CheckCircle,
  Loader,
  Clock
} from 'lucide-react';

interface Notification {
  id: number;
  type: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [actioning, setActioning] = useState(false);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/notifications');
      setNotifications(response.data);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkRead = async (id: number) => {
    try {
      const response = await api.put(`/api/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? response.data : n));
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      setActioning(true);
      await api.post('/api/notifications/mark-all-read');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (err) {
      console.error(err);
    } finally {
      setActioning(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/api/notifications/${id}`);
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'Upcoming Trip':
      case 'Trip Reminder':
        return <Calendar className="text-sky-500" size={18} />;
      case 'Budget Warning':
      case 'Overspending Alert':
        return <AlertTriangle className="text-amber-500" size={18} />;
      case 'Packing Reminder':
        return <Package className="text-marigold-500" size={18} />;
      case 'Checklist Completed':
        return <CheckCircle className="text-emerald-500" size={18} />;
      case 'Trip Shared Successfully':
        return <Share2 className="text-petrol-500" size={18} />;
      case 'Trip Exported':
        return <FileText className="text-teal-500" size={18} />;
      default:
        return <Bell className="text-paper-400" size={18} />;
    }
  };

  const getNotificationColorClass = (type: string) => {
    switch (type) {
      case 'Overspending Alert':
        return 'border-rose-100 dark:border-rose-900/10 bg-rose-50/20 dark:bg-rose-950/5';
      case 'Budget Warning':
        return 'border-amber-100 dark:border-amber-900/10 bg-amber-50/15 dark:bg-amber-950/5';
      case 'Checklist Completed':
        return 'border-emerald-100 dark:border-emerald-900/10 bg-emerald-50/10 dark:bg-emerald-950/5';
      default:
        return 'border-paper-100 dark:border-paper-800 bg-paper-50 dark:bg-paper-800';
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="max-w-3xl mx-auto space-y-6"
    >
      
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-paper-50 dark:bg-paper-800 border border-paper-200 dark:border-paper-700 p-6 rounded-2xl shadow-sm">
        <div>
          <h2 className="text-xl font-extrabold text-paper-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
            <Bell size={20} className="text-marigold-500" />
            BudgetBound Notification Center
          </h2>
          <p className="text-[11px] text-paper-400 mt-0.5">
            Stay updated with your travel reminders, checklists, and expenditure warnings
          </p>
        </div>

        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllRead}
            disabled={actioning}
            className="bg-marigold-600 hover:bg-marigold-500 text-white font-extrabold text-[10px] px-4.5 py-2.5 rounded-xl uppercase transition-all shadow-md flex items-center gap-1.5 shrink-0"
          >
            {actioning ? <Loader size={12} className="animate-spin" /> : <Check size={12} />}
            Mark All Read
          </button>
        )}
      </div>

      {/* Notifications list */}
      {loading && notifications.length === 0 ? (
        <SkeletonList />
      ) : notifications.length === 0 ? (
        <EmptyState
          icon={<Bell size={24} />}
          title="No Notifications"
          description="You are all caught up! There are no system alerts, checklist reminders, or overspending warnings."
          actionLabel="Refresh Notifications"
          onAction={fetchNotifications}
        />
      ) : (
        <div className="space-y-3.5">
          <AnimatePresence initial={false}>
            {notifications.map((notif) => (
              <motion.div 
                key={notif.id}
                initial={{ opacity: 0, height: 0, overflow: 'hidden' }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className={`border p-4.5 rounded-2xl flex items-start gap-4 transition-all ${
                  notif.is_read 
                    ? 'bg-paper-50/50 dark:bg-paper-900/10 border-paper-200 dark:border-paper-800 text-paper-500 dark:text-paper-400' 
                    : 'shadow-sm text-paper-800 dark:text-paper-300 font-medium'
                } ${getNotificationColorClass(notif.type)}`}
              >
                {/* Category indicator icon */}
                <div className="h-9 w-9 rounded-xl bg-paper-50 dark:bg-paper-800 border border-paper-100 dark:border-paper-700/60 shadow-sm flex items-center justify-center shrink-0">
                  {getNotificationIcon(notif.type)}
                </div>

                {/* Message text content */}
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex justify-between items-start gap-2">
                    <span className="text-xs font-extrabold uppercase text-[9px] tracking-wide text-paper-400 block">
                      {notif.type}
                    </span>
                    
                    {/* Unread circle badge */}
                    {!notif.is_read && (
                      <span className="h-2 w-2 rounded-full bg-rose-500 mt-1 animate-pulse" />
                    )}
                  </div>
                  
                  <p className="text-xs leading-relaxed">{notif.message}</p>
                  
                  <div className="flex items-center gap-1 text-[10px] text-paper-400 pt-1 font-semibold">
                    <Clock size={10} />
                    <span>{new Date(notif.created_at).toLocaleDateString()}</span>
                    <span>{new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex items-center gap-1.5 shrink-0 self-center">
                  {!notif.is_read && (
                    <button
                      onClick={() => handleMarkRead(notif.id)}
                      className="p-1.5 bg-paper-50 dark:bg-paper-700/60 hover:bg-paper-100 dark:hover:bg-paper-700 rounded-lg text-paper-500 dark:text-paper-400 transition-colors"
                      title="Mark Read"
                    >
                      <Check size={13} />
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(notif.id)}
                    className="p-1.5 bg-rose-50 dark:bg-rose-950/20 hover:bg-rose-100 rounded-lg text-rose-600 dark:text-rose-400 transition-colors"
                    title="Delete Alert"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );
};



