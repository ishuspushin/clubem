'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import { ChevronDownIcon, LogoutIcon, SettingsIcon } from '@/app/components/icons';
import Link from 'next/link';

interface HeaderProps {
  title?: string;
}

export function Header({ title }: HeaderProps) {
  const { user, logout } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const settingsPath = user?.role === 'admin' ? '/admin/settings' : '/app/settings';

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6">
      <div>
        {title && <h1 className="text-xl font-semibold text-slate-900">{title}</h1>}
      </div>

      <div className="flex items-center gap-4">
        {/* Role badge */}
        <span
          className={`
            px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide
            ${user?.role === 'admin'
              ? 'bg-violet-100 text-violet-700'
              : 'bg-sky-100 text-sky-700'
            }
          `}
        >
          {user?.role}
        </span>

        {/* User dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 p-2 rounded-md hover:bg-slate-100 transition-colors"
          >
            <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center text-sm font-medium text-slate-600">
              {user?.name?.charAt(0) || 'U'}
            </div>
            <span className="text-sm font-medium text-slate-700 hidden sm:block">
              {user?.name}
            </span>
            <ChevronDownIcon className="w-4 h-4 text-slate-400" />
          </button>

          {isDropdownOpen && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-md shadow-lg border border-slate-200 py-1 z-50">
              <div className="px-4 py-3 border-b border-slate-100">
                <p className="text-sm font-medium text-slate-900">{user?.name}</p>
                <p className="text-sm text-slate-500 truncate">{user?.email}</p>
              </div>
              <Link
                href={settingsPath}
                onClick={() => setIsDropdownOpen(false)}
                className="flex items-center gap-3 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
              >
                <SettingsIcon className="w-4 h-4" />
                Settings
              </Link>
              <button
                onClick={() => {
                  logout();
                  window.location.href = '/login';
                }}
                className="w-full flex items-center gap-3 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
              >
                <LogoutIcon className="w-4 h-4" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

