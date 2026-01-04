'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/context/AuthContext';
import { Button } from '@/app/components/ui/Button';
import { Input } from '@/app/components/ui/Input';
import { Select } from '@/app/components/ui/Select';
import { UserRole } from '@/app/types';
import { RefreshIcon } from '@/app/components/icons';
import toast from 'react-hot-toast';

type ViewState = 'login' | 'signup' | 'forgot' | 'reset';

export default function LoginPage() {
  const router = useRouter();
  const { login, signup, checkApproval, isAuthenticated, user } = useAuth();

  const [view, setView] = useState<ViewState>('login');
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('staff');
  
  // Forgot/Reset password states
  const [resetCode, setResetCode] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
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
          setEmail(data.email);
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

    try {
      if (view === 'signup') {
        if (!email || !password) {
            setError('Please enter email and password');
            setIsLoading(false);
            return;
        }

        const result = await signup(email, password, role);

        if (result.success) {
          if (result.needsApproval) {
            // Store credentials for approval checking
            localStorage.setItem('clubem_pending_approval', JSON.stringify({
              email,
              password,
              role,
            }));
            setIsWaitingForApproval(true);
          } else {
            // Auto-approved (admin), redirect
            router.push(role === 'admin' ? '/admin' : '/app');
          }
        } else {
          setError(result.error || 'Failed to create account');
        }
      } else if (view === 'login') {
        if (!email || !password) {
            setError('Please enter email and password');
            setIsLoading(false);
            return;
        }
        const result = await login(email, password, role);

        if (result.success) {
          router.push(role === 'admin' ? '/admin' : '/app');
        } else {
          setError(result.error || 'Invalid credentials');
        }
      } else if (view === 'forgot') {
        if (!email) {
            setError('Please enter your email');
            setIsLoading(false);
            return;
        }

        const response = await fetch('/api/auth/forgot-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            toast.success('Reset code sent to your email');
            setView('reset');
        } else {
            setError(data.error || 'Failed to send reset code');
        }
      } else if (view === 'reset') {
        if (!email || !resetCode || !newPassword) {
            setError('Please fill in all fields');
            setIsLoading(false);
            return;
        }

        const response = await fetch('/api/auth/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, code: resetCode, newPassword }),
        });

        const data = await response.json();

        if (response.ok) {
            toast.success('Password reset successfully');
            setView('login');
            setPassword('');
            setResetCode('');
            setNewPassword('');
        } else {
            setError(data.error || 'Failed to reset password');
        }
      }
    } catch (err) {
      console.error(err);
      setError('An error occurred. Please try again.');
    } finally {
        setIsLoading(false);
    }
  };

  const handleCheckApproval = async () => {
    setIsCheckingApproval(true);
    setError('');

    try {
      const result = await checkApproval(email, password);

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
    setEmail('');
    setPassword('');
    setError('');
    setView('login');
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
                Email: <span className="font-mono font-medium">{email}</span>
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
              {(view === 'login' || view === 'signup') && (
                  <div className="flex gap-2 mb-6 p-1 bg-slate-100 rounded-lg">
                    <button
                      type="button"
                      onClick={() => {
                        setView('login');
                        setError('');
                      }}
                      className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${view === 'login'
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                        }`}
                    >
                      Sign In
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setView('signup');
                        setError('');
                      }}
                      className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${view === 'signup'
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                        }`}
                    >
                      Sign Up
                    </button>
                  </div>
              )}

              {view === 'forgot' && (
                 <div className="mb-6">
                    <h2 className="text-lg font-semibold text-slate-900">Reset Password</h2>
                    <p className="text-sm text-slate-500">Enter your email to receive a reset code.</p>
                 </div>
              )}
              
              {view === 'reset' && (
                 <div className="mb-6">
                    <h2 className="text-lg font-semibold text-slate-900">Set New Password</h2>
                    <p className="text-sm text-slate-500">Enter the code sent to {email} and your new password.</p>
                 </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                {(view === 'login' || view === 'signup') && (
                    <Select
                      label="Role"
                      value={role}
                      onChange={(e) => setRole(e.target.value as UserRole)}
                      options={[
                        { value: 'admin', label: 'Administrator' },
                        { value: 'staff', label: 'Staff Member' },
                      ]}
                    />
                )}

                <Input
                  label="Email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  disabled={view === 'reset'} // Locked during reset
                />

                {(view === 'login' || view === 'signup') && (
                    <Input
                      label="Password"
                      type="password"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      autoComplete="current-password"
                    />
                )}
                
                {view === 'reset' && (
                    <>
                        <Input
                          label="Reset Code"
                          type="text"
                          placeholder="Enter 6-digit code"
                          value={resetCode}
                          onChange={(e) => setResetCode(e.target.value)}
                        />
                        <Input
                          label="New Password"
                          type="password"
                          placeholder="Enter new password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                        />
                    </>
                )}

                {error && (
                  <div className="p-3 rounded-md bg-red-50 border border-red-200">
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                )}
                
                {view === 'login' && (
                    <div className="flex justify-end">
                        <button 
                            type="button" 
                            className="text-sm text-blue-600 hover:text-blue-800"
                            onClick={() => {
                                setView('forgot');
                                setError('');
                            }}
                        >
                            Forgot Password?
                        </button>
                    </div>
                )}

                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  isLoading={isLoading}
                >
                  {view === 'signup' ? 'Create Account' : 
                   view === 'login' ? 'Sign In' :
                   view === 'forgot' ? 'Send Reset Code' :
                   'Reset Password'}
                </Button>
                
                {(view === 'forgot' || view === 'reset') && (
                    <Button
                      variant="secondary"
                      onClick={() => {
                          setView('login');
                          setError('');
                      }}
                      className="w-full"
                      size="lg"
                    >
                      Back to Login
                    </Button>
                )}
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
