import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';
import { getAuthenticatedUserFromId, unauthorizedResponse } from '@/app/api/auth/helpers';
import { OrderStatus } from '@prisma/client';

const ENGINE_URL = process.env.ENGINE_URL || 'http://localhost:5000';
const ENGINE_V2_URL = process.env.ENGINE_V2_URL || 'http://localhost:5000';

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

    // Create Order in PROCESSING status immediately
    const order = await prisma.order.create({
      data: {
        status: OrderStatus.PROCESSING,
        groupOrderNumber: `PENDING-${Date.now().toString().slice(-6)}`,
        data: {
          originalFiles: files.map(f => f.name)
        },
        platformId: platformId,
        createdById: userId,
      },
    });

    // Process in background
    // We convert files to buffers to ensure they are available in background
    const filesData = await Promise.all(files.map(async (file) => ({
      name: file.name,
      type: file.type,
      buffer: Buffer.from(await file.arrayBuffer())
    })));

    processOrderInBackground(order.id, platformId, filesData).catch(err => {
      console.error(`Background processing failed for order ${order.id}:`, err);
    });

    return NextResponse.json({
      orderId: order.id,
      status: order.status,
    }, { status: 201 });

  } catch (error: any) {
    console.error('Create order error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function processOrderInBackground(orderId: string, platformId: string, filesData: any[]) {
  try {
    // Prepare FormData for engines
    const engineFormData = new FormData();
    for (const file of filesData) {
      const blob = new Blob([file.buffer], { type: file.type });
      engineFormData.append('files', blob, file.name);
    }

    // 1. Try Engine V2 (Sync)
    try {
      console.log(`[Background] Attempting Engine V2 extraction for order ${orderId}...`);
      const v2Response = await fetch(`${ENGINE_V2_URL}/api/extract`, {
        method: 'POST',
        body: engineFormData,
      });

      if (v2Response.ok) {
        const v2Result = await v2Response.json();
        console.log(`[Background] Engine V2 success for order ${orderId}:`, v2Result.workflow_id);

        if (v2Result.extracted_data && v2Result.extracted_data.length > 0) {
          const firstResult = v2Result.extracted_data[0];

          if (firstResult) {
            const outputData = {
              main_order_information: firstResult.order_level || {},
              individual_orders: (firstResult.individual_orders || []).map((item: any) => ({
                ...item,
                modifications: typeof item.modifications === 'string'
                  ? item.modifications.split(',').map((s: string) => s.trim()).filter(Boolean)
                  : (item.modifications || [])
              })),
              group_orders: [{
                group_order_number: firstResult.order_level?.group_order_number,
                pick_time: firstResult.order_level?.group_order_pick_time
              }],
              originalFiles: filesData.map(f => f.name)
            };

            const groupOrderNumber = firstResult.order_level?.group_order_number ||
              `PENDING-${Date.now().toString().slice(-6)}`;

            await prisma.order.update({
              where: { id: orderId },
              data: {
                status: OrderStatus.NEEDS_MANUAL_REVIEW,
                groupOrderNumber: groupOrderNumber,
                data: outputData as any,
                engineJobId: `v2_${v2Result.workflow_id}`,
              },
            });
            return;
          }
        }
      }
    } catch (error) {
      console.error(`[Background] Engine V2 error for order ${orderId}:`, error);
    }

    // 2. Fallback to Engine V1 (Async)
    console.log(`[Background] Falling back to Engine V1 for order ${orderId}...`);
    const engineResponse = await fetch(`${ENGINE_URL}/api/parse`, {
      method: 'POST',
      body: engineFormData,
    });

    if (!engineResponse.ok) {
      const errorData = await engineResponse.json();
      throw new Error(errorData.error || 'Failed to connect to extraction engine');
    }

    const { job_id } = await engineResponse.json();
    await prisma.order.update({
      where: { id: orderId },
      data: {
        engineJobId: job_id,
      },
    });

  } catch (error: any) {
    console.error(`[Background] Processing failed for order ${orderId}:`, error);
    await prisma.order.update({
      where: { id: orderId },
      data: { status: OrderStatus.FAILED },
    });
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('userId');

    console.log('GET /api/orders - userId:', userId);

    if (!userId) {
      console.log('GET /api/orders - No userId provided');
      return unauthorizedResponse('User ID is required');
    }

    const user = await getAuthenticatedUserFromId(userId);
    if (!user) {
      console.log('GET /api/orders - User not found or not approved:', userId);
      return unauthorizedResponse('Invalid or unapproved user');
    }

    console.log('GET /api/orders - User authenticated:', user.email, 'role:', user.role);

    const orders = await prisma.order.findMany({
      where: user.role === 'admin' ? {} : { createdById: userId },
      include: {
        platform: true,
        createdBy: {
          select: {
            email: true,
            name: true,
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
                  groupOrderNumber: outputData.group_orders?.[0]?.group_order_number || order.groupOrderNumber,
                  data: {
                    ...outputData,
                    originalFiles: (order.data as any)?.originalFiles || []
                  },
                },
                include: {
                  platform: true,
                  createdBy: {
                    select: {
                      email: true,
                      name: true,
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
                      email: true,
                      name: true,
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
  } catch (error: any) {
    console.error('Get orders error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
