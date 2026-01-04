'use client';

import React, { useState, useEffect } from 'react';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Table, TableCard } from '@/app/components/ui/Table';
import { Badge, getStatusBadgeVariant, formatStatus } from '@/app/components/ui/Badge';
import { Button } from '@/app/components/ui/Button';
import { Order, ProcessingStep } from '@/app/types';
import { RefreshIcon } from '@/app/components/icons';
import { useAuth } from '@/app/context/AuthContext';
import { toast } from 'react-hot-toast';

const stepLabels: Record<ProcessingStep, string> = {
  ocr: 'OCR',
  extraction: 'Extraction',
  formatting: 'Formatting',
  email: 'Email',
};

export default function ProcessingQueuePage() {
  const { user } = useAuth();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchQueue = async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      const response = await fetch(`/api/orders?userId=${user.id}`);
      if (!response.ok) throw new Error('Failed to fetch queue');
      const data = await response.json();
      // Filter for processing or failed
      const queueOrders = (data.orders || []).filter((o: any) =>
        o.status === 'PROCESSING' || o.status === 'FAILED'
      );
      setOrders(queueOrders);
    } catch (error: any) {
      console.error('Queue fetch error:', error);
      toast.error('Failed to load processing queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [user?.id]);

  const handleRetry = async (orderId: string) => {
    try {
      const response = await fetch(`/api/orders/${orderId}/retry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: user?.id
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to retry order');
      }

      toast.success('Order retry initiated');
      fetchQueue();
    } catch (err: any) {
      toast.error(err.message || 'Failed to retry order');
    }
  };

  const columns = [
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
      key: 'groupOrderNumber',
      header: 'Group Order #',
      render: (order: any) => (
        <span className="text-slate-600 font-mono text-sm">{order.groupOrderNumber || '—'}</span>
      ),
    },
    {
      key: 'currentStep',
      header: 'Current Step',
      render: (order: any) => (
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            {(['ocr', 'extraction', 'formatting', 'email'] as ProcessingStep[]).map((step, idx) => {
              const steps: ProcessingStep[] = ['ocr', 'extraction', 'formatting', 'email'];
              const stepIndex = steps.indexOf(order.currentStep || 'ocr');
              const currentStepIndex = idx;
              const isCompleted = currentStepIndex < stepIndex;
              const isCurrent = currentStepIndex === stepIndex;

              return (
                <div
                  key={step}
                  className={`
                    w-2 h-2 rounded-full
                    ${isCompleted ? 'bg-emerald-500' : isCurrent ? 'bg-violet-500' : 'bg-slate-200'}
                  `}
                  title={stepLabels[step]}
                />
              );
            })}
          </div>
          <span className="text-sm text-slate-600">{stepLabels[order.currentStep as ProcessingStep] || 'Initializing...'}</span>
        </div>
      ),
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
        order.status === 'FAILED' && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleRetry(order.id)}
            leftIcon={<RefreshIcon className="w-4 h-4" />}
          >
            Retry
          </Button>
        )
      ),
    },
  ];

  return (
    <PageContainer
      title="Processing Queue"
      description="Monitor and manage orders in the processing pipeline"
      action={
        <Button
          variant="secondary"
          size="sm"
          onClick={fetchQueue}
          isLoading={loading}
          leftIcon={<RefreshIcon className="w-4 h-4" />}
        >
          Refresh
        </Button>
      }
    >
      {/* Processing Steps Legend */}
      <div className="mb-6 p-4 bg-white rounded-md border border-slate-200">
        <h3 className="text-sm font-semibold text-slate-900 mb-3">Processing Pipeline</h3>
        <div className="flex flex-wrap gap-6">
          {(['ocr', 'extraction', 'formatting', 'email'] as ProcessingStep[]).map((step, idx) => (
            <div key={step} className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-sm font-medium text-slate-600">
                {idx + 1}
              </div>
              <span className="text-sm text-slate-700">{stepLabels[step]}</span>
            </div>
          ))}
        </div>
      </div>

      <TableCard
        title="Active Queue"
        description={`${orders.length} orders in queue`}
      >
        <Table
          columns={columns}
          data={orders}
          keyExtractor={(item, index) => item.id || `order-${index}`}
          emptyMessage={loading ? "Loading queue..." : "No orders currently in queue"}
        />
      </TableCard>
    </PageContainer>
  );
}

