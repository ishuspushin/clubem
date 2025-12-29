'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/app/context/AuthContext';
import {
  DashboardIcon,
  OrdersIcon,
  UploadIcon,
  UsersIcon,
  PlatformIcon,
  FieldsIcon,
  ProcessIcon,
  ReviewIcon,
  SettingsIcon,
  LogoutIcon,
  QueueIcon,
} from '@/app/components/icons';

interface NavItem {
  name: string;
  href: string;
  icon: React.ReactNode;
}

const adminNavItems: NavItem[] = [
  { name: 'Dashboard', href: '/admin', icon: <DashboardIcon /> },
  { name: 'Processing Queue', href: '/admin/queue', icon: <QueueIcon /> },
  { name: 'Orders', href: '/admin/orders', icon: <OrdersIcon /> },
  { name: 'Fields', href: '/admin/fields', icon: <FieldsIcon /> },
  { name: 'Platforms', href: '/admin/platforms', icon: <PlatformIcon /> },
  { name: 'Users', href: '/admin/users', icon: <UsersIcon /> },
  { name: 'Manual Review', href: '/admin/review', icon: <ReviewIcon /> },
  { name: 'Settings', href: '/admin/settings', icon: <SettingsIcon /> },
];

const staffNavItems: NavItem[] = [
  { name: 'Upload Orders', href: '/app', icon: <UploadIcon /> },
  { name: 'My Uploads', href: '/app/uploads', icon: <OrdersIcon /> },
  { name: 'Orders', href: '/app/orders', icon: <OrdersIcon /> },
  { name: 'Settings', href: '/app/settings', icon: <SettingsIcon /> },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navItems = user?.role === 'admin' ? adminNavItems : staffNavItems;
  const basePath = user?.role === 'admin' ? '/admin' : '/app';

  const isActive = (href: string) => {
    if (href === basePath) {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 bg-slate-900 text-white flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800">
        <Link href={basePath} className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white rounded-md flex items-center justify-center">
            <span className="text-slate-900 font-bold text-lg">C</span>
          </div>
          <span className="text-xl font-semibold tracking-tight">Clubem</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 overflow-y-auto">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.name}>
              <Link
                href={item.href}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-md
                  text-sm font-medium transition-colors
                  ${isActive(item.href)
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }
                `}
              >
                {item.icon}
                {item.name}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 px-3 py-2 mb-2">
          <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center text-sm font-medium">
            {user?.name?.charAt(0) || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.name}</p>
            <p className="text-xs text-slate-400 capitalize">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={() => {
            logout();
            window.location.href = '/login';
          }}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
        >
          <LogoutIcon />
          Sign Out
        </button>
      </div>
    </aside>
  );
}

