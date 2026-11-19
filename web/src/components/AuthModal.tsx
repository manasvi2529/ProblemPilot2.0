'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/lib/auth-context';
import { Layers, X, KeyRound, UserPlus, Sparkles, AlertCircle } from 'lucide-react';

export function AuthModal() {
  const { isAuthModalOpen, closeAuthModal, authTab, setAuthTab, login, register, user } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (authTab === 'login') {
        if (!email || !password) {
          throw new Error('Please enter both email and password.');
        }
        await login(email, password);
      } else {
        if (!username || !email || !password) {
          throw new Error('Username, email, and password (min 8 chars) are required.');
        }
        await register(name, username, email, password);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemoAccount = () => {
    setAuthTab('login');
    setEmail('demo_user@example.com');
    setPassword('DemoPassword123!');
    setError(null);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 bg-black/80 backdrop-blur-sm"
          onClick={() => {
            if (user) closeAuthModal();
          }}
        />

        {/* Modal Window with Emil Kowalski scale: 0.96 entrance */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 8 }}
          transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
          className="relative w-full max-w-md overflow-hidden rounded-2xl border border-border-subtle bg-[#0c121e] p-7 shadow-2xl shadow-black/90"
        >
          {user && (
            <button
              onClick={closeAuthModal}
              className="absolute right-4 top-4 rounded-lg p-1.5 text-slate-400 hover:bg-surface-200 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          )}

          {/* Header */}
          <div className="flex flex-col items-center text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-brand-600 to-accent-purple shadow-lg shadow-brand-500/25 mb-3">
              <Layers className="h-6 w-6 text-white" />
            </div>
            <h2 className="text-xl font-bold tracking-tight text-white">
              ProblemPilot <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-accent-purple">AI</span>
            </h2>
            <p className="mt-1 text-xs text-slate-400">
              Autonomous Problem Discovery & Codebase Generation
            </p>
          </div>

          {/* Quick Demo Fill Helper */}
          <div className="mt-4 flex justify-center">
            <button
              type="button"
              onClick={fillDemoAccount}
              className="btn-press flex items-center gap-1.5 rounded-full border border-brand-500/30 bg-brand-500/10 px-3 py-1 text-[11px] font-medium text-brand-300 hover:bg-brand-500/20"
            >
              <Sparkles className="h-3 w-3 text-brand-400" />
              <span>Use Demo Account (1-Click Fill)</span>
            </button>
          </div>

          {/* Tabs */}
          <div className="mt-5 flex rounded-xl border border-border-subtle bg-surface-300/60 p-1">
            <button
              type="button"
              onClick={() => {
                setAuthTab('login');
                setError(null);
              }}
              className={`btn-press flex-1 rounded-lg py-2 text-xs font-semibold transition-all ${
                authTab === 'login'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setAuthTab('register');
                setError(null);
              }}
              className={`btn-press flex-1 rounded-lg py-2 text-xs font-semibold transition-all ${
                authTab === 'register'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 flex items-center gap-2 rounded-lg border border-accent-rose/30 bg-accent-rose/10 px-3 py-2 text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0 text-accent-rose" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="mt-5 space-y-3.5">
            {authTab === 'register' && (
              <>
                <div>
                  <label className="block text-[11px] font-medium text-slate-300 mb-1">Full Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Jane Doe"
                    className="w-full rounded-lg border border-border-subtle bg-surface-400/80 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-300 mb-1">Username</label>
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="janedoe"
                    className="w-full rounded-lg border border-border-subtle bg-surface-400/80 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
              </>
            )}

            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-lg border border-border-subtle bg-surface-400/80 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">Password</label>
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="•••••••• (min 8 characters)"
                className="w-full rounded-lg border border-border-subtle bg-surface-400/80 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-press mt-2 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-accent-purple py-2.5 text-xs font-semibold text-white shadow-lg shadow-brand-500/25 hover:from-brand-500 hover:to-accent-purple/90 disabled:opacity-50"
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Processing...</span>
                </span>
              ) : authTab === 'login' ? (
                <>
                  <KeyRound className="h-3.5 w-3.5" />
                  <span>Sign In & Continue</span>
                </>
              ) : (
                <>
                  <UserPlus className="h-3.5 w-3.5" />
                  <span>Create Account</span>
                </>
              )}
            </button>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
