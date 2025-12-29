import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';
import { getAuthenticatedUserFromId, unauthorizedResponse } from '@/app/api/auth/helpers';
import { OrderStatus } from '@prisma/client';

const ENGINE_URL = process.env.ENGINE_URL || 'http://localhost:5000';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('userId');

    if (!userId) {
      return unauthorizedResponse('User ID is required');
    }

    const user = await getAuthenticatedUserFromId(userId);
    if (!user) {
      return unauthorizedResponse('Invalid or unapproved user');
    }

    let order = await prisma.order.findUnique({
      where: { id },
      include: {
        platform: true,
        createdBy: {
          select: {
            username: true,
          }
        }
      }
    });

    if (!order) {
      return NextResponse.json({ error: 'Order not found' }, { status: 404 });
    }

    // If order is still processing, check the engine
    if (order.status === OrderStatus.PROCESSING && order.engineJobId) {
      try {
        const engineResponse = await fetch(`${ENGINE_URL}/api/jobs/${order.engineJobId}`);
        if (engineResponse.ok) {
          const job = await engineResponse.json();

          if (job.status === 'completed' && job.result?.files?.length > 0) {
            // Take the first file's output as the primary order data for now
            // In a more complex scenario, we might merge multiple files
            const firstResult = job.result.files[0];
            const outputData = firstResult.output || {};

            // Update order with results
            order = await prisma.order.update({
              where: { id },
              data: {
                status: OrderStatus.NEEDS_MANUAL_REVIEW,
                groupOrderNumber: outputData.order_info?.order_number || order.groupOrderNumber,
                data: outputData,
              },
              include: {
                platform: true,
                createdBy: {
                  select: {
                    username: true,
                  }
                }
              }
            });
          } else if (job.status === 'failed') {
            order = await prisma.order.update({
              where: { id },
              data: {
                status: OrderStatus.FAILED,
              },
              include: {
                platform: true,
                createdBy: {
                  select: {
                    username: true,
                  }
                }
              }
            });
          }
        }
      } catch (err) {
        console.error('Error checking engine job status:', err);
      }
    }

    return NextResponse.json({ order });
  } catch (error) {
    console.error('Get order error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();
    const { status, data, userId } = body;

    if (!userId) {
      return unauthorizedResponse('User ID is required');
    }

    const user = await getAuthenticatedUserFromId(userId);
    if (!user) {
      return unauthorizedResponse('Invalid or unapproved user');
    }

    // Only admins or the creator can update orders
    const existingOrder = await prisma.order.findUnique({ where: { id } });
    if (!existingOrder) {
      return NextResponse.json({ error: 'Order not found' }, { status: 404 });
    }

    if (user.role !== 'admin' && existingOrder.createdById !== userId) {
      return NextResponse.json({ error: 'Permission denied' }, { status: 403 });
    }

    const updatedOrder = await prisma.order.update({
      where: { id },
      data: {
        ...(status && { status: status as OrderStatus }),
        ...(data && { data }),
        ...(data && { manuallyEdited: true }),
        ...(data && user.role === 'admin' && { reviewedById: userId }),
      },
      include: {
        platform: true,
        createdBy: {
          select: {
            username: true,
          }
        }
      }
    });

    // If the order is being accepted (moving from NEEDS_MANUAL_REVIEW to READY_TO_SEND),
    // delete the files from the engine.
    if (
      status === OrderStatus.READY_TO_SEND &&
      existingOrder.status === OrderStatus.NEEDS_MANUAL_REVIEW &&
      existingOrder.engineJobId
    ) {
      try {
        await fetch(`${ENGINE_URL}/api/jobs/${existingOrder.engineJobId}`, {
          method: 'DELETE',
        });
      } catch (err) {
        console.error('Failed to delete engine job files:', err);
        // We don't fail the request if deletion fails, but we log it
      }
    }

    return NextResponse.json({ order: updatedOrder });
  } catch (error) {
    console.error('Update order error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
