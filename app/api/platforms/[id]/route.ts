import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';
import { getAuthenticatedUser, requireAdmin, unauthorizedResponse, forbiddenResponse } from '@/app/api/auth/helpers';
import { PlatformStatus } from '@/generated/prisma/enums';

// PATCH update platform (admin only)
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();
    const { name, status, userId } = body;

    // Check authentication and admin role
    const { getAuthenticatedUserFromId } = await import('@/app/api/auth/helpers');
    const user = await getAuthenticatedUserFromId(userId);
    if (!user) {
      return unauthorizedResponse();
    }

    if (!requireAdmin(user)) {
      return forbiddenResponse();
    }

    // Check if platform exists
    const platform = await prisma.platform.findUnique({
      where: { id },
    });

    if (!platform) {
      return NextResponse.json(
        { error: 'Platform not found' },
        { status: 404 }
      );
    }

    // Prepare update data
    const updateData: { name?: string; status?: PlatformStatus } = {};

    if (name !== undefined) {
      // Check if new name conflicts with existing platform
      if (name !== platform.name) {
        const existingPlatform = await prisma.platform.findUnique({
          where: { name },
        });
        if (existingPlatform) {
          return NextResponse.json(
            { error: 'Platform with this name already exists' },
            { status: 409 }
          );
        }
      }
      updateData.name = name;
    }

    if (status !== undefined) {
      updateData.status = status === 'active' ? PlatformStatus.ACTIVE : PlatformStatus.DISABLED;
    }

    // Update platform
    const updatedPlatform = await prisma.platform.update({
      where: { id },
      data: updateData,
    });

    // Return updated platform data
    return NextResponse.json({
      platform: {
        id: updatedPlatform.id,
        name: updatedPlatform.name,
        status: updatedPlatform.status === PlatformStatus.ACTIVE ? 'active' as const : 'disabled' as const,
        lastUpdated: updatedPlatform.updatedAt.toISOString().split('T')[0],
      },
    });
  } catch (error) {
    console.error('Update platform error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// DELETE platform (admin only)
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json().catch(() => ({}));
    const { userId } = body;

    // Check authentication and admin role
    const { getAuthenticatedUserFromId } = await import('@/app/api/auth/helpers');
    const user = await getAuthenticatedUserFromId(userId);
    if (!user) {
      return unauthorizedResponse();
    }

    if (!requireAdmin(user)) {
      return forbiddenResponse();
    }

    // Check if platform exists
    const platform = await prisma.platform.findUnique({
      where: { id },
    });

    if (!platform) {
      return NextResponse.json(
        { error: 'Platform not found' },
        { status: 404 }
      );
    }

    // Delete platform
    await prisma.platform.delete({
      where: { id },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Delete platform error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

