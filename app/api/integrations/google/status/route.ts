import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const userId = searchParams.get('userId');

  if (!userId) {
    return NextResponse.json({ error: 'User ID is required' }, { status: 400 });
  }

  try {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        googleAccessToken: true,
        googleRefreshToken: true,
        googleTokenExpiry: true,
      },
    });

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    const isConnected = !!user.googleAccessToken;
    const isExpired = user.googleTokenExpiry ? new Date() > user.googleTokenExpiry : true;

    return NextResponse.json({
      isConnected,
      isExpired: isConnected && isExpired && !user.googleRefreshToken,
      expiry: user.googleTokenExpiry,
    });
  } catch (err) {
    console.error('Status check error:', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
