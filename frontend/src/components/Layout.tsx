import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import api from '../services/api';
import {
  LayoutDashboard,
  Compass,
  Map,
  MapPin,
  Sparkles,
  LogOut,
  Menu,
  X,
  Sun,
  Moon,
  User,
  Wallet,
  Briefcase,
  GitCompare,
  Bell,
  Settings,
  ShieldAlert
} from 'lucide-react';

interface SidebarLinkProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick?: () => void;
  badgeCount?: number;
}

const SidebarLink: React.FC<SidebarLinkProps> = ({ to, icon, label, active, onClick, badgeCount }) => {
  return (
    <Link
      to={to}
      onClick={onClick}
      className={`flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-200 ${active
          ? 'bg-violet-600 text-white shadow-md shadow-violet-500/20'
          : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
        }`}
    >
      <div className="flex items-center gap-3">
        {icon}
        <span className="font-medium text-sm">{label}</span>
      </div>
      {badgeCount !== undefined && badgeCount > 0 && (
        <span className="h-5 min-w-5 px-1.5 rounded-full bg-rose-500 text-white text-[10px] font-extrabold flex items-center justify-center animate-pulse">
          {badgeCount}
        </span>
      )}
    </Link>
  );
};

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const { darkMode, toggleTheme } = useTheme();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchUnreadCount = async () => {
    try {
      const response = await api.get('/api/notifications/unread-count');
      setUnreadCount(response.data.unread_count);
    } catch (err) {
      console.error('Failed to fetch unread count:', err);
    }
  };

  // FIX #1: Reset scroll position when route changes (location.pathname)
  useEffect(() => {
    // Find and scroll the main scrollable container to top
    const mainElement = document.querySelector('main');
    if (mainElement) {
      mainElement.scrollTop = 0;
    }
  }, [location.pathname]); // Trigger only when pathname changes, not on every location update

  useEffect(() => {
    if (user) {
      fetchUnreadCount();
      const interval = setInterval(fetchUnreadCount, 30000); // Poll every 30s
      return () => clearInterval(interval);
    }
  }, [user, location]);

  const handleLogout = () => {
    logout();
  };

  // Determine user avatar image
  const renderAvatar = () => {
    if (user?.photo_url) {
      return (
        <img
          src={user.photo_url}
          alt="Avatar"
          className="h-10 w-10 rounded-full object-cover border border-violet-200"
          onError={(e) => {
            // fallback if URL fails
            (e.target as HTMLImageElement).src = '';
            (e.target as HTMLImageElement).style.display = 'none';
          }}
        />
      );
    }
    return (
      <div className="h-10 w-10 rounded-full bg-violet-100 dark:bg-violet-950 flex items-center justify-center text-violet-700 dark:text-violet-300 font-extrabold uppercase text-sm">
        {user?.name ? user.name[0] : 'T'}
      </div>
    );
  };

  const navLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { to: '/planner', label: 'Trip Flow', icon: <Compass size={20} /> },
    { to: '/my-trips', label: 'Saved Trips', icon: <Briefcase size={20} /> },
    { to: '/compare', label: 'Compare', icon: <GitCompare size={20} /> },
    { to: '/explorer', label: 'Destination Explorer', icon: <Map size={20} /> },
    { to: '/ai-companion', label: 'AI Companion', icon: <Sparkles size={20} /> },
    { to: '/multi-stop', label: 'Multi-Stop Planner', icon: <MapPin size={20} /> },
    { to: '/notifications', label: 'Notifications', icon: <Bell size={20} />, badgeCount: unreadCount },
    { to: '/profile', label: 'Preferences', icon: <Settings size={20} /> },
  ];

  // If user is admin, append Admin Analytics link
  if (user?.is_admin) {
    navLinks.push({ to: '/admin', label: 'Admin Analytics', icon: <ShieldAlert size={20} /> });
  }

  // Skip Layout rendering for public shared trip views
  if (location.pathname.startsWith('/share/')) {
    return <>{children}</>;
  }

  return (
    <div className="h-screen overflow-hidden bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 flex flex-col md:flex-row transition-colors duration-200">

      {/* Mobile Header */}
      <header className="md:hidden flex items-center justify-between px-6 py-4 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 shadow-sm sticky top-0 z-50">
        <Link to="/" className="flex items-center gap-2">
          <Wallet className="h-6 w-6 text-violet-600" />
          <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-violet-600 to-indigo-600 bg-clip-text text-transparent">
            BudgetBound
          </span>
        </Link>
        <div className="flex items-center gap-4">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
          >
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </header>

      {/* Sidebar Navigation */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 h-full bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col justify-between p-6 transform transition-transform duration-300 ease-in-out md:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        <div className="flex flex-col gap-8 overflow-y-auto max-h-[80%] pr-1">
          {/* Logo */}
          <div className="hidden md:flex items-center gap-2">
            <Wallet className="h-7 w-7 text-violet-600" />
            <span className="font-bold text-2xl tracking-tight bg-gradient-to-r from-violet-600 to-indigo-600 bg-clip-text text-transparent">
              BudgetBound
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="flex flex-col gap-2">
            {navLinks.map((link) => (
              <SidebarLink
                key={link.to}
                to={link.to}
                icon={link.icon}
                label={link.label}
                active={location.pathname.startsWith(link.to)}
                badgeCount={(link as any).badgeCount}
                onClick={() => setSidebarOpen(false)}
              />
            ))}
          </nav>
        </div>

        {/* User profile & Actions */}
        <div className="flex flex-col gap-4 border-t border-slate-200 dark:border-slate-700 pt-6 mt-auto">
          <div className="flex items-center gap-3">
            {renderAvatar()}
            <div className="flex flex-col min-w-0">
              <span className="font-semibold text-sm truncate">{user?.name || 'Traveler'}</span>
              <span className="text-xs text-slate-500 dark:text-slate-400 truncate">{user?.email}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 justify-between">
            <button
              onClick={toggleTheme}
              className="flex-1 p-2 rounded-lg bg-slate-100 dark:bg-slate-700/50 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 flex items-center justify-center gap-2 text-xs font-medium transition-all"
            >
              {darkMode ? (
                <>
                  <Sun size={14} /> Light Mode
                </>
              ) : (
                <>
                  <Moon size={14} /> Dark Mode
                </>
              )}
            </button>

            <button
              onClick={handleLogout}
              className="p-2 rounded-lg bg-rose-50 dark:bg-rose-950/20 text-rose-600 hover:bg-rose-100 dark:hover:bg-rose-900/30 flex items-center justify-center text-xs font-medium transition-all"
              title="Logout"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden p-6 md:p-10 md:ml-64 w-full">
        {/* Overlay for mobile sidebar */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-30 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
        {children}
      </main>
    </div>
  );
};
