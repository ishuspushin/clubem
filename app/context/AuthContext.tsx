'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserRole, AuthState, type User } from '@/app/types';

interface AuthContextType extends AuthState {
  login: (username: string, password: string, role: UserRole) => Promise<{ success: boolean; error?: string; needsApproval?: boolean }>;
  signup: (username: string, password: string, role: UserRole) => Promise<{ success: boolean; error?: string; needsApproval?: boolean }>;
  checkApproval: (username: string, password: string) => Promise<{ isApproved: boolean; user?: User | null; error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'clubem_auth';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
  });
  const [isLoading, setIsLoading] = useState(true);

  // Load auth state from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as AuthState;
        setAuthState(parsed);
      } catch {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  // Persist auth state to localStorage
  useEffect(() => {
    if (!isLoading) {
      if (authState.isAuthenticated && authState.user) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(authState));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  }, [authState, isLoading]);

  const login = async (username: string, password: string, role: UserRole): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        return { success: false, error: error.error || 'Login failed' };
      }

      const data = await response.json();
      
      // Verify the role matches (optional check, or you can remove role from login)
      if (data.user.role !== role) {
        return { success: false, error: 'Role mismatch' };
      }

      setAuthState({
        user: data.user,
        isAuthenticated: true,
      });
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const signup = async (username: string, password: string, role: UserRole): Promise<{ success: boolean; error?: string; needsApproval?: boolean }> => {
    try {
      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password, role }),
      });

      if (!response.ok) {
        const error = await response.json();
        return { success: false, error: error.error || 'Signup failed' };
      }

      const data = await response.json();

      // If user needs approval, don't set them as authenticated
      if (data.needsApproval) {
        return { 
          success: true, 
          needsApproval: true 
        };
      }

      // If approved, set as authenticated
      setAuthState({
        user: data.user,
        isAuthenticated: true,
      });
      return { success: true, needsApproval: false };
    } catch (error) {
      console.error('Signup error:', error);
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const checkApproval = async (username: string, password: string): Promise<{ isApproved: boolean; user?: User | null; error?: string }> => {
    try {
      const response = await fetch('/api/auth/check-approval', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        return { isApproved: false, error: error.error || 'Failed to check approval status' };
      }

      const data = await response.json();

      // If approved, set as authenticated
      if (data.isApproved && data.user) {
        setAuthState({
          user: data.user,
          isAuthenticated: true,
        });
      }

      return { 
        isApproved: data.isApproved, 
        user: data.user || null 
      };
    } catch (error) {
      console.error('Check approval error:', error);
      return { isApproved: false, error: 'Network error. Please try again.' };
    }
  };

  const logout = () => {
    setAuthState({
      user: null,
      isAuthenticated: false,
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-slate-600">Loading...</div>
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{
        ...authState,
        login,
        signup,
        checkApproval,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

