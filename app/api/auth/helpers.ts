import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'staff';
  isApproved: boolean;
}

/**
 * Get authenticated user from userId
 * Use this when you already have the userId (e.g., from request body)
 */
export async function getAuthenticatedUserFromId(userId: string): Promise<AuthUser | null> {
  try {
    if (!userId) {
      return null;
    }

    // Find user
    const user = await prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user || !user.isApproved) {
      return null;
    }

    return {
      id: user.id,
      name: user.name || user.email.split('@')[0],
      email: user.email,
      role: user.role.toLowerCase() as 'admin' | 'staff',
      isApproved: user.isApproved,
    };
  } catch (error) {
    console.error('Auth error:', error);
    return null;
  }
}

/**
 * Get authenticated user from userId (for GET requests)
 */
export async function getAuthenticatedUserById(userId: string): Promise<AuthUser | null> {
  try {
    if (!userId) {
      return null;
    }

    const user = await prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user || !user.isApproved) {
      return null;
    }

    return {
      id: user.id,
      name: user.name || user.email.split('@')[0],
      email: user.email,
      role: user.role.toLowerCase() as 'admin' | 'staff',
      isApproved: user.isApproved,
    };
  } catch (error) {
    console.error('Auth error:', error);
    return null;
  }
}

/**
 * Check if user is admin
 */
export function requireAdmin(user: AuthUser | null): boolean {
  return user?.role === 'admin' && user?.isApproved === true;
}

/**
 * Create unauthorized response
 */
export function unauthorizedResponse(message: string = 'Unauthorized') {
  return NextResponse.json(
    { error: message },
    { status: 401 }
  );
}

/**
 * Create forbidden response
 */
export function forbiddenResponse(message: string = 'Forbidden: Admin access required') {
  return NextResponse.json(
    { error: message },
    { status: 403 }
  );
}

