import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';
import { Parser } from 'json2csv';
import * as XLSX from 'xlsx';
import { getValidGoogleToken, createGoogleSheet } from '@/app/api/integrations/google/utils';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const { searchParams } = new URL(request.url);
        const format = searchParams.get('format') || 'csv';
        const userId = searchParams.get('userId');

        if (!userId) {
            return NextResponse.json({ error: 'User ID is required' }, { status: 400 });
        }

        // Verify user and order
        const user = await prisma.user.findUnique({ where: { id: userId } });
        if (!user) {
            return NextResponse.json({ error: 'User not found' }, { status: 404 });
        }

        const order = await prisma.order.findUnique({
            where: { id },
            include: { platform: true },
        });

        if (!order) {
            return NextResponse.json({ error: 'Order not found' }, { status: 404 });
        }

        // Permission check
        if (user.role.toLowerCase() !== 'admin' && order.createdById !== userId) {
            return NextResponse.json({ error: 'Permission denied' }, { status: 403 });
        }

        const orderData = order.data as any;
        const guestItems = orderData?.individual_orders || [];
        const mainInfo = orderData?.main_order_information || {};

        // Prepare data for export using the specific format from work.pdf/excel_export.py
        const exportData = guestItems.map((item: any) => {
            const modifications = Array.isArray(item.modifications) ? item.modifications : [];
            return {
                'Group Order #': order.groupOrderNumber,
                'Guest Name': item.guest_name || '',
                'Item Name': item.item_name || '',
                'Modification 1': modifications[0] || '',
                'Modification 2': modifications[1] || '',
                'Modification 3': modifications[2] || '',
                'Modification 4': modifications[3] || '',
                'Comments': item.comments || '',
            };
        });

        if (format === 'gsheet') {
            const accessToken = await getValidGoogleToken(userId);
            if (!accessToken) {
                return NextResponse.json({ error: 'Google Account not connected or session expired' }, { status: 401 });
            }

            // Prepare structured data for Google Sheets (Matching excel_export.py format)
            const mainInfoRows = [
                ['Main Order Information'],
                ['Business Client', mainInfo.business_client || ''],
                ['Client Name', mainInfo.client_name || ''],
                ['Client Information', mainInfo.client_information || ''],
                ['Order Subtotal', mainInfo.order_subtotal ? `$${mainInfo.order_subtotal}` : ''],
                ['Requested Pickup Time', mainInfo.requested_pick_up_time || ''],
                ['Requested Pickup Date', mainInfo.requested_pick_up_date || ''],
                ['Number of Guests', mainInfo.number_of_guests || ''],
                ['Delivery', mainInfo.delivery || ''],
                [], // Empty row
            ];

            const groupOrders = orderData?.group_orders || [];
            const groupOrderRows = groupOrders.length > 0 ? [
                ['Group Orders'],
                ['Group Order Number', groupOrders[0].group_order_number || ''],
                ['Pick Time', groupOrders[0].pick_time || ''],
                [], // Empty row
            ] : [];

            const individualOrderHeader = [['Individual Orders']];
            const headers = Object.keys(exportData[0] || {});
            const rows = exportData.map(item => Object.values(item));

            const sheetData = [
                ...mainInfoRows,
                ...groupOrderRows,
                ...individualOrderHeader,
                headers,
                ...rows
            ];

            const sheetUrl = await createGoogleSheet(
                accessToken,
                `Order ${order.groupOrderNumber} - ${mainInfo.business_client || 'Export'}`,
                sheetData
            );

            return NextResponse.json({ url: sheetUrl });
        }

        if (format === 'csv') {
            const parser = new Parser();
            const csv = parser.parse(exportData);

            return new NextResponse(csv, {
                headers: {
                    'Content-Type': 'text/csv',
                    'Content-Disposition': `attachment; filename="order_${order.groupOrderNumber}.csv"`,
                },
            });
        } else if (format === 'excel') {
            const workbook = XLSX.utils.book_new();

            // Prepare structured data for Excel
            const mainInfoRows = [
                ['Main Order Information'],
                ['Business Client', mainInfo.business_client || ''],
                ['Client Name', mainInfo.client_name || ''],
                ['Client Information', mainInfo.client_information || ''],
                ['Order Subtotal', mainInfo.order_subtotal ? `$${mainInfo.order_subtotal}` : ''],
                ['Requested Pickup Time', mainInfo.requested_pick_up_time || ''],
                ['Requested Pickup Date', mainInfo.requested_pick_up_date || ''],
                ['Number of Guests', mainInfo.number_of_guests || ''],
                ['Delivery', mainInfo.delivery || ''],
                [], // Empty row
            ];

            const groupOrders = orderData?.group_orders || [];
            const groupOrderRows = groupOrders.length > 0 ? [
                ['Group Orders'],
                ['Group Order Number', groupOrders[0].group_order_number || ''],
                ['Pick Time', groupOrders[0].pick_time || ''],
                [], // Empty row
            ] : [];

            const individualOrderHeader = [['Individual Orders']];
            const headers = Object.keys(exportData[0] || {});
            const rows = exportData.map(item => Object.values(item));

            const excelData = [
                ...mainInfoRows,
                ...groupOrderRows,
                ...individualOrderHeader,
                headers,
                ...rows
            ];

            const worksheet = XLSX.utils.aoa_to_sheet(excelData);
            XLSX.utils.book_append_sheet(workbook, worksheet, 'Order Export');

            const buf = XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' });

            return new NextResponse(buf, {
                headers: {
                    'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'Content-Disposition': `attachment; filename="order_${order.groupOrderNumber}.xlsx"`,
                },
            });
        }

        return NextResponse.json({ error: 'Invalid format' }, { status: 400 });
    } catch (error) {
        console.error('Export error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
