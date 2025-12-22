import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';

// PATCH approve user
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    // Check if user exists
    const user = await prisma.user.findUnique({
      where: { id },
    });

    if (!user) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    // Update approval status
    const updatedUser = await prisma.user.update({
      where: { id },
      data: { isApproved: true },
    });

    // Return updated user data
    return NextResponse.json({
      user: {
        id: updatedUser.id,
        name: updatedUser.username,
        email: `${updatedUser.username}@clubem.com`,
        role: updatedUser.role.toLowerCase() as 'admin' | 'staff',
        status: 'active' as const,
        createdAt: updatedUser.createdAt.toISOString().split('T')[0],
        isApproved: updatedUser.isApproved,
      },
    });
  } catch (error) {
    console.error('Approve user error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

