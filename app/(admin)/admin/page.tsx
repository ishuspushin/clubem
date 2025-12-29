'use client';

import React, { useState, useEffect } from 'react';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { StatCard, Card } from '@/app/components/ui/Card';
import { Table, TableCard } from '@/app/components/ui/Table';
import { Badge, getStatusBadgeVariant, formatStatus } from '@/app/components/ui/Badge';
import { UploadIcon, OrdersIcon, ReviewIcon, ProcessIcon } from '@/app/components/icons';
import { Order } from '@/app/types';
import Link from 'next/link';
import { useAuth } from '@/app/context/AuthContext';
import { toast } from 'react-hot-toast';

export default function AdminDashboardPage() {
  const { user } = useAuth();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDashboardData() {
      if (!user?.id) return;
      try {
        const response = await fetch(`/api/orders?userId=${user.id}`);
        if (!response.ok) throw new Error('Failed to fetch dashboard data');
        const data = await response.json();
        setOrders(data.orders || []);
      } catch (error: any) {
        console.error('Dashboard fetch error:', error);
        toast.error('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, [user?.id]);

  const recentOrders = orders.slice(0, 5);

  const stats = {
    totalUploads: orders.length,
    ordersProcessedToday: orders.filter(o => {
      const today = new Date().toISOString().split('T')[0];
      return o.createdAt.split('T')[0] === today;
    }).length,
    failedOrders: orders.filter(o => o.status === 'FAILED').length,
    pendingReview: orders.filter(o => o.status === 'NEEDS_MANUAL_REVIEW').length,
  };

  const orderColumns = [
    {
      key: 'client',
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
      header: 'Date',
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
        return <span>{orderData.number_of_guests || '—'}</span>;
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
        <Link
          href={`/admin/orders/${order.id}`}
          className="text-sm text-slate-600 hover:text-slate-900"
        >
          View
        </Link>
      ),
    },
  ];

  return (
    <PageContainer
      title="Dashboard"
      description="Overview of your group order processing"
    >
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Uploads"
          value={stats.totalUploads}
          icon={<UploadIcon className="w-6 h-6" />}
        />
        <StatCard
          title="Processed Today"
          value={stats.ordersProcessedToday}
          icon={<OrdersIcon className="w-6 h-6" />}
          trend={{ value: 0, isPositive: true }}
        />
        <StatCard
          title="Failed Orders"
          value={stats.failedOrders}
          icon={<ProcessIcon className="w-6 h-6" />}
        />
        <StatCard
          title="Pending Review"
          value={stats.pendingReview}
          icon={<ReviewIcon className="w-6 h-6" />}
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card>
          <h3 className="text-sm font-semibold text-slate-900 mb-3">Quick Actions</h3>
          <div className="space-y-2">
            <Link
              href="/admin/orders"
              className="block px-4 py-3 bg-slate-50 hover:bg-slate-100 rounded-md text-sm font-medium text-slate-700 transition-colors"
            >
              View All Orders
            </Link>
            <Link
              href="/admin/orders?status=NEEDS_MANUAL_REVIEW"
              className="block px-4 py-3 bg-slate-50 hover:bg-slate-100 rounded-md text-sm font-medium text-slate-700 transition-colors"
            >
              Manual Review ({stats.pendingReview} pending)
            </Link>
            <Link
              href="/admin/users"
              className="block px-4 py-3 bg-slate-50 hover:bg-slate-100 rounded-md text-sm font-medium text-slate-700 transition-colors"
            >
              Manage Users
            </Link>
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-900 mb-3">Processing Status</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-violet-50 rounded-md">
              <p className="text-2xl font-semibold text-violet-700">
                {orders.filter(o => o.status === 'PROCESSING').length}
              </p>
              <p className="text-xs text-violet-600 mt-1">Processing</p>
            </div>
            <div className="text-center p-4 bg-amber-50 rounded-md">
              <p className="text-2xl font-semibold text-amber-700">
                {orders.filter(o => o.status === 'NEEDS_MANUAL_REVIEW').length}
              </p>
              <p className="text-xs text-amber-600 mt-1">Needs Review</p>
            </div>
            <div className="text-center p-4 bg-sky-50 rounded-md">
              <p className="text-2xl font-semibold text-sky-700">
                {orders.filter(o => o.status === 'READY_TO_SEND').length}
              </p>
              <p className="text-xs text-sky-600 mt-1">Ready to Send</p>
            </div>
            <div className="text-center p-4 bg-emerald-50 rounded-md">
              <p className="text-2xl font-semibold text-emerald-700">
                {orders.filter(o => o.status === 'SENT').length}
              </p>
              <p className="text-xs text-emerald-600 mt-1">Sent</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Orders */}
      <TableCard
        title="Recent Orders"
        action={
          <Link
            href="/admin/orders"
            className="text-sm text-slate-600 hover:text-slate-900"
          >
            View All
          </Link>
        }
      >
        <Table
          columns={orderColumns}
          data={recentOrders}
          keyExtractor={(order) => order.id}
          emptyMessage={loading ? 'Loading dashboard data...' : 'No recent orders'}
        />
      </TableCard>
    </PageContainer>
  );
}

