'use client';

import React, { use, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Card, CardHeader } from '@/app/components/ui/Card';
import { Table, TableCard } from '@/app/components/ui/Table';
import { Badge, getStatusBadgeVariant, formatStatus } from '@/app/components/ui/Badge';
import { Button } from '@/app/components/ui/Button';
import { useAuth } from '@/app/context/AuthContext';
import { DownloadIcon, SheetIcon, RefreshIcon } from '@/app/components/icons';
import { toast } from 'react-hot-toast';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function StaffOrderDetailPage({ params }: PageProps) {
  const router = useRouter();
  const { user } = useAuth();
  const { id } = use(params);

  const [order, setOrder] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchOrder = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    else setIsRefreshing(true);

    try {
      const url = `/api/orders/${id}?userId=${user?.id}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch order details');
      }
      const data = await response.json();
      setOrder(data.order);
      setError(null);
    } catch (err: any) {
      console.error('Fetch order error:', err);
      setError(err.message || 'An error occurred while fetching order details');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [id, user?.id]);

  useEffect(() => {
    if (user?.id) {
      fetchOrder();
    }
  }, [user?.id, fetchOrder]);

  // Polling if processing
  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (order && order.status === 'PROCESSING') {
      interval = setInterval(() => {
        fetchOrder(false);
      }, 5000); // Poll every 5 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [order?.status, fetchOrder]);

  const handleGoogleSheets = async () => {
    if (!user?.id || !order) return;

    try {
      toast.loading('Preparing Google Sheet...', { id: 'gsheet' });

      // 1. Check if Google OAuth is configured
      const configRes = await fetch('/api/integrations/google/config-check');
      const { isConfigured } = await configRes.json();

      if (isConfigured) {
        // Use OAuth automated flow
        const response = await fetch(`/api/orders/${id}/export?userId=${user.id}&format=gsheet`);

        if (response.ok) {
          const { url } = await response.json();
          window.open(url, '_blank');
          toast.success('Google Sheet created successfully!', { id: 'gsheet' });
          return;
        }

        // If OAuth fails but was configured (e.g. 401 Unauthorized), we could fall back or show error
        // Let's check for 401 specifically to guide the user
        if (response.status === 401) {
          toast.error('Google account not connected. Please connect it in Settings.', { id: 'gsheet' });
          return;
        }
      }

      // 2. Fallback to Clipboard + sheets.new (Ctrl+V)
      // This happens if not configured OR if OAuth API failed for non-auth reasons
      const response = await fetch(`/api/orders/${id}/export?userId=${user.id}&format=csv`);
      if (!response.ok) throw new Error('Failed to fetch order data');

      const csvData = await response.text();

      // Convert CSV to TSV for easy pasting into Google Sheets
      const tsvData = csvData.split('\n').map(line => {
        return line.split(',').map(cell => {
          return cell.replace(/^"(.*)"$/, '$1').replace(/""/g, '"');
        }).join('\t');
      }).join('\n');

      await navigator.clipboard.writeText(tsvData);
      window.open('https://sheets.new', '_blank');

      toast.success('Data copied! Just press Ctrl+V in the new sheet.', { id: 'gsheet' });
    } catch (err: any) {
      console.error('Google Sheets error:', err);
      toast.error(err.message || 'Failed to create Google Sheet', { id: 'gsheet' });
    }
  };

  const handleExport = async (format: 'csv' | 'excel') => {
    if (!user?.id) return;

    try {
      const response = await fetch(`/api/orders/${id}/export?userId=${user.id}&format=${format}`);
      if (!response.ok) throw new Error(`Failed to export to ${format}`);

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `order_${order.groupOrderNumber}.${format === 'csv' ? 'csv' : 'xlsx'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`Exported to ${format.toUpperCase()}`);
    } catch (err: any) {
      console.error(`Export ${format} error:`, err);
      toast.error(err.message || `Failed to export to ${format}`);
    }
  };

  const handleAcceptOrder = async () => {
    try {
      const response = await fetch(`/api/orders/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: user?.id,
          status: 'READY_TO_SEND'
        }),
      });

      if (!response.ok) throw new Error('Failed to accept order');

      toast.success('Order accepted and ready to send!');
      fetchOrder(false);
    } catch (err: any) {
      console.error('Accept order error:', err);
      toast.error(err.message || 'Failed to accept order');
    }
  };

  if (loading) {
    return (
      <PageContainer title="Loading Order...">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-600"></div>
        </div>
      </PageContainer>
    );
  }

  if (error || !order) {
    return (
      <PageContainer title="Order Not Found">
        <Card>
          <p className="text-slate-600">{error || 'The requested order could not be found.'}</p>
          <Button
            variant="secondary"
            className="mt-4"
            onClick={() => router.push('/app/orders')}
          >
            Back to Orders
          </Button>
        </Card>
      </PageContainer>
    );
  }

  // Extract data from engine output structure
  const orderData = order.data?.main_order_information || {};
  const guestItems = order.data?.individual_orders || [];

  const guestColumns = [
    {
      key: 'guest_name',
      header: 'Guest Name',
      render: (item: any) => (
        <span className="font-medium text-slate-900">{item.guest_name || '—'}</span>
      ),
    },
    {
      key: 'item_name',
      header: 'Item',
      render: (item: any) => (
        <span className="text-slate-900">{item.item_name || '—'}</span>
      ),
    },
    {
      key: 'modifications',
      header: 'Modifications',
      render: (item: any) => (
        <span className="text-slate-600">
          {Array.isArray(item.modifications) ? item.modifications.join(', ') : item.modifications || '—'}
        </span>
      ),
    },
    {
      key: 'comments',
      header: 'Comments',
      render: (item: any) => (
        <span className="text-slate-600">{item.comments || '—'}</span>
      ),
    },
  ];

  return (
    <PageContainer
      title={`Order ${order.groupOrderNumber}`}
      description={`${order.platform?.name} - ${new Date(order.createdAt).toLocaleDateString()}`}
      action={
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => fetchOrder(false)}
            disabled={isRefreshing}
            leftIcon={<RefreshIcon className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />}
          >
            Refresh
          </Button>
          <Button
            variant="secondary"
            onClick={() => router.push('/app/orders')}
          >
            Back to Orders
          </Button>
        </div>
      }
    >
      {/* Order Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <Card className="lg:col-span-2">
          <CardHeader title="Order Information" />
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-slate-500">Business Client</p>
              <p className="font-medium text-slate-900">{orderData.business_client || '—'}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Client Name</p>
              <p className="font-medium text-slate-900">{orderData.client_name || '—'}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Group Order Number</p>
              <p className="font-mono text-slate-900">{order.groupOrderNumber}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Requested Date</p>
              <p className="font-medium text-slate-900">{orderData.requested_pick_up_date || '—'}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Pickup/Delivery Time</p>
              <p className="font-medium text-slate-900">{orderData.requested_pick_up_time || '—'}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Delivery Mode</p>
              <p className="font-medium text-slate-900 capitalize">{orderData.delivery || '—'}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Number of Guests</p>
              <p className="font-medium text-slate-900">{orderData.number_of_guests || '—'}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Order Subtotal</p>
              <p className="font-medium text-slate-900">{orderData.order_subtotal || '—'}</p>
            </div>
            <div className="col-span-2">
              <p className="text-sm text-slate-500">Client Information</p>
              <p className="font-medium text-slate-900">{orderData.client_information || '—'}</p>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="Status" />
          <div className="space-y-4">
            <div>
              <p className="text-sm text-slate-500 mb-2">Current Status</p>
              <Badge variant={getStatusBadgeVariant(order.status.toLowerCase() as any)} className="text-sm">
                {formatStatus(order.status.toLowerCase() as any)}
              </Badge>
            </div>

            <div>
              <p className="text-sm text-slate-500 mb-2">Created</p>
              <p className="font-medium text-slate-900">{new Date(order.createdAt).toLocaleString()}</p>
            </div>

            <div>
              <p className="text-sm text-slate-500 mb-2">Platform</p>
              <p className="font-medium text-slate-900">{order.platform?.name}</p>
            </div>

            {order.status === 'PROCESSING' && (
              <div className="p-3 bg-violet-50 rounded-md">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-2 h-2 bg-violet-500 rounded-full animate-pulse"></div>
                  <p className="text-sm font-medium text-violet-700">Processing...</p>
                </div>
                <p className="text-xs text-violet-600">
                  Our engine is extracting data from your PDF. This usually takes 10-20 seconds.
                </p>
              </div>
            )}

            {order.status === 'NEEDS_MANUAL_REVIEW' && (
              <div className="space-y-3">
                <div className="p-3 bg-amber-50 rounded-md">
                  <p className="text-sm text-amber-700">
                    This order needs manual review. Please verify the extracted data below.
                  </p>
                </div>
                <Button
                  variant="primary"
                  className="w-full"
                  onClick={handleAcceptOrder}
                >
                  Accept & Mark Ready
                </Button>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Export Options - Only show when order is ready or sent */}
      {(order.status === 'READY_TO_SEND' || order.status === 'SENT') && (
        <Card className="mb-6">
          <CardHeader title="Export Options" />
          <div className="flex flex-wrap gap-3">
            <Button
              variant="secondary"
              leftIcon={<SheetIcon className="w-4 h-4" />}
              onClick={handleGoogleSheets}
            >
              Open in Google Sheets
            </Button>
            <Button
              variant="secondary"
              leftIcon={<DownloadIcon className="w-4 h-4" />}
              onClick={() => handleExport('excel')}
            >
              Export to Excel
            </Button>
            <Button
              variant="secondary"
              leftIcon={<DownloadIcon className="w-4 h-4" />}
              onClick={() => handleExport('csv')}
            >
              Export to CSV
            </Button>
          </div>
        </Card>
      )}

      {/* Guest Items */}
      <TableCard
        title="Guest Items"
        description={`${guestItems.length} items in this order`}
      >
        <Table
          columns={guestColumns}
          data={guestItems}
          keyExtractor={(item: any, index: number) => item.id || `item-${index}`}
          emptyMessage={order.status === 'PROCESSING' ? 'Processing items...' : 'No items found in this order'}
        />
      </TableCard>
    </PageContainer>
  );
}
