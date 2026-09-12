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
      className={`flex items-center justify-between px-4 py-2.5 rounded-lg transition-all duration-150 border-l-2 ${active
          ? 'bg-marigold-500/10 border-marigold-500 text-ink-900 dark:text-paper-50 font-semibold'
          : 'border-transparent text-paper-600 dark:text-paper-400 hover:bg-paper-200/60 dark:hover:bg-ink-800 hover:border-paper-400 dark:hover:border-ink-500'
        }`}
    >
      <div className="flex items-center gap-3">
        <span className={active ? 'text-marigold-600 dark:text-marigold-400' : ''}>{icon}</span>
        <span className="text-sm">{label}</span>
      </div>
      {badgeCount !== undefined && badgeCount > 0 && (
        <span className="h-5 min-w-5 px-1.5 rounded-full bg-berry-600 text-white text-[10px] font-num font-semibold flex items-center justify-center">
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

  const renderAvatar = () => {
    if (user?.photo_url) {
      return (
        <img
          src={user.photo_url}
          alt="Avatar"
          className="h-10 w-10 rounded-full object-cover border border-marigold-300"
          onError={(e) => {
            (e.target as HTMLImageElement).src = '';
            (e.target as HTMLImageElement).style.display = 'none';
          }}
        />
      );
    }
    return (
      <div className="h-10 w-10 rounded-full bg-marigold-100 dark:bg-marigold-950 flex items-center justify-center text-marigold-700 dark:text-marigold-300 font-display font-semibold uppercase text-sm">
        {user?.name ? user.name[0] : 'T'}
      </div>
    );
  };

  const navLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard size={19} /> },
    { to: '/planner', label: 'Trip Flow', icon: <Compass size={19} /> },
    { to: '/my-trips', label: 'Saved Trips', icon: <Briefcase size={19} /> },
    { to: '/compare', label: 'Compare', icon: <GitCompare size={19} /> },
    { to: '/explorer', label: 'Destination Explorer', icon: <Map size={19} /> },
    { to: '/ai-companion', label: 'AI Companion', icon: <Sparkles size={19} /> },
    { to: '/multi-stop', label: 'Multi-Stop Planner', icon: <MapPin size={19} /> },
    { to: '/notifications', label: 'Notifications', icon: <Bell size={19} />, badgeCount: unreadCount },
    { to: '/profile', label: 'Preferences', icon: <Settings size={19} /> },
  ];

  if (user?.is_admin) {
    navLinks.push({ to: '/admin', label: 'Admin Analytics', icon: <ShieldAlert size={19} /> });
  }

  if (location.pathname.startsWith('/share/')) {
    return <>{children}</>;
  }

  return (
    <div className="h-screen overflow-hidden bg-paper-100 dark:bg-ink-950 text-ink-900 dark:text-paper-100 flex flex-col md:flex-row transition-colors duration-200">

      {/* Mobile Header */}
      <header className="md:hidden flex items-center justify-between px-6 py-4 bg-paper-50 dark:bg-ink-900 border-b border-paper-300 dark:border-ink-700 sticky top-0 z-50">
        <Link to="/" className="flex items-center gap-2">
          <Wallet className="h-6 w-6 text-marigold-600" />
          <span className="font-display font-semibold text-xl tracking-tight text-ink-900 dark:text-paper-50">
            BudgetBound
          </span>
        </Link>
        <div className="flex items-center gap-4">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg bg-paper-200 dark:bg-ink-700 text-paper-700 dark:text-paper-300 hover:bg-paper-300"
          >
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg text-paper-700 dark:text-paper-300 hover:bg-paper-200 dark:hover:bg-ink-700"
          >
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </header>

      {/* Sidebar Navigation — styled as a boarding-pass stub */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 h-full bg-paper-50 dark:bg-ink-900 border-r border-dashed border-paper-400 dark:border-ink-600 flex flex-col justify-between p-6 transform transition-transform duration-300 ease-in-out md:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        <div className="flex flex-col gap-7 overflow-y-auto max-h-[80%] pr-1 no-scrollbar">
          {/* Logo */}
          <div className="hidden md:flex items-center gap-2">
            <Wallet className="h-7 w-7 text-marigold-600" />
            <span className="font-display font-semibold text-2xl tracking-tight text-ink-900 dark:text-paper-50">
              BudgetBound
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="flex flex-col gap-1">
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

        {/* Perforated tear-line before the account stub */}
        <div className="flex flex-col gap-4 mt-auto pt-6">
          <div className="ticket-perforation !mx-0" />
          <div className="flex items-center gap-3 pt-2">
            {renderAvatar()}
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-semibold truncate">{user?.name || 'Traveler'}</span>
              <span className="text-xs text-paper-500 dark:text-paper-400 truncate font-num">{user?.email}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 justify-between">
            <button
              onClick={toggleTheme}
              className="flex-1 p-2 rounded-lg bg-paper-200/70 dark:bg-ink-800 text-paper-700 dark:text-paper-300 hover:bg-paper-300 dark:hover:bg-ink-700 flex items-center justify-center gap-2 text-xs font-medium transition-all"
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
              className="p-2 rounded-lg bg-berry-50 dark:bg-berry-950/30 text-berry-700 dark:text-berry-400 hover:bg-berry-100 dark:hover:bg-berry-900/30 flex items-center justify-center text-xs font-medium transition-all"
              title="Logout"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden p-6 md:p-10 md:ml-64 w-full">
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-ink-950/50 backdrop-blur-sm z-30 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
        {children}
      </main>
    </div>
  );
};
