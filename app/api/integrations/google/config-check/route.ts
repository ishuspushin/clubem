import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const isConfigured = !!(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET);
  
  return NextResponse.json({
    isConfigured,
    // We don't want to expose the actual credentials, just whether they exist
  });
}
