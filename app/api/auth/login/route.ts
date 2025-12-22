import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';
import bcrypt from 'bcrypt';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { username, password } = body;

        // Validate input
        if (!username || !password) {
            return NextResponse.json(
                { error: 'Username and password are required' },
                { status: 400 }
            );
        }

        // Find user by username
        const user = await prisma.user.findUnique({
            where: { username },
        });

        if (!user) {
            return NextResponse.json(
                { error: 'Invalid credentials' },
                { status: 401 }
            );
        }

        // Verify password
        const isPasswordValid = await bcrypt.compare(password, user.password);

        if (!isPasswordValid) {
            return NextResponse.json(
                { error: 'Invalid credentials' },
                { status: 401 }
            );
        }

        // Check if user is approved (both admin and staff need approval)
        if (!user.isApproved) {
            return NextResponse.json(
                { error: 'Your account is pending approval. Please contact an administrator.' },
                { status: 403 }
            );
        }

        // Return user data (without password)
        // Map to frontend User type format
        return NextResponse.json({
            user: {
                id: user.id,
                name: user.username,
                email: `${user.username}@clubem.com`,
                role: user.role.toLowerCase() as 'admin' | 'staff',
                status: 'active' as const,
                createdAt: user.createdAt.toISOString().split('T')[0],
            },
        });
    } catch (error) {
        console.error('Login error:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}

