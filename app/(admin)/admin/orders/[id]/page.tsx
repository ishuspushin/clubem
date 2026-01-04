'use client';

import React, { useState, useEffect, useCallback, use } from 'react';
import { useRouter } from 'next/navigation';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Card, CardHeader } from '@/app/components/ui/Card';
import { Table, TableCard } from '@/app/components/ui/Table';
import { Badge, getStatusBadgeVariant, formatStatus } from '@/app/components/ui/Badge';
import { Button } from '@/app/components/ui/Button';
import { useAuth } from '@/app/context/AuthContext';
import { SendIcon, ReviewIcon, DownloadIcon, SheetIcon, RefreshIcon, CheckIcon } from '@/app/components/icons';
import { toast } from 'react-hot-toast';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function AdminOrderDetailPage({ params }: PageProps) {
  const router = useRouter();
  const { user } = useAuth();
  const { id } = use(params);

  const [order, setOrder] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const fetchOrder = useCallback(async (showLoading = true) => {
    if (!user?.id) return;
    if (showLoading) setLoading(true);
    else setIsRefreshing(true);

    try {
      const response = await fetch(`/api/orders/${id}?userId=${user.id}`);
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
    fetchOrder();
  }, [fetchOrder]);

  const handleUpdateStatus = async (newStatus: string) => {
    try {
      setIsSending(true);
      const response = await fetch(`/api/orders/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: user?.id,
          status: newStatus
        }),
      });

      if (!response.ok) throw new Error('Failed to update order status');

      toast.success(`Order status updated to ${formatStatus(newStatus as any)}`);
      fetchOrder(false);
    } catch (err: any) {
      console.error('Update status error:', err);
      toast.error(err.message || 'Failed to update order');
    } finally {
      setIsSending(false);
    }
  };

  const handleRetryOrder = async () => {
    try {
      setIsSending(true);
      const response = await fetch(`/api/orders/${id}/retry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: user?.id }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to initiate retry');
      }

      toast.success('Retry initiated!');
      fetchOrder(false);
    } catch (err: any) {
      console.error('Retry order error:', err);
      toast.error(err.message || 'Failed to initiate retry');
    } finally {
      setIsSending(false);
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
            onClick={() => router.push('/admin/orders')}
          >
            Back to Orders
          </Button>
        </Card>
      </PageContainer>
    );
  }

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
        if (response.status === 401) {
          toast.error('Google account not connected. Please connect it in Settings.', { id: 'gsheet' });
          return;
        }
      }

      // 2. Fallback to Clipboard + sheets.new (Ctrl+V)
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
            onClick={() => router.push('/admin/orders')}
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
          <CardHeader title="Status & Actions" />
          <div className="space-y-4">
            <div>
              <p className="text-sm text-slate-500 mb-2">Current Status</p>
              <Badge variant={getStatusBadgeVariant(order.status.toLowerCase() as any)} className="text-sm">
                {formatStatus(order.status.toLowerCase() as any)}
              </Badge>
            </div>

            <div>
              <p className="text-sm text-slate-500 mb-2">Uploaded By</p>
              <p className="font-medium text-slate-900">{order.createdBy?.name || order.createdBy?.email || 'System'}</p>
              <p className="text-xs text-slate-500">{new Date(order.createdAt).toLocaleString()}</p>
            </div>

            <div className="pt-4 border-t border-slate-200 space-y-2">
              {order.status === 'NEEDS_MANUAL_REVIEW' && (
                <>
                  <Button
                    variant="secondary"
                    className="w-full"
                    leftIcon={<ReviewIcon className="w-4 h-4" />}
                    onClick={() => router.push(`/admin/review?orderId=${order.id}`)}
                  >
                    Review Order
                  </Button>
                  <Button
                    variant="primary"
                    className="w-full"
                    leftIcon={<CheckIcon className="w-4 h-4" />}
                    onClick={() => handleUpdateStatus('CONFIRMED')}
                    isLoading={isSending}
                  >
                    Confirm Order
                  </Button>
                </>
              )}
              {order.status === 'CONFIRMED' && (
                <div className="flex items-center justify-center gap-2 text-emerald-600 font-medium px-4 py-2 bg-emerald-50 rounded-md">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Confirmed
                </div>
              )}
              {order.status === 'FAILED' && (
                <div className="space-y-3">
                  <div className="p-3 bg-red-50 rounded-md">
                    <p className="text-sm text-red-700 font-medium">Extraction Failed</p>
                    <p className="text-xs text-red-600">The engine was unable to parse this file. You can try retrying or contact support.</p>
                  </div>
                  <Button
                    variant="primary"
                    className="w-full"
                    leftIcon={<RefreshIcon className="w-4 h-4" />}
                    onClick={handleRetryOrder}
                    isLoading={isSending}
                  >
                    Retry Extraction
                  </Button>
                </div>
              )}
              {order.status !== 'NEEDS_MANUAL_REVIEW' && order.status !== 'CONFIRMED' && order.status !== 'FAILED' && (
                <div className="text-slate-500 font-medium px-4 py-2 text-center">
                  Status: {formatStatus(order.status.toLowerCase() as any)}
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>

      {/* Export Options - Only show when order is confirmed */}
      {order.status === 'CONFIRMED' && (
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
          keyExtractor={(item: any, index: number) => `${order.id}-guest-${index}`}
          emptyMessage="No items in this order"
        />
      </TableCard>
    </PageContainer>
  );
}

