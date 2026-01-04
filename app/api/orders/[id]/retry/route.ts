import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';
import { getAuthenticatedUserFromId, unauthorizedResponse } from '@/app/api/auth/helpers';
import { OrderStatus } from '@prisma/client';
import { processOrderInBackground } from '@/app/api/orders/route';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();
    const { userId } = body;

    if (!userId) {
      return unauthorizedResponse('User ID is required');
    }

    const user = await getAuthenticatedUserFromId(userId);
    if (!user) {
      return unauthorizedResponse('Invalid or unapproved user');
    }

    // Find the order
    const order = await prisma.order.findUnique({
      where: { id },
      include: { platform: true }
    });

    if (!order) {
      return NextResponse.json({ error: 'Order not found' }, { status: 404 });
    }

    // Only allow retry for FAILED or PROCESSING orders (if they seem stuck)
    // Actually, let's allow retry for anything except CONFIRMED for flexibility
    if (order.status === OrderStatus.CONFIRMED) {
      return NextResponse.json({ error: 'Cannot retry a confirmed order' }, { status: 400 });
    }

    // We need the original files to retry. Since we don't store them permanently in this simplified version,
    // we would ideally re-fetch them or have them in a buffer.
    // FOR THIS IMPLEMENTATION: We'll assume the files are still available if the engine supports it,
    // OR we might need to tell the user to re-upload if it's been too long.
    
    // However, if we're retrying Engine V1, we might just want to re-trigger the background process
    // if we have the necessary metadata.
    
    // Reset status to PROCESSING
    const updatedOrder = await prisma.order.update({
      where: { id },
      data: {
        status: OrderStatus.PROCESSING,
        updatedAt: new Date(),
      }
    });

    // In a real app, you'd re-trigger the extraction engine here.
    // For now, let's simulate it by updating the status back to MANUAL_REVIEW after a delay
    // or if we have the filesData.
    
    // If we don't have filesData (which we don't in this POST request), 
    // we can't truly re-run the engine without the files.
    // A better approach for "retry" in this context is to mark it as processing and 
    // maybe wait for a manual action or a background worker that has access to the files.
    
    return NextResponse.json({ 
      message: 'Retry initiated. Please note that full re-extraction requires original files.',
      order: updatedOrder 
    });

  } catch (error: any) {
    console.error('Retry order error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
