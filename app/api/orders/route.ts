import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';
import { getAuthenticatedUserFromId, unauthorizedResponse } from '@/app/api/auth/helpers';
import { OrderStatus } from '@prisma/client';

const ENGINE_URL = process.env.ENGINE_URL || 'http://localhost:5000';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const userId = formData.get('userId') as string;
    const platformId = formData.get('platformId') as string;
    const files = formData.getAll('files') as File[];

    if (!userId) {
      return unauthorizedResponse('User ID is required');
    }

    const user = await getAuthenticatedUserFromId(userId);
    if (!user) {
      return unauthorizedResponse('Invalid or unapproved user');
    }

    if (!platformId) {
      return NextResponse.json({ error: 'Platform ID is required' }, { status: 400 });
    }

    if (files.length === 0) {
      return NextResponse.json({ error: 'At least one file is required' }, { status: 400 });
    }

    // 1. Send files to Python engine
    const engineFormData = new FormData();
    for (const file of files) {
      engineFormData.append('files', file);
    }

    const engineResponse = await fetch(`${ENGINE_URL}/api/parse`, {
      method: 'POST',
      body: engineFormData,
    });

    if (!engineResponse.ok) {
      const errorData = await engineResponse.json();
      throw new Error(errorData.error || 'Failed to connect to extraction engine');
    }

    const { job_id } = await engineResponse.json();

    // 2. Create Order in Prisma
    const order = await prisma.order.create({
      data: {
        status: OrderStatus.PROCESSING,
        groupOrderNumber: `PENDING-${Date.now().toString().slice(-6)}`, // Temporary until parsed
        data: {}, // Will be filled once engine completes
        engineJobId: job_id,
        platformId: platformId,
        createdById: userId,
      },
    });

    return NextResponse.json({
      orderId: order.id,
      status: order.status,
      engineJobId: job_id
    }, { status: 201 });

  } catch (error: any) {
    console.error('Create order error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('userId');

    if (!userId) {
      return unauthorizedResponse('User ID is required');
    }

    const user = await getAuthenticatedUserFromId(userId);
    if (!user) {
      return unauthorizedResponse('Invalid or unapproved user');
    }

    const orders = await prisma.order.findMany({
      where: user.role === 'admin' ? {} : { createdById: userId },
      include: {
        platform: true,
        createdBy: {
          select: {
            username: true,
          }
        }
      },
      orderBy: { createdAt: 'desc' },
    });

    // Check engine status for any orders that are still PROCESSING
    const updatedOrders = await Promise.all(orders.map(async (order) => {
      if (order.status === OrderStatus.PROCESSING && order.engineJobId) {
        try {
          const engineResponse = await fetch(`${ENGINE_URL}/api/jobs/${order.engineJobId}`);
          if (engineResponse.ok) {
            const job = await engineResponse.json();

            if (job.status === 'completed' && job.result?.files?.length > 0) {
              const firstResult = job.result.files[0];
              const outputData = firstResult.output || {};

              return await prisma.order.update({
                where: { id: order.id },
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
              return await prisma.order.update({
                where: { id: order.id },
                data: { status: OrderStatus.FAILED },
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
          console.error(`Error checking engine job ${order.engineJobId}:`, err);
        }
      }
      return order;
    }));

    return NextResponse.json({ orders: updatedOrders });
  } catch (error) {
    console.error('Get orders error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
