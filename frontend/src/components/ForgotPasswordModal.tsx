import React, { useState } from 'react';
import { X, AlertCircle, CheckCircle, Loader, Mail, Lock } from 'lucide-react';
import api from '../services/api';

interface ForgotPasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ForgotPasswordModal: React.FC<ForgotPasswordModalProps> = ({ isOpen, onClose }) => {
  const [step, setStep] = useState<'email' | 'reset'>('email');
  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleVerifyEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email) {
      setError('Please enter your email address.');
      return;
    }

    setLoading(true);
    try {
      await api.post('/api/auth/forgot-password', { email });
      setStep('reset');
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        'Email not found. Please check and try again.'
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!newPassword || !confirmPassword) {
      setError('Please fill in all fields.');
      return;
    }

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await api.post('/api/auth/reset-password', {
        email,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setSuccess(true);
      // Auto-close after 2 seconds
      setTimeout(() => {
        onClose();
        resetForm();
      }, 2000);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        'Failed to reset password. Please try again.'
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setStep('email');
    setEmail('');
    setNewPassword('');
    setConfirmPassword('');
    setError(null);
    setSuccess(false);
    setShowPassword(false);
  };

  const handleClose = () => {
    onClose();
    resetForm();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-paper-50 dark:bg-ink-900 rounded-2xl shadow-2xl max-w-md w-full p-8 relative">
        {/* Close button */}
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 hover:bg-paper-200 dark:hover:bg-ink-800 rounded-lg transition-colors"
          title="Close"
        >
          <X size={20} className="text-paper-600 dark:text-paper-400" />
        </button>

        {!success ? (
          <>
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2.5 bg-marigold-100 dark:bg-marigold-950 rounded-lg">
                  {step === 'email' ? (
                    <Mail size={20} className="text-marigold-600" />
                  ) : (
                    <Lock size={20} className="text-marigold-600" />
                  )}
                </div>
                <h2 className="text-xl font-semibold text-ink-900 dark:text-paper-50">
                  {step === 'email' ? 'Reset Password' : 'Create New Password'}
                </h2>
              </div>
              <p className="text-sm text-paper-600 dark:text-paper-400">
                {step === 'email'
                  ? 'Enter your email address to reset your password.'
                  : 'Enter your new password below.'}
              </p>
            </div>

            {error && (
              <div className="mb-6 p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-sm flex items-start gap-2.5">
                <AlertCircle size={16} className="shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {step === 'email' ? (
              <form onSubmit={handleVerifyEmail} className="flex flex-col gap-4">
                <div>
                  <label className="block text-xs font-semibold text-paper-600 dark:text-paper-400 mb-2">
                    Email address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    className="w-full bg-paper-100 dark:bg-ink-800/60 border border-paper-300 dark:border-ink-600 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-marigold-500 text-ink-900 dark:text-white transition-all"
                    disabled={loading}
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-2 inline-flex items-center justify-center gap-2 bg-marigold-500 hover:bg-marigold-400 text-ink-950 font-semibold py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <Loader size={16} className="animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    'Continue'
                  )}
                </button>

                <button
                  type="button"
                  onClick={handleClose}
                  className="w-full py-3 rounded-xl border border-paper-300 dark:border-ink-600 text-ink-900 dark:text-paper-100 font-semibold hover:bg-paper-100 dark:hover:bg-ink-800 transition-colors"
                >
                  Cancel
                </button>
              </form>
            ) : (
              <form onSubmit={handleResetPassword} className="flex flex-col gap-4">
                <div>
                  <label className="block text-xs font-semibold text-paper-600 dark:text-paper-400 mb-2">
                    New Password
                  </label>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-paper-100 dark:bg-ink-800/60 border border-paper-300 dark:border-ink-600 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-marigold-500 text-ink-900 dark:text-white transition-all"
                    disabled={loading}
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-paper-600 dark:text-paper-400 mb-2">
                    Confirm Password
                  </label>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-paper-100 dark:bg-ink-800/60 border border-paper-300 dark:border-ink-600 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-marigold-500 text-ink-900 dark:text-white transition-all"
                    disabled={loading}
                  />
                </div>

                <label className="flex items-center gap-2 text-xs text-paper-600 dark:text-paper-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showPassword}
                    onChange={(e) => setShowPassword(e.target.checked)}
                    className="rounded"
                  />
                  Show passwords
                </label>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-2 inline-flex items-center justify-center gap-2 bg-marigold-500 hover:bg-marigold-400 text-ink-950 font-semibold py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <Loader size={16} className="animate-spin" />
                      Resetting...
                    </>
                  ) : (
                    'Reset Password'
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setStep('email');
                    setError(null);
                  }}
                  className="w-full py-3 rounded-xl border border-paper-300 dark:border-ink-600 text-ink-900 dark:text-paper-100 font-semibold hover:bg-paper-100 dark:hover:bg-ink-800 transition-colors"
                >
                  Back
                </button>
              </form>
            )}

            <p className="text-center text-xs text-paper-500 dark:text-paper-400 mt-6">
              Remember your password?{' '}
              <button
                onClick={handleClose}
                className="text-marigold-700 dark:text-marigold-400 hover:underline font-semibold"
              >
                Back to login
              </button>
            </p>
          </>
        ) : (
          <div className="text-center py-8">
            <div className="flex justify-center mb-4">
              <div className="p-3 bg-emerald-100 dark:bg-emerald-950 rounded-full">
                <CheckCircle size={32} className="text-emerald-600" />
              </div>
            </div>
            <h3 className="text-lg font-semibold text-ink-900 dark:text-paper-50 mb-2">
              Password Reset Success
            </h3>
            <p className="text-sm text-paper-600 dark:text-paper-400">
              Your password has been updated. You can now log in with your new password.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

