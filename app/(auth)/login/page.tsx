'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/context/AuthContext';
import { Button } from '@/app/components/ui/Button';
import { Input } from '@/app/components/ui/Input';
import { Select } from '@/app/components/ui/Select';
import { UserRole } from '@/app/types';
import { RefreshIcon } from '@/app/components/icons';

export default function LoginPage() {
  const router = useRouter();
  const { login, signup, checkApproval, isAuthenticated, user } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('staff');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSignup, setIsSignup] = useState(false);
  const [isWaitingForApproval, setIsWaitingForApproval] = useState(false);
  const [isCheckingApproval, setIsCheckingApproval] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      router.push(user.role === 'admin' ? '/admin' : '/app');
    }
  }, [isAuthenticated, user, router]);

  // Check if there's a pending approval in localStorage
  useEffect(() => {
    const pendingApproval = localStorage.getItem('clubem_pending_approval');
    if (pendingApproval) {
      try {
        const data = JSON.parse(pendingApproval);
        // Use setTimeout to avoid synchronous setState in effect
        setTimeout(() => {
          setUsername(data.username);
          setPassword(data.password);
          setRole(data.role);
          setIsWaitingForApproval(true);
        }, 0);
      } catch {
        localStorage.removeItem('clubem_pending_approval');
      }
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (!username || !password) {
      setError('Please enter username and password');
      setIsLoading(false);
      return;
    }

    try {
      if (isSignup) {
        const result = await signup(username, password, role);

        if (result.success) {
          if (result.needsApproval) {
            // Store credentials for approval checking
            localStorage.setItem('clubem_pending_approval', JSON.stringify({
              username,
              password,
              role,
            }));
            setIsWaitingForApproval(true);
            setIsLoading(false);
          } else {
            // Auto-approved (admin), redirect
            router.push(role === 'admin' ? '/admin' : '/app');
          }
        } else {
          setError(result.error || 'Failed to create account');
          setIsLoading(false);
        }
      } else {
        const result = await login(username, password, role);

        if (result.success) {
          router.push(role === 'admin' ? '/admin' : '/app');
        } else {
          setError(result.error || 'Invalid credentials');
          setIsLoading(false);
        }
      }
    } catch {
      setError('An error occurred. Please try again.');
      setIsLoading(false);
    }
  };

  const handleCheckApproval = async () => {
    setIsCheckingApproval(true);
    setError('');

    try {
      const result = await checkApproval(username, password);

      if (result.error) {
        setError(result.error);
        setIsCheckingApproval(false);
        return;
      }

      if (result.isApproved && result.user) {
        // Approved! Clear pending state and redirect
        localStorage.removeItem('clubem_pending_approval');
        setIsWaitingForApproval(false);
        router.push(result.user.role === 'admin' ? '/admin' : '/app');
      } else {
        // Still pending
        setError('');
        setIsCheckingApproval(false);
      }
    } catch {
      setError('An error occurred while checking approval status.');
      setIsCheckingApproval(false);
    }
  };

  const handleBackToLogin = () => {
    localStorage.removeItem('clubem_pending_approval');
    setIsWaitingForApproval(false);
    setUsername('');
    setPassword('');
    setError('');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-slate-900 rounded-xl mb-4">
            <span className="text-white font-bold text-2xl">C</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Welcome to Clubem</h1>
          <p className="mt-2 text-sm text-slate-500">
            Group Order Processing Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-8">
          {isWaitingForApproval ? (
            /* Waiting for Approval State */
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-amber-100 rounded-full mb-4">
                <svg className="w-8 h-8 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-slate-900 mb-2">
                Waiting for Approval
              </h2>
              <p className="text-sm text-slate-600 mb-6">
                Your account has been created successfully, but it requires administrator approval before you can access the platform.
                {role === 'admin' && (
                  <span className="block mt-2 text-xs text-slate-500">
                    Note: Even administrator accounts require approval from an existing administrator.
                  </span>
                )}
              </p>
              <p className="text-xs text-slate-500 mb-6">
                Username: <span className="font-mono font-medium">{username}</span>
              </p>

              {error && (
                <div className="p-3 rounded-md bg-red-50 border border-red-200 mb-4">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              <div className="space-y-3">
                <Button
                  onClick={handleCheckApproval}
                  className="w-full"
                  size="lg"
                  isLoading={isCheckingApproval}
                  leftIcon={<RefreshIcon className="w-4 h-4" />}
                >
                  Check Approval Status
                </Button>
                <Button
                  variant="secondary"
                  onClick={handleBackToLogin}
                  className="w-full"
                  size="lg"
                >
                  Back to Login
                </Button>
              </div>
            </div>
          ) : (
            <>
              {/* Toggle between Login and Signup */}
              <div className="flex gap-2 mb-6 p-1 bg-slate-100 rounded-lg">
                <button
                  type="button"
                  onClick={() => {
                    setIsSignup(false);
                    setError('');
                  }}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${!isSignup
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                    }`}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsSignup(true);
                    setError('');
                  }}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${isSignup
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                    }`}
                >
                  Sign Up
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <Select
                  label="Role"
                  value={role}
                  onChange={(e) => setRole(e.target.value as UserRole)}
                  options={[
                    { value: 'admin', label: 'Administrator' },
                    { value: 'staff', label: 'Staff Member' },
                  ]}
                />

                <Input
                  label="Username"
                  type="text"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                />

                <Input
                  label="Password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />

                {error && (
                  <div className="p-3 rounded-md bg-red-50 border border-red-200">
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                )}

                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  isLoading={isLoading}
                >
                  {isSignup ? 'Create Account' : 'Sign In'}
                </Button>
              </form>
            </>
          )}
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-xs text-slate-400">
          Clubem &copy; {new Date().getFullYear()} &middot; Internal Use Only
        </p>
      </div>
    </div>
  );
}

