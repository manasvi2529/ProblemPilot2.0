'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { usePreferences } from '@/lib/preferences-context';
import {
  Sparkles,
  Lightbulb,
  FolderGit2,
  ShieldCheck,
  GraduationCap,
  Plug,
  CloudLightning,
  Compass,
  ShieldAlert,
  Volume2,
  VolumeX,
  Sun,
  Moon,
  Menu,
  X,
  LogIn,
  LogOut,
  ChevronRight,
  Zap,
  Sliders,
  CheckCircle2,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { user, operatingMode, setOperatingMode, openAuthModal, logout } = useAuth();
  const { voiceEnabled, toggleVoice, theme, toggleTheme } = usePreferences();
  const [isOpenMobile, setIsOpenMobile] = useState(false);

  // Close mobile drawer on route change
  useEffect(() => {
    setIsOpenMobile(false);
  }, [pathname]);

  // Prevent background scrolling when mobile sidebar is open
  useEffect(() => {
    if (isOpenMobile) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpenMobile]);

  const navGroups = [
    {
      title: 'PLATFORM CORE',
      items: [
        {
          href: '/',
          label: 'Prompt Studio',
          icon: Sparkles,
          badge: 'Live',
        },
        {
          href: '/opportunities',
          label: 'Candidate Opportunities',
          icon: Lightbulb,
        },
        {
          href: '/projects',
          label: 'Projects & Workspaces',
          icon: FolderGit2,
        },
      ],
    },
    {
      title: 'AUTONOMOUS SUITE',
      items: [
        {
          href: '/teacher',
          label: 'AI Teacher & Mentor',
          icon: GraduationCap,
          badge: 'Prep',
        },
        {
          href: '/approvals',
          label: 'Security Approvals',
          icon: ShieldCheck,
        },
        {
          href: '/integrations',
          label: 'Integrations & Cloud',
          icon: Plug,
        },
      ],
    },
    {
      title: 'AUDIT & RESEARCH',
      items: [
        {
          href: '/audit',
          label: 'Audit Ledger',
          icon: ShieldAlert,
        },
        {
          href: '/deployments',
          label: 'Cloud Deployments',
          icon: CloudLightning,
        },
        {
          href: '/research',
          label: 'Research & Evidence',
          icon: Compass,
        },
      ],
    },
  ];

  const sidebarContent = (
    <div className="flex flex-col h-full bg-[#0a0f1d] border-r border-[#1a233a] select-none text-slate-300">
      {/* Brand & System Status */}
      <div className="p-5 border-b border-[#1a233a]">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-accent-purple shadow-md shadow-brand-500/20 group-hover:scale-105 transition-transform duration-200">
            <Zap className="h-4 w-4 text-white fill-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-black text-sm tracking-tight text-white group-hover:text-brand-300 transition-colors">
                ProblemPilot
              </span>
              <span className="rounded bg-brand-500/20 px-1.5 py-0.2 text-[9px] font-bold text-brand-300 border border-brand-500/30">
                AI
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-emerald opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-accent-emerald"></span>
              </span>
              <span className="text-[10px] text-slate-400 font-mono">Engine Active &bull; 8000</span>
            </div>
          </div>
        </Link>
      </div>

      {/* Operating Mode Selector Quick-Toggle */}
      <div className="px-4 py-3 border-b border-[#1a233a] bg-[#0c1427]/60">
        <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
          <span className="flex items-center gap-1">
            <Sliders className="h-3 w-3 text-brand-400" />
            Mode
          </span>
          <span className="text-brand-300 font-mono capitalize">{operatingMode}</span>
        </div>
        <div className="grid grid-cols-3 gap-1 bg-[#070b14] p-0.5 rounded-lg border border-[#1e293b]">
          {(['autonomous', 'guided', 'hybrid'] as const).map((m) => {
            const active = operatingMode === m;
            return (
              <button
                key={m}
                onClick={() => setOperatingMode(m)}
                className={`btn-press py-1 text-[10px] font-semibold rounded capitalize transition-all ${
                  active
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title={`Switch to ${m} mode`}
              >
                {m === 'autonomous' ? '⚡ Auto' : m === 'guided' ? '🛡️ Guide' : '⚖️ Hybrid'}
              </button>
            );
          })}
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navGroups.map((group) => (
          <div key={group.title} className="space-y-1">
            <div className="px-3 text-[10px] font-black uppercase tracking-wider text-slate-400">
              {group.title}
            </div>
            <div className="space-y-0.5 pt-1">
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`btn-press group flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all duration-150 ${
                      isActive
                        ? 'bg-brand-500/15 text-white border-l-2 border-brand-500 shadow-sm'
                        : 'text-slate-400 hover:bg-[#131d33] hover:text-slate-100'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon
                        className={`h-4 w-4 transition-colors ${
                          isActive
                            ? 'text-brand-400'
                            : 'text-slate-400 group-hover:text-slate-200'
                        }`}
                      />
                      <span>{item.label}</span>
                    </div>

                    {item.badge && (
                      <span className="rounded bg-brand-500/20 px-1.5 py-0.5 text-[9px] font-bold text-brand-300">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Footer Area: User Profile, Voice & Theme */}
      <div className="p-3 border-t border-[#1a233a] bg-[#0c1427]/60 space-y-2">
        {/* User Card */}
        {user ? (
          <div className="flex items-center justify-between rounded-xl bg-[#070b14] p-2 border border-[#1e293b]">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="h-7 w-7 shrink-0 rounded-lg bg-brand-600/30 border border-brand-500/40 flex items-center justify-center text-xs font-bold text-brand-300">
                {(user.username || user.email || 'U')[0].toUpperCase()}
              </div>
              <div className="min-w-0">
                <div className="text-xs font-bold text-white truncate">
                  {user.username || user.name || 'Engineer'}
                </div>
                <div className="text-[10px] text-slate-400 truncate font-mono">
                  {user.email}
                </div>
              </div>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="btn-press p-1.5 rounded-lg text-slate-400 hover:text-accent-rose hover:bg-accent-rose/10 transition-colors"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => openAuthModal('login')}
            className="btn-press flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 px-3 py-2 text-xs font-bold text-white shadow-sm hover:bg-brand-500 transition-colors"
          >
            <LogIn className="h-3.5 w-3.5" />
            <span>Sign In / Register</span>
          </button>
        )}

        {/* Voice and Theme Switchers */}
        <div className="flex items-center gap-1.5 pt-1">
          <button
            onClick={toggleVoice}
            className={`btn-press flex-1 flex items-center justify-center gap-1.5 rounded-lg py-1.5 px-2 text-[11px] font-medium border transition-colors ${
              voiceEnabled
                ? 'border-brand-500/40 bg-brand-500/15 text-brand-300'
                : 'border-[#1e293b] bg-[#070b14] text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle Voice Synthesis / TTS"
          >
            {voiceEnabled ? (
              <Volume2 className="h-3.5 w-3.5 text-accent-emerald" />
            ) : (
              <VolumeX className="h-3.5 w-3.5" />
            )}
            <span>{voiceEnabled ? 'Voice On' : 'Muted'}</span>
          </button>

          <button
            onClick={toggleTheme}
            className="btn-press flex items-center justify-center rounded-lg p-1.5 border border-[#1e293b] bg-[#070b14] text-slate-400 hover:text-slate-200 hover:bg-[#131d33] transition-colors"
            title="Toggle Dark / Light Theme"
          >
            {theme === 'dark' ? (
              <Sun className="h-3.5 w-3.5 text-amber-400" />
            ) : (
              <Moon className="h-3.5 w-3.5 text-brand-400" />
            )}
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar: Fixed 64 (16rem) width */}
      <aside className="hidden md:block fixed inset-y-0 left-0 w-64 z-30">
        {sidebarContent}
      </aside>

      {/* Mobile Top Header with Hamburger */}
      <header className="md:hidden sticky top-0 z-40 flex items-center justify-between border-b border-[#1a233a] bg-[#0a0f1d]/90 backdrop-blur-md px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-600 shadow-sm">
            <Zap className="h-3.5 w-3.5 text-white fill-white" />
          </div>
          <span className="font-black text-sm text-white">ProblemPilot AI</span>
        </Link>

        <button
          onClick={() => setIsOpenMobile(!isOpenMobile)}
          className="btn-press p-2 rounded-xl text-slate-300 hover:text-white bg-[#131d33] border border-[#1e293b]"
          aria-label="Toggle Navigation Menu"
        >
          {isOpenMobile ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </header>

      {/* Mobile Drawer Overlay */}
      {isOpenMobile && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          {/* Backdrop with fade-in */}
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
            onClick={() => setIsOpenMobile(false)}
          />

          {/* Slide-out Sidebar Drawer */}
          <div className="relative w-72 max-w-[85vw] h-full shadow-2xl z-10 transition-transform duration-300 ease-out">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
