import { UserRole, PlatformStatus } from "@/generated/prisma/enums";
import { prisma } from "@/src/utils/prisma";
import bcrypt from "bcrypt";
import { env } from "@/src/utils/consts";

async function main() {
    const adminUsername = env.admin.username
    const adminPassword = env.admin.password
    const saltRounds = env.bcrypt.saltRounds

    if (!adminUsername || !adminPassword || !saltRounds) {
        console.error('Admin username or password is not set in the environment variables')
        process.exit(1)
    }

    const hashedPassword = await bcrypt.hash(adminPassword, Number(saltRounds))

    await prisma.user.upsert({
        where: { username: adminUsername },
        update: {
            password: hashedPassword,
            role: UserRole.ADMIN,
            isApproved: true, // Admin is always approved
        },
        create: {
            username: adminUsername,
            password: hashedPassword,
            role: UserRole.ADMIN,
            isApproved: true, // Admin is always approved
        },
    })

    console.log('Admin user seeded successfully')

    // Seed platforms
    const platforms = [
        'Grubhub',
        'Forkable',
        'Sharebite',
        'CaterCow',
        'EzCater',
        'ClubFeast',
        'Hungry',
    ]

    for (const platformName of platforms) {
        await prisma.platform.upsert({
            where: { name: platformName },
            update: {
                status: PlatformStatus.ACTIVE,
            },
            create: {
                name: platformName,
                status: PlatformStatus.ACTIVE,
            },
        })
    }

    console.log(`${platforms.length} platforms seeded successfully`)
}

main()
    .catch((e) => {
        console.error(e)
        process.exit(1)
    })
    .finally(async () => {
        await prisma.$disconnect()
    })