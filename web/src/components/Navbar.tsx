'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';
import { SystemHealth } from '@/types';
import {
  Sparkles,
  FolderGit2,
  ShieldCheck,
  Compass,
  CloudLightning,
  LogOut,
  User as UserIcon,
  Activity,
  Layers
} from 'lucide-react';

export function Navbar() {
  const pathname = usePathname();
  const { user, logout, openAuthModal, setOperatingMode } = useAuth();
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [pendingApprovals, setPendingApprovals] = useState<number>(0);

  useEffect(() => {
    async function loadStatus() {
      try {
        const h = await api.getHealth();
        setHealth(h);
      } catch (err) {
        console.warn('Health check failed:', err);
      }

      if (user) {
        try {
          const approvals = await api.listApprovals('pending');
          setPendingApprovals(approvals.length);
        } catch {
          // ignore
        }
      }
    }

    loadStatus();
    const interval = setInterval(loadStatus, 20000);
    return () => clearInterval(interval);
  }, [user]);

  const navItems = [
    { label: 'Prompt Studio', href: '/', icon: Sparkles },
    { label: 'Projects', href: '/projects', icon: FolderGit2 },
    {
      label: 'Approvals',
      href: '/approvals',
      icon: ShieldCheck,
      badge: pendingApprovals > 0 ? pendingApprovals : undefined
    },
    { label: 'Evidence & Research', href: '/research', icon: Compass },
    { label: 'Deployments', href: '/deployments', icon: CloudLightning },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border-subtle bg-[#090d16]/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <Link href="/" className="group flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 to-accent-purple shadow-lg shadow-brand-500/20 transition-transform duration-200 group-hover:scale-105">
              <Layers className="h-5 w-5 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
                ProblemPilot <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-accent-purple font-extrabold text-sm">AI</span>
              </span>
              <span className="text-[10px] font-medium text-slate-400">Problem &rarr; Architecture &rarr; Code</span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`btn-press relative flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors ${
                    isActive
                      ? 'bg-surface-100 text-white shadow-sm border border-border-subtle'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-surface-200/50'
                  }`}
                >
                  <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-brand-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                  {item.badge !== undefined && (
                    <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-accent-rose px-1 text-[10px] font-bold text-white">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-3">
          {/* Health status */}
          <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-border-subtle bg-surface-300/60 px-2.5 py-1 text-[11px] font-mono text-slate-400">
            <span className={`h-2 w-2 rounded-full ${health?.status === 'healthy' ? 'bg-accent-emerald animate-pulse' : 'bg-accent-rose'}`} />
            <span>AI: {health?.integrations.ai.configured ? 'OpenRouter Llama-3.3' : 'Offline'}</span>
          </div>

          {/* Operating Mode Selector */}
          {user && (
            <div className="flex items-center rounded-lg border border-border-subtle bg-surface-400/80 p-0.5 text-xs font-medium text-slate-400">
              {(['guided', 'hybrid', 'autonomous'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setOperatingMode(mode)}
                  className={`btn-press rounded-md px-2.5 py-1 text-[11px] font-semibold capitalize transition-all ${
                    user.operating_mode === mode
                      ? 'bg-brand-600 text-white shadow-sm'
                      : 'hover:text-slate-200'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          )}

          {/* User Profile / Auth */}
          {user ? (
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 rounded-lg border border-border-subtle bg-surface-300/60 px-3 py-1.5">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-500/20 text-xs font-bold text-brand-300 border border-brand-500/30">
                  {(user.name || user.username || 'U').charAt(0).toUpperCase()}
                </div>
                <span className="hidden sm:inline text-xs font-medium text-slate-200">
                  {user.name || user.username}
                </span>
              </div>
              <button
                onClick={logout}
                title="Sign out"
                className="btn-press flex h-8 w-8 items-center justify-center rounded-lg border border-border-subtle bg-surface-300/40 text-slate-400 hover:text-accent-rose hover:bg-surface-200"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => openAuthModal('login')}
              className="btn-press flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-brand-500"
            >
              <UserIcon className="h-3.5 w-3.5" />
              <span>Sign In</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
