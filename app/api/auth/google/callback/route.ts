import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get('code');
  const userId = searchParams.get('state');
  const error = searchParams.get('error');

  if (error) {
    return NextResponse.redirect(`${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/admin/settings?error=google_auth_failed`);
  }

  if (!code || !userId) {
    return NextResponse.json({ error: 'Invalid callback parameters' }, { status: 400 });
  }

  const clientId = process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
  const redirectUri = `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/api/auth/google/callback`;

  try {
    const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        code,
        client_id: clientId!,
        client_secret: clientSecret!,
        redirect_uri: redirectUri,
        grant_type: 'authorization_code',
      }),
    });

    if (!tokenResponse.ok) {
      const errorData = await tokenResponse.json();
      console.error('Token exchange error:', errorData);
      return NextResponse.redirect(`${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/admin/settings?error=token_exchange_failed`);
    }

    const tokens = await tokenResponse.json();

    // Save tokens to user
    await prisma.user.update({
      where: { id: userId },
      data: {
        googleAccessToken: tokens.access_token,
        googleRefreshToken: tokens.refresh_token || undefined, // Only provided on first auth
        googleTokenExpiry: new Date(Date.now() + tokens.expires_in * 1000),
      },
    });

    // Determine where to redirect based on user role (we can fetch user role here)
    const user = await prisma.user.findUnique({ where: { id: userId } });
    const redirectPath = user?.role.toLowerCase() === 'admin' ? '/admin/settings' : '/app/settings';

    return NextResponse.redirect(`${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}${redirectPath}?success=google_connected`);
  } catch (err) {
    console.error('Google callback error:', err);
    return NextResponse.redirect(`${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/admin/settings?error=internal_server_error`);
  }
}
