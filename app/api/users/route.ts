import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';
import bcrypt from 'bcrypt';
import { UserRole } from '@prisma/client';

// GET all users
export async function GET() {
  try {
    const users = await prisma.user.findMany({
      orderBy: { createdAt: 'desc' },
    });

    // Map to frontend User type format
    const mappedUsers = users.map(user => ({
      id: user.id,
      name: user.username,
      email: `${user.username}@clubem.com`,
      role: user.role.toLowerCase() as 'admin' | 'staff',
      status: user.isApproved ? 'active' as const : 'inactive' as const,
      createdAt: user.createdAt.toISOString().split('T')[0],
      isApproved: user.isApproved,
    }));

    return NextResponse.json({ users: mappedUsers });
  } catch (error) {
    console.error('Get users error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// POST create new user
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { username, password, role } = body;

    // Validate input
    if (!username || !password) {
      return NextResponse.json(
        { error: 'Username and password are required' },
        { status: 400 }
      );
    }

    if (password.length < 6) {
      return NextResponse.json(
        { error: 'Password must be at least 6 characters long' },
        { status: 400 }
      );
    }

    // Validate role
    const validRole = role === 'admin' ? UserRole.ADMIN : UserRole.STAFF;
    if (role && role !== 'admin' && role !== 'staff') {
      return NextResponse.json(
        { error: 'Invalid role. Must be "admin" or "staff"' },
        { status: 400 }
      );
    }

    // Check if user already exists
    const existingUser = await prisma.user.findUnique({
      where: { username },
    });

    if (existingUser) {
      return NextResponse.json(
        { error: 'Username already exists' },
        { status: 409 }
      );
    }

    // Hash password
    const saltRounds = parseInt(process.env.BCRYPT_SALT_ROUNDS || '10', 10);
    const hashedPassword = await bcrypt.hash(password, saltRounds);

    // Create user - users added from admin panel are auto-approved
    const user = await prisma.user.create({
      data: {
        username,
        password: hashedPassword,
        role: validRole,
        isApproved: true, // Admin-created users are automatically approved
      },
    });

    // Return user data (without password)
    return NextResponse.json({
      user: {
        id: user.id,
        name: user.username,
        email: `${user.username}@clubem.com`,
        role: user.role.toLowerCase() as 'admin' | 'staff',
        status: user.isApproved ? 'active' as const : 'inactive' as const,
        createdAt: user.createdAt.toISOString().split('T')[0],
        isApproved: user.isApproved,
      },
    }, { status: 201 });
  } catch (error) {
    console.error('Create user error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

