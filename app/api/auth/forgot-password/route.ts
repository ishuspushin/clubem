import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';
import { sendEmail } from '@/src/utils/email';
import crypto from 'crypto';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { email } = body;

        if (!email) {
            return NextResponse.json(
                { error: 'Email is required' },
                { status: 400 }
            );
        }

        const user = await prisma.user.findUnique({
            where: { email },
        });

        if (!user) {
            // Do not reveal if user exists
            return NextResponse.json(
                { message: 'If an account exists with this email, a reset code has been sent.' },
                { status: 200 }
            );
        }

        // Generate reset token (6 digit code)
        const resetToken = crypto.randomInt(100000, 999999).toString();
        const tokenExpiry = new Date(Date.now() + 15 * 60 * 1000); // 15 minutes

        // Save token to user
        await prisma.user.update({
            where: { id: user.id },
            data: {
                resetPasswordToken: resetToken,
                resetPasswordTokenExpiry: tokenExpiry,
            },
        });

        // Send email
        const emailSent = await sendEmail(
            email,
            'Password Reset Code',
            `Your password reset code is: ${resetToken}. It expires in 15 minutes.`,
            `<p>Your password reset code is: <strong>${resetToken}</strong></p><p>It expires in 15 minutes.</p>`
        );

        if (!emailSent) {
             return NextResponse.json(
                { error: 'Failed to send email' },
                { status: 500 }
            );
        }

        return NextResponse.json(
            { message: 'If an account exists with this email, a reset code has been sent.' },
            { status: 200 }
        );

    } catch (error) {
        console.error('Forgot password error:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}
