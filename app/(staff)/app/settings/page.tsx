'use client';

import React from 'react';
import { PageContainer, PageSection } from '@/app/components/layout/PageContainer';
import { Card } from '@/app/components/ui/Card';
import { Button } from '@/app/components/ui/Button';
import { Input } from '@/app/components/ui/Input';
import { useAuth } from '@/app/context/AuthContext';

export default function StaffSettingsPage() {
  const { user } = useAuth();
  const [googleStatus, setGoogleStatus] = React.useState<{ isConnected: boolean; expiry?: string } | null>(null);

  React.useEffect(() => {
    if (user?.id) {
      fetch(`/api/integrations/google/status?userId=${user.id}`)
        .then(res => res.json())
        .then(data => setGoogleStatus(data))
        .catch(err => console.error('Failed to fetch google status', err));
    }
  }, [user?.id]);

  const handleConnectGoogle = () => {
    if (!user?.id) return;
    window.location.href = `/api/auth/google?userId=${user.id}`;
  };

  return (
    <PageContainer
      title="Settings"
      description="View your profile and update your password"
    >
      {/* Google Integration Section */}
      <PageSection title="Integrations">
        <Card>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-medium text-slate-900">Google Sheets</h3>
                <p className="text-sm text-slate-500">
                  {googleStatus?.isConnected 
                    ? `Connected (Expires: ${googleStatus.expiry ? new Date(googleStatus.expiry).toLocaleString() : 'N/A'})`
                    : 'Automate exports directly to Google Sheets without manual pasting.'}
                </p>
              </div>
            </div>
            <Button
              variant={googleStatus?.isConnected ? 'secondary' : 'primary'}
              onClick={handleConnectGoogle}
            >
              {googleStatus?.isConnected ? 'Reconnect Google Account' : 'Connect Google Account'}
            </Button>
          </div>
        </Card>
      </PageSection>

      {/* Profile Section */}
      <PageSection title="Profile Information">
        <Card>
          <div className="flex items-start gap-6">
            <div className="w-16 h-16 bg-slate-200 rounded-full flex items-center justify-center text-2xl font-semibold text-slate-600">
              {user?.name?.charAt(0) || 'S'}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-medium text-slate-900">{user?.name}</h3>
              <p className="text-sm text-slate-500">{user?.email}</p>
              <p className="text-sm text-slate-500 mt-1">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-sky-100 text-sky-700 capitalize">
                  {user?.role}
                </span>
              </p>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-slate-200">
            <p className="text-sm text-slate-500 mb-4">
              Contact an administrator if you need to update your profile information.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Full Name
                </label>
                <p className="px-3 py-2 bg-slate-50 rounded-md text-slate-900">
                  {user?.name}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Email
                </label>
                <p className="px-3 py-2 bg-slate-50 rounded-md text-slate-900">
                  {user?.email}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Role
                </label>
                <p className="px-3 py-2 bg-slate-50 rounded-md text-slate-900 capitalize">
                  {user?.role}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Status
                </label>
                <p className="px-3 py-2 bg-slate-50 rounded-md text-slate-900 capitalize">
                  {user?.status}
                </p>
              </div>
            </div>
          </div>
        </Card>
      </PageSection>

      {/* Change Password */}
      <PageSection title="Change Password">
        <Card>
          <div className="max-w-md space-y-4">
            <Input
              label="Current Password"
              type="password"
              placeholder="Enter current password"
            />
            <Input
              label="New Password"
              type="password"
              placeholder="Enter new password"
              helperText="Password must be at least 8 characters"
            />
            <Input
              label="Confirm New Password"
              type="password"
              placeholder="Confirm new password"
            />
            <Button>Update Password</Button>
          </div>
        </Card>
      </PageSection>

      {/* Preferences */}
      <PageSection title="Preferences">
        <Card>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-900">Email Notifications</p>
                <p className="text-sm text-slate-500">
                  Receive email updates when your orders are processed
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked className="sr-only peer" />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-slate-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-900"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-900">Order Status Updates</p>
                <p className="text-sm text-slate-500">
                  Get notified when order status changes
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked className="sr-only peer" />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-slate-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-900"></div>
              </label>
            </div>
          </div>
        </Card>
      </PageSection>
    </PageContainer>
  );
}

