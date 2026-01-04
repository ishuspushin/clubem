import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';
import bcrypt from 'bcrypt';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { email, code, newPassword } = body;

        if (!email || !code || !newPassword) {
            return NextResponse.json(
                { error: 'Email, code, and new password are required' },
                { status: 400 }
            );
        }

        if (newPassword.length < 6) {
             return NextResponse.json(
                { error: 'Password must be at least 6 characters long' },
                { status: 400 }
            );
        }

        const user = await prisma.user.findUnique({
            where: { email },
        });

        if (!user) {
            return NextResponse.json(
                { error: 'Invalid request' },
                { status: 400 }
            );
        }

        if (
            !user.resetPasswordToken ||
            user.resetPasswordToken !== code ||
            !user.resetPasswordTokenExpiry ||
            user.resetPasswordTokenExpiry < new Date()
        ) {
            return NextResponse.json(
                { error: 'Invalid or expired code' },
                { status: 400 }
            );
        }

        // Hash new password
        const saltRounds = parseInt(process.env.BCRYPT_SALT_ROUNDS || '10', 10);
        const hashedPassword = await bcrypt.hash(newPassword, saltRounds);

        // Update user
        await prisma.user.update({
            where: { id: user.id },
            data: {
                password: hashedPassword,
                resetPasswordToken: null,
                resetPasswordTokenExpiry: null,
            },
        });

        return NextResponse.json(
            { message: 'Password reset successfully' },
            { status: 200 }
        );

    } catch (error) {
        console.error('Reset password error:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}
