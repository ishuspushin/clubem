'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Table, TableCard } from '@/app/components/ui/Table';
import { Badge, getStatusBadgeVariant, formatStatus } from '@/app/components/ui/Badge';
import { Button } from '@/app/components/ui/Button';
import { Input } from '@/app/components/ui/Input';
import { Select } from '@/app/components/ui/Select';
import { useAuth } from '@/app/context/AuthContext';
import { EyeIcon, DownloadIcon, RefreshIcon } from '@/app/components/icons';
import { toast } from 'react-hot-toast';

export default function StaffOrdersPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const fetchOrders = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    else setIsRefreshing(true);

    try {
      const response = await fetch(`/api/orders?userId=${user?.id}`);
      if (!response.ok) {
        throw new Error('Failed to fetch orders');
      }
      const data = await response.json();
      setOrders(data.orders || []);
    } catch (error: any) {
      console.error('Fetch orders error:', error);
      toast.error(error.message || 'Failed to load orders');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [user?.id]);

  useEffect(() => {
    if (user?.id) {
      fetchOrders();
    }
  }, [user?.id, fetchOrders]);

  const filteredOrders = orders.filter(order => {
    const orderData = order.data?.main_order_information || {};
    const clientName = orderData.client_name || '';
    const businessClient = orderData.business_client || '';
    const orderId = order.id || '';
    const groupOrderNumber = order.groupOrderNumber || '';

    const matchesSearch =
      clientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      businessClient.toLowerCase().includes(searchQuery.toLowerCase()) ||
      orderId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      groupOrderNumber.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const columns = [
    {
      key: 'clientName',
      header: 'Client',
      render: (order: any) => {
        const orderData = order.data?.main_order_information || {};
        return (
          <div>
            <p className="font-medium text-slate-900">{orderData.client_name || 'Processing...'}</p>
            <p className="text-sm text-slate-500">{orderData.business_client || order.platform?.name}</p>
          </div>
        );
      },
    },
    {
      key: 'requestedDate',
      header: 'Requested Date',
      render: (order: any) => {
        const orderData = order.data?.main_order_information || {};
        return orderData.requested_pick_up_date || '—';
      }
    },
    {
      key: 'numberOfGuests',
      header: 'Guests',
      render: (order: any) => {
        const orderData = order.data?.main_order_information || {};
        return <span className="font-medium">{orderData.number_of_guests || '—'}</span>;
      },
    },
    {
      key: 'status',
      header: 'Status',
      render: (order: any) => (
        <Badge variant={getStatusBadgeVariant(order.status.toLowerCase() as any)}>
          {formatStatus(order.status.toLowerCase() as any)}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (order: any) => (
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/app/orders/${order.id}`)}
            leftIcon={<EyeIcon className="w-4 h-4" />}
          >
            View
          </Button>
          {(order.status === 'SENT' || order.status === 'READY_TO_SEND') && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toast.success('Exporting...')}
              leftIcon={<DownloadIcon className="w-4 h-4" />}
            >
              Export
            </Button>
          )}
        </div>
      ),
    },
  ];

  const statusOptions = [
    { value: 'all', label: 'All Statuses' },
    { value: 'PROCESSING', label: 'Processing' },
    { value: 'NEEDS_MANUAL_REVIEW', label: 'Needs Review' },
    { value: 'READY_TO_SEND', label: 'Ready to Send' },
    { value: 'SENT', label: 'Sent' },
    { value: 'FAILED', label: 'Failed' },
  ];

  return (
    <PageContainer
      title="My Orders"
      description="View and track orders from your uploads"
      action={
        <Button
          variant="ghost"
          size="sm"
          onClick={() => fetchOrders(false)}
          disabled={isRefreshing}
          leftIcon={<RefreshIcon className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />}
        >
          Refresh
        </Button>
      }
    >
      {/* Filters */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1 max-w-md">
          <Input
            placeholder="Search by client or order ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="w-full sm:w-48">
          <Select
            options={statusOptions}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          />
        </div>
      </div>

      <TableCard>
        <Table
          columns={columns}
          data={filteredOrders}
          keyExtractor={(item, index) => item.id || `order-${index}`}
          emptyMessage={loading ? 'Loading orders...' : 'No orders found'}
        />
      </TableCard>
    </PageContainer>
  );
}

