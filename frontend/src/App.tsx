import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { Loader } from 'lucide-react';

// Dynamic lazy page imports for optimized code-splitting (Phase 4 Performance)
const LandingPage = lazy(() => import('./pages/LandingPage').then(m => ({ default: m.LandingPage })));
const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })));
const Register = lazy(() => import('./pages/Register').then(m => ({ default: m.Register })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const BudgetPlanner = lazy(() => import('./pages/BudgetPlanner').then(m => ({ default: m.BudgetPlanner })));
const DestinationExplorer = lazy(() => import('./pages/DestinationExplorer').then(m => ({ default: m.DestinationExplorer })));
const DestinationDetail = lazy(() => import('./pages/DestinationDetail').then(m => ({ default: m.DestinationDetail })));
const BudgetOptimizer = lazy(() => import('./pages/BudgetOptimizer').then(m => ({ default: m.BudgetOptimizer })));
const ExpenseTracker = lazy(() => import('./pages/ExpenseTracker').then(m => ({ default: m.ExpenseTracker })));
const AICompanion = lazy(() => import('./pages/AICompanion').then(m => ({ default: m.AICompanion })));
const SavedTrips = lazy(() => import('./pages/SavedTrips').then(m => ({ default: m.SavedTrips })));
const CompareDestinations = lazy(() => import('./pages/CompareDestinations').then(m => ({ default: m.CompareDestinations })));
const SharedTripView = lazy(() => import('./pages/SharedTripView').then(m => ({ default: m.SharedTripView })));
const NotificationsPage = lazy(() => import('./pages/NotificationsPage').then(m => ({ default: m.NotificationsPage })));
const UserProfilePage = lazy(() => import('./pages/UserProfilePage').then(m => ({ default: m.UserProfilePage })));
const AdminAnalyticsPage = lazy(() => import('./pages/AdminAnalyticsPage').then(m => ({ default: m.AdminAnalyticsPage })));
const MultiStopPlanner = lazy(() => import('./pages/MultiStopPlanner').then(m => ({ default: m.MultiStopPlanner })));

// Loading Spinner Indicator (Phase 3 Loader State)
const RouteFallbackLoader = () => (
  <div className="min-h-screen bg-paper-50 dark:bg-paper-900 flex flex-col items-center justify-center text-paper-900 dark:text-paper-100 gap-4">
    <Loader className="h-10 w-10 text-marigold-700 animate-spin" />
    <span className="text-sm font-bold tracking-wider text-paper-400 uppercase">Synchronizing BudgetBound...</span>
  </div>
);

// Protected Route Wrapper Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <RouteFallbackLoader />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
};

// Anonymous Route Wrapper Component (Redirects to dashboard if already logged in)
const AnonymousRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <RouteFallbackLoader />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<RouteFallbackLoader />}>
          <Routes>
            {/* Public / Auth Routes */}
            <Route path="/" element={<AnonymousRoute><LandingPage /></AnonymousRoute>} />
            <Route path="/login" element={<AnonymousRoute><Login /></AnonymousRoute>} />
            <Route path="/register" element={<AnonymousRoute><Register /></AnonymousRoute>} />

            {/* Protected Dashboard/App Routes */}
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/planner" element={<ProtectedRoute><BudgetPlanner /></ProtectedRoute>} />
            <Route path="/my-trips" element={<ProtectedRoute><SavedTrips /></ProtectedRoute>} />
            <Route path="/compare" element={<ProtectedRoute><CompareDestinations /></ProtectedRoute>} />
            <Route path="/reverse-search" element={<ProtectedRoute><BudgetPlanner initialMode="discover" /></ProtectedRoute>} />

            <Route path="/explorer" element={<ProtectedRoute><DestinationExplorer /></ProtectedRoute>} />
            <Route path="/explorer/:id" element={<ProtectedRoute><DestinationDetail /></ProtectedRoute>} />

            <Route path="/optimizer/:tripId" element={<ProtectedRoute><BudgetOptimizer /></ProtectedRoute>} />
            <Route path="/expenses/:tripId" element={<ProtectedRoute><ExpenseTracker /></ProtectedRoute>} />
            <Route path="/ai-companion" element={<ProtectedRoute><AICompanion /></ProtectedRoute>} />
            <Route path="/multi-stop" element={<ProtectedRoute><MultiStopPlanner /></ProtectedRoute>} />

            <Route path="/notifications" element={<ProtectedRoute><NotificationsPage /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><UserProfilePage /></ProtectedRoute>} />
            <Route path="/admin" element={<ProtectedRoute><AdminAnalyticsPage /></ProtectedRoute>} />

            {/* Public Shared Trip Route */}
            <Route path="/share/:shareToken" element={<SharedTripView />} />

            {/* Catch-all route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;



