import { UserRole, Status, FieldLevel, FieldRenderType, ValueType } from "@prisma/client";
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
    const platformNames = [
        'Grubhub',
        'Forkable',
        'Sharebite',
        'CaterCow',
        'EzCater',
        'ClubFeast',
        'Hungry',
    ]

    const seededPlatforms = []
    for (const name of platformNames) {
        const platform = await prisma.platform.upsert({
            where: { name },
            update: {
                status: Status.ACTIVE,
            },
            create: {
                name,
                status: Status.ACTIVE,
            },
        })
        seededPlatforms.push(platform)
    }

    console.log(`${seededPlatforms.length} platforms seeded successfully`)

    // Seed Sections and Fields (Fields are platform-specific)
    const sectionDefinitions = [
        {
            name: 'Order Information',
            level: FieldLevel.ORDER,
            renderType: FieldRenderType.KEY_VALUE,
            rank: 0,
            fields: [
                { name: 'Business Client', key: 'business_client', value: ValueType.TEXT, rank: 0 },
                { name: 'Client Name', key: 'client_name', value: ValueType.TEXT, rank: 1 },
                { name: 'Group Order Number', key: 'group_order_number', value: ValueType.TEXT, rank: 2 },
                { name: 'Requested Date', key: 'requested_date', value: ValueType.DATE, rank: 3 },
                { name: 'Number of Guests', key: 'number_of_guests', value: ValueType.NUMBER, rank: 4 },
                { name: 'Delivery Mode', key: 'delivery_mode', value: ValueType.TEXT, rank: 5 },
                { name: 'Order Subtotal', key: 'order_subtotal', value: ValueType.NUMBER, rank: 6 },
                { name: 'Pickup Time', key: 'pickup_time', value: ValueType.TIME, rank: 7 },
            ]
        },
        {
            name: 'Guest Items',
            level: FieldLevel.GUEST,
            renderType: FieldRenderType.REPEATED_BLOCK,
            rank: 1,
            fields: [
                { name: 'Guest Name', key: 'guest_name', value: ValueType.TEXT, rank: 0 },
                { name: 'Item Name', key: 'item_name', value: ValueType.TEXT, rank: 1 },
                { name: 'Modifications', key: 'modifications', value: ValueType.TEXT, rank: 2 },
                { name: 'Comments', key: 'comments', value: ValueType.TEXT, rank: 3 },
            ]
        }
    ]

    for (const sectionDef of sectionDefinitions) {
        const { fields, ...sectionInfo } = sectionDef;

        const section = await prisma.section.upsert({
            where: {
                id: (await prisma.section.findFirst({
                    where: { name: sectionInfo.name, level: sectionInfo.level }
                }))?.id || '000000000000000000000000'
            },
            update: {
                ...sectionInfo,
            },
            create: {
                ...sectionInfo,
            },
        });

        // For each platform, create these fields
        for (const platform of seededPlatforms) {
            for (const fieldData of fields) {
                await prisma.fields.upsert({
                    where: {
                        id: (await prisma.fields.findFirst({
                            where: {
                                key: fieldData.key,
                                sectionId: section.id,
                                platformId: platform.id
                            }
                        }))?.id || '000000000000000000000000'
                    },
                    update: {
                        ...fieldData,
                        sectionId: section.id,
                        platformId: platform.id,
                        level: section.level,
                    },
                    create: {
                        ...fieldData,
                        sectionId: section.id,
                        platformId: platform.id,
                        level: section.level,
                    }
                });
            }
        }
    }

    console.log('Sections and platform-specific default fields seeded successfully')
}

main()
    .catch((e) => {
        console.error(e)
        process.exit(1)
    })
    .finally(async () => {
        await prisma.$disconnect()
    })