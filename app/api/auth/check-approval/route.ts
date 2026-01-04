import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';

// POST check approval status
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password } = body;

    // Validate input
    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    // Find user by email
    const user = await prisma.user.findUnique({
      where: { email },
    });

    if (!user) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    // Verify password
    const bcrypt = await import('bcrypt');
    const isPasswordValid = await bcrypt.compare(password, user.password);

    if (!isPasswordValid) {
      return NextResponse.json(
        { error: 'Invalid credentials' },
        { status: 401 }
      );
    }

    // Return approval status
    return NextResponse.json({
      isApproved: user.isApproved,
      user: user.isApproved ? {
        id: user.id,
        name: user.name || user.email.split('@')[0],
        email: user.email,
        role: user.role.toLowerCase() as 'admin' | 'staff',
        status: 'active' as const,
        createdAt: user.createdAt.toISOString().split('T')[0],
      } : null,
    });
  } catch (error) {
    console.error('Check approval error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

