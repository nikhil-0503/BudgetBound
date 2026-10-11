import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Wallet, AlertCircle, Loader, Sun, Moon } from 'lucide-react';
import { ForgotPasswordModal } from '../components/ForgotPasswordModal';

export const Login: React.FC = () => {
  usePageTitle('Login | BudgetBound');
  const { login, error, clearError } = useAuth();
  const { darkMode, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [showForgotPassword, setShowForgotPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!email || !password) {
      setLocalError('Please fill in all fields.');
      return;
    }

    setSubmitting(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-paper-100 dark:bg-ink-950 text-ink-900 dark:text-paper-100 flex items-center justify-center p-6 selection:bg-marigold-400 selection:text-ink-950 transition-colors duration-200 relative">

      <div className="absolute top-6 right-6 z-20">
        <button
          onClick={toggleTheme}
          className="p-2.5 rounded-full border border-paper-300 dark:border-ink-700 bg-paper-50 dark:bg-ink-900 text-paper-600 dark:text-paper-300 hover:bg-paper-200 dark:hover:bg-ink-800 transition-colors"
          title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          {darkMode ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>

      <div className="w-full max-w-md ticket p-0 shadow-xl relative z-10">
        <div className="px-8 pt-8 pb-6">
          <Link to="/" className="flex items-center gap-2 justify-center mb-1.5">
            <Wallet className="h-7 w-7 text-marigold-600" />
            <span className="font-display font-semibold text-2xl tracking-tight text-ink-900 dark:text-paper-50">
              BudgetBound
            </span>
          </Link>
          <p className="text-xs text-paper-500 text-center font-medium">Plan trips that fit your wallet</p>
        </div>

        <div className="ticket-perforation" />

        <div className="px-8 pt-6 pb-8">
          <h2 className="font-display text-xl font-semibold text-ink-900 dark:text-paper-50 mb-6 text-center">Welcome back</h2>

          {(error || localError) && (
            <div className="mb-6 p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs flex items-start gap-2.5">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              <span>{localError || error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="block text-xs font-semibold text-paper-600 dark:text-paper-400 mb-2">Email address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full bg-paper-50 dark:bg-ink-800/60 border border-paper-300 dark:border-ink-600 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-marigold-500 text-ink-900 dark:text-white transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-paper-600 dark:text-paper-400 mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-paper-50 dark:bg-ink-800/60 border border-paper-300 dark:border-ink-600 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-marigold-500 text-ink-900 dark:text-white transition-all"
              />
              <button
                type="button"
                onClick={() => setShowForgotPassword(true)}
                className="text-xs text-marigold-700 dark:text-marigold-400 hover:underline font-semibold mt-2"
              >
                Forgot password?
              </button>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full mt-2 inline-flex items-center justify-center gap-2 bg-marigold-500 hover:bg-marigold-400 text-ink-950 font-semibold py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <Loader size={16} className="animate-spin" />
                  Signing in…
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-xs text-paper-500 dark:text-paper-400">
            New to BudgetBound?{' '}
            <Link to="/register" className="text-marigold-700 dark:text-marigold-400 hover:underline font-semibold">
              Create an account
            </Link>
          </p>
        </div>
      </div>

      <ForgotPasswordModal 
        isOpen={showForgotPassword} 
        onClose={() => setShowForgotPassword(false)} 
      />
    </div>
  );
};
