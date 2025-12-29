'use client';

import React, { useState } from 'react';
import { PageContainer, PageSection } from '@/app/components/layout/PageContainer';
import { Card, CardHeader } from '@/app/components/ui/Card';
import { Button } from '@/app/components/ui/Button';
import { Input } from '@/app/components/ui/Input';
import { Select } from '@/app/components/ui/Select';
import { useAuth } from '@/app/context/AuthContext';

export default function AdminSettingsPage() {
  const { user } = useAuth();
  const [isSaving, setIsSaving] = useState(false);
  const [emailSettings, setEmailSettings] = useState({
    senderEmail: 'orders@clubem.com',
    senderName: 'Clubem Orders',
    replyTo: 'support@clubem.com',
  });
  const [generalSettings, setGeneralSettings] = useState({
    timezone: 'America/New_York',
    dateFormat: 'MM/DD/YYYY',
    autoSend: false,
  });

  const handleSaveEmail = async () => {
    setIsSaving(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setIsSaving(false);
    alert('Email settings saved!');
  };

  const handleSaveGeneral = async () => {
    setIsSaving(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setIsSaving(false);
    alert('General settings saved!');
  };

  const timezoneOptions = [
    { value: 'America/New_York', label: 'Eastern Time (ET)' },
    { value: 'America/Chicago', label: 'Central Time (CT)' },
    { value: 'America/Denver', label: 'Mountain Time (MT)' },
    { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  ];

  const dateFormatOptions = [
    { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
    { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
    { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
  ];

  const [googleStatus, setGoogleStatus] = useState<{ isConnected: boolean; expiry?: string } | null>(null);

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
      description="Configure system preferences and options"
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
              {user?.name?.charAt(0) || 'A'}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-medium text-slate-900">{user?.name}</h3>
              <p className="text-sm text-slate-500">{user?.email}</p>
              <p className="text-sm text-slate-500 mt-1">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-violet-100 text-violet-700 capitalize">
                  {user?.role}
                </span>
              </p>
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

      {/* Email Settings */}
      <PageSection title="Email Settings">
        <Card>
          <div className="max-w-md space-y-4">
            <Input
              label="Sender Email"
              type="email"
              value={emailSettings.senderEmail}
              onChange={(e) => setEmailSettings(prev => ({ ...prev, senderEmail: e.target.value }))}
            />
            <Input
              label="Sender Name"
              value={emailSettings.senderName}
              onChange={(e) => setEmailSettings(prev => ({ ...prev, senderName: e.target.value }))}
            />
            <Input
              label="Reply-To Email"
              type="email"
              value={emailSettings.replyTo}
              onChange={(e) => setEmailSettings(prev => ({ ...prev, replyTo: e.target.value }))}
            />
            <Button onClick={handleSaveEmail} isLoading={isSaving}>
              Save Email Settings
            </Button>
          </div>
        </Card>
      </PageSection>

      {/* General Settings */}
      <PageSection title="General Settings">
        <Card>
          <div className="max-w-md space-y-4">
            <Select
              label="Timezone"
              options={timezoneOptions}
              value={generalSettings.timezone}
              onChange={(e) => setGeneralSettings(prev => ({ ...prev, timezone: e.target.value }))}
            />
            <Select
              label="Date Format"
              options={dateFormatOptions}
              value={generalSettings.dateFormat}
              onChange={(e) => setGeneralSettings(prev => ({ ...prev, dateFormat: e.target.value }))}
            />
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="autoSend"
                checked={generalSettings.autoSend}
                onChange={(e) => setGeneralSettings(prev => ({ ...prev, autoSend: e.target.checked }))}
                className="w-4 h-4 text-slate-900 border-slate-300 rounded focus:ring-slate-500"
              />
              <label htmlFor="autoSend" className="text-sm text-slate-700">
                Auto-send orders when processing completes
              </label>
            </div>
            <Button onClick={handleSaveGeneral} isLoading={isSaving}>
              Save General Settings
            </Button>
          </div>
        </Card>
      </PageSection>

      {/* Danger Zone */}
      <PageSection title="Danger Zone">
        <Card className="border-red-200">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-slate-900">Clear All Data</h4>
              <p className="text-sm text-slate-500">
                This will permanently delete all orders and uploads. This action cannot be undone.
              </p>
            </div>
            <Button variant="danger">
              Clear Data
            </Button>
          </div>
        </Card>
      </PageSection>
    </PageContainer>
  );
}

