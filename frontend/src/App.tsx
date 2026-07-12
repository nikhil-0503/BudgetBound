import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

import { Layout } from './components/Layout';
import { LandingPage } from './pages/LandingPage';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { BudgetPlanner } from './pages/BudgetPlanner';
import { DestinationExplorer } from './pages/DestinationExplorer';
import { DestinationDetail } from './pages/DestinationDetail';
import { BudgetOptimizer } from './pages/BudgetOptimizer';
import { ExpenseTracker } from './pages/ExpenseTracker';
import { AICompanion } from './pages/AICompanion';
import { Loader } from 'lucide-react';

// Protected Route Wrapper Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex flex-col items-center justify-center text-slate-900 dark:text-slate-100 gap-4">
        <Loader className="h-10 w-10 text-violet-500 animate-spin" />
        <span className="text-sm font-medium tracking-wide text-slate-500 dark:text-slate-400">Loading BudgetBound...</span>
      </div>
    );
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
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex flex-col items-center justify-center text-slate-900 dark:text-slate-100 gap-4">
        <Loader className="h-10 w-10 text-violet-500 animate-spin" />
        <span className="text-sm font-medium tracking-wide text-slate-500 dark:text-slate-400">Loading BudgetBound...</span>
      </div>
    );
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
          <Routes>
            {/* Public / Auth Routes */}
            <Route path="/" element={<AnonymousRoute><LandingPage /></AnonymousRoute>} />
            <Route path="/login" element={<AnonymousRoute><Login /></AnonymousRoute>} />
            <Route path="/register" element={<AnonymousRoute><Register /></AnonymousRoute>} />

            {/* Protected Dashboard/App Routes */}
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/planner" element={<ProtectedRoute><BudgetPlanner /></ProtectedRoute>} />
            <Route path="/reverse-search" element={<ProtectedRoute><BudgetPlanner initialMode="discover" /></ProtectedRoute>} />
            
            <Route path="/explorer" element={<ProtectedRoute><DestinationExplorer /></ProtectedRoute>} />
            <Route path="/explorer/:id" element={<ProtectedRoute><DestinationDetail /></ProtectedRoute>} />
            
            <Route path="/optimizer/:tripId" element={<ProtectedRoute><BudgetOptimizer /></ProtectedRoute>} />
            <Route path="/expenses/:tripId" element={<ProtectedRoute><ExpenseTracker /></ProtectedRoute>} />
            <Route path="/ai-companion" element={<ProtectedRoute><AICompanion /></ProtectedRoute>} />

            {/* Catch-all route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
  );
}

export default App;
