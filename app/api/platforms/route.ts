import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';
import { getAuthenticatedUserFromId, requireAdmin, unauthorizedResponse, forbiddenResponse } from '@/app/api/auth/helpers';
import { PlatformStatus } from '@/generated/prisma/enums';

// GET all platforms (all authenticated users can read)
export async function GET(request: NextRequest) {
  try {
    // Get userId from query params (for GET requests)
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('userId');

    if (!userId) {
      return unauthorizedResponse('User ID is required');
    }

    // Verify user is authenticated (but don't require admin for read)
    const { getAuthenticatedUserById } = await import('@/app/api/auth/helpers');
    const user = await getAuthenticatedUserById(userId);

    if (!user) {
      return unauthorizedResponse('Invalid or unapproved user');
    }

    // Get all platforms
    const platforms = await prisma.platform.findMany({
      orderBy: { createdAt: 'desc' },
    });

    // Map to frontend Platform type format
    const mappedPlatforms = platforms.map(platform => ({
      id: platform.id,
      name: platform.name,
      status: platform.status === PlatformStatus.ACTIVE ? 'active' as const : 'disabled' as const,
      lastUpdated: platform.updatedAt.toISOString().split('T')[0],
    }));

    return NextResponse.json({ platforms: mappedPlatforms });
  } catch (error) {
    console.error('Get platforms error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// POST create platform (admin only)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, status, userId } = body;

    // Validate input
    if (!name) {
      return NextResponse.json(
        { error: 'Platform name is required' },
        { status: 400 }
      );
    }

    // Check authentication and admin role
    const user = await getAuthenticatedUserFromId(userId);
    if (!user) {
      return unauthorizedResponse();
    }

    if (!requireAdmin(user)) {
      return forbiddenResponse();
    }

    // Validate status
    const validStatus = status === 'active' ? PlatformStatus.ACTIVE : PlatformStatus.DISABLED;

    // Check if platform already exists
    const existingPlatform = await prisma.platform.findUnique({
      where: { name },
    });

    if (existingPlatform) {
      return NextResponse.json(
        { error: 'Platform with this name already exists' },
        { status: 409 }
      );
    }

    // Create platform
    const platform = await prisma.platform.create({
      data: {
        name,
        status: validStatus,
      },
    });

    // Return platform data
    return NextResponse.json({
      platform: {
        id: platform.id,
        name: platform.name,
        status: platform.status === PlatformStatus.ACTIVE ? 'active' as const : 'disabled' as const,
        lastUpdated: platform.updatedAt.toISOString().split('T')[0],
      },
    }, { status: 201 });
  } catch (error) {
    console.error('Create platform error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

