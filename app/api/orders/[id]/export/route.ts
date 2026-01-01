import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/src/utils/prisma';
import * as XLSX from 'xlsx';
import ExcelJS from 'exceljs';
import { getValidGoogleToken, createGoogleSheet, formatGoogleSheet } from '@/app/api/integrations/google/utils';
import { prepareExportData } from '@/src/utils/export';

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

        const fullSheetData = prepareExportData(order);
        const orderData = order.data as any;
        const mainInfo = orderData?.main_order_information || {};

        if (format === 'gsheet') {
            const accessToken = await getValidGoogleToken(userId);
            if (!accessToken) {
                return NextResponse.json({ error: 'Google Account not connected or session expired' }, { status: 401 });
            }

            const { url, spreadsheetId } = await createGoogleSheet(
                accessToken,
                `Order ${order.groupOrderNumber} - ${mainInfo.business_client || 'Export'}`,
                fullSheetData
            );

            // Format the sheet (indentation and colors)
            const groupOrders = orderData?.group_orders || [];
            const individualOrders = orderData?.individual_orders || [];

            // Calculate where individual orders start
            // Main info (10 rows) + Group info (4 rows if exists)
            const individualOrderStartIndex = 10 + (groupOrders.length > 0 ? 4 : 0);

            await formatGoogleSheet(
                accessToken,
                spreadsheetId,
                fullSheetData,
                individualOrderStartIndex,
                individualOrders.length
            );

            return NextResponse.json({ url });
        }

        if (format === 'csv') {
            const csv = fullSheetData.map(row =>
                row.map(cell => {
                    const s = String(cell ?? '');
                    if (s.includes(',') || s.includes('"') || s.includes('\n')) {
                        return `"${s.replace(/"/g, '""')}"`;
                    }
                    return s;
                }).join(',')
            ).join('\n');

            // Sanitize filename for header
            const safeFilename = `order_${order.groupOrderNumber}`.replace(/[^\x00-\x7F]/g, '_');

            return new NextResponse(new TextEncoder().encode(csv), {
                headers: {
                    'Content-Type': 'text/csv; charset=utf-8',
                    'Content-Disposition': `attachment; filename="${safeFilename}.csv"`,
                },
            });
        } else if (format === 'excel') {
            const workbook = new ExcelJS.Workbook();
            const worksheet = workbook.addWorksheet('Order Export');

            // Set column widths
            worksheet.columns = [
                { width: 30 }, // A
                { width: 30 }, // B
                { width: 30 }, // C
                { width: 50 }, // D
                { width: 50 }, // E
            ];

            const groupOrders = orderData?.group_orders || [];
            const individualOrders = orderData?.individual_orders || [];

            // 1. Main Order Information (Base)
            worksheet.addRow(['Main Order Information']).font = { bold: true, size: 14 };
            worksheet.addRow(['Business Client', mainInfo.business_client || '']);
            worksheet.addRow(['Client Name', mainInfo.client_name || '']);
            worksheet.addRow(['Client Information', mainInfo.client_information || '']);
            worksheet.addRow(['Order Subtotal', mainInfo.order_subtotal ? `$${mainInfo.order_subtotal}` : '']);
            worksheet.addRow(['Requested Pickup Time', mainInfo.requested_pick_up_time || '']);
            worksheet.addRow(['Requested Pickup Date', mainInfo.requested_pick_up_date || '']);
            worksheet.addRow(['Number of Guests', mainInfo.number_of_guests || '']);
            worksheet.addRow(['Delivery', mainInfo.delivery || '']);
            worksheet.addRow([]); // Empty row

            // 2. Group Order Info (1 indentation)
            if (groupOrders.length > 0) {
                const groupRow = worksheet.addRow(['', 'Group Order']);
                groupRow.getCell(2).font = { bold: true, size: 12 };

                worksheet.addRow(['', 'Group Order Number #', groupOrders[0].group_order_number || '']);
                worksheet.addRow(['', 'Group Order # - Pick Time', groupOrders[0].pick_time || '']);
                worksheet.addRow([]); // Empty row
            }

            // 3. Individual Orders (2 indentations + colors)
            const colors = [
                'FFC7CE', // Light Red
                'FFEB9C', // Light Yellow
                'C6EFCE', // Light Green
                'BDD7EE', // Light Blue
                'D9D9D9', // Light Grey
                'E2EFDA', // Pale Green
                'FCE4D6', // Pale Orange
            ];

            individualOrders.forEach((item: any, index: number) => {
                const color = colors[index % colors.length];
                const modifications = Array.isArray(item.modifications) ? item.modifications : [];

                const headerRow = worksheet.addRow(['', '', `Individual Order ${index + 1}`]);
                headerRow.getCell(3).font = { bold: true };

                // Style individual order block with color
                const rows = [
                    worksheet.addRow(['', '', 'Group Order Number #', item.group_order_number || '']),
                    worksheet.addRow(['', '', 'Guest Name', item.guest_name || '']),
                    worksheet.addRow(['', '', 'Item Name', item.item_name || '']),
                    worksheet.addRow(['', '', 'Modifications', ...modifications]),
                    worksheet.addRow(['', '', 'Comments', item.comments || '']),
                ];

                [headerRow, ...rows].forEach(row => {
                    for (let i = 3; i <= 10; i++) {
                        const cell = row.getCell(i);
                        if (cell.value || i <= 5) {
                            cell.fill = {
                                type: 'pattern',
                                pattern: 'solid',
                                fgColor: { argb: color }
                            };
                        }
                    }
                });

                worksheet.addRow([]); // Empty row
            });

            const buffer = await workbook.xlsx.writeBuffer();
            const safeExcelFilename = `order_${order.groupOrderNumber}`.replace(/[^\x00-\x7F]/g, '_');

            // Use Uint8Array to ensure compatibility with NextResponse body
            return new NextResponse(new Uint8Array(buffer as ArrayBuffer), {
                headers: {
                    'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'Content-Disposition': `attachment; filename="${safeExcelFilename}.xlsx"`,
                },
            });
        }

        return NextResponse.json({ error: 'Invalid format' }, { status: 400 });
    } catch (error) {
        console.error('Export error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
