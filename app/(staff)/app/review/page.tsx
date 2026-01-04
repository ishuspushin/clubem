'use client';

import React, { useState, useEffect } from 'react';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Card, CardHeader } from '@/app/components/ui/Card';
import { Table, TableCard } from '@/app/components/ui/Table';
import { Badge, getStatusBadgeVariant, formatStatus } from '@/app/components/ui/Badge';
import { Button } from '@/app/components/ui/Button';
import { Input } from '@/app/components/ui/Input';
import { Order, GuestItem } from '@/app/types';
import { CheckIcon, SendIcon, RefreshIcon, EyeIcon } from '@/app/components/icons';
import { useAuth } from '@/app/context/AuthContext';
import { toast } from 'react-hot-toast';
import { useRouter } from 'next/navigation';

export default function ManualReviewPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<any | null>(null);
  const [editedOrderData, setEditedOrderData] = useState<any>({});
  const [editedItems, setEditedItems] = useState<any[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  const fetchOrders = async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      const response = await fetch(`/api/orders?userId=${user.id}`);
      if (!response.ok) throw new Error('Failed to fetch orders');
      const data = await response.json();
      const needsReview = (data.orders || []).filter((o: any) =>
        o.status === 'NEEDS_MANUAL_REVIEW'
      );
      setOrders(needsReview);
      if (needsReview.length > 0 && !selectedOrder) {
        handleSelectOrder(needsReview[0]);
      }
    } catch (error: any) {
      console.error('Review fetch error:', error);
      toast.error('Failed to load orders needing review');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();

    // Check for orderId in query params to auto-select
    const params = new URLSearchParams(window.location.search);
    const orderId = params.get('orderId');
    if (orderId && orders.length > 0) {
      const order = orders.find(o => o.id === orderId);
      if (order) {
        handleSelectOrder(order);
      }
    }
  }, [user?.id, orders.length]);

  const handleSelectOrder = (order: any) => {
    setSelectedOrder(order);
    setEditedOrderData(order.data?.main_order_information || {});
    const items = order.data?.individual_orders || [];
    setEditedItems(items.map((item: any, index: number) => ({
      ...item,
      id: item.id || `temp-${index}` // Ensure unique ID for keys
    })));
  };

  const handleOrderDataChange = (field: string, value: string | number) => {
    setEditedOrderData((prev: any) => ({
      ...prev,
      [field]: value
    }));
  };

  const handleItemChange = (itemId: string, field: string, value: string) => {
    setEditedItems(prev =>
      prev.map(item =>
        item.id === itemId ? { ...item, [field]: value } : item
      )
    );
  };

  const handleSaveCorrections = async () => {
    if (!selectedOrder) return;
    try {
      setIsSaving(true);
      // Update the order data with edited items, ensuring modifications are handled correctly
      const processedItems = editedItems.map(item => ({
        ...item,
        modifications: typeof item.modifications === 'string'
          ? item.modifications.split(',').map((s: string) => s.trim()).filter((s: string) => s !== '')
          : item.modifications
      }));

      const updatedData = {
        ...selectedOrder.data,
        main_order_information: editedOrderData,
        individual_orders: processedItems
      };

      const response = await fetch(`/api/orders/${selectedOrder.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: user?.id,
          data: updatedData
        }),
      });

      if (!response.ok) throw new Error('Failed to save corrections');

      toast.success('Corrections saved successfully');
      fetchOrders();
    } catch (err: any) {
      toast.error(err.message || 'Failed to save corrections');
    } finally {
      setIsSaving(false);
    }
  };

  const handleApproveAndSend = async () => {
    if (!selectedOrder) return;
    try {
      setIsSaving(true);
      const response = await fetch(`/api/orders/${selectedOrder.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: user?.id,
          status: 'CONFIRMED'
        }),
      });

      if (!response.ok) throw new Error('Failed to approve order');

      toast.success('Order approved and marked as ready');
      setSelectedOrder(null);
      fetchOrders();
    } catch (err: any) {
      toast.error(err.message || 'Failed to approve order');
    } finally {
      setIsSaving(false);
    }
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
      key: 'guests',
      header: 'Guests',
      render: (order: any) => order.data?.main_order_information?.number_of_guests || '—',
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
  ];

  return (
    <PageContainer
      title="Manual Review"
      description="Review and correct orders that need human verification"
      action={
        <Button
          variant="secondary"
          size="sm"
          onClick={fetchOrders}
          isLoading={loading}
          leftIcon={<RefreshIcon className="w-4 h-4" />}
        >
          Refresh
        </Button>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Orders List */}
        <div className="lg:col-span-1">
          <TableCard
            title="Orders Needing Review"
            description={`${orders.length} orders`}
          >
            <Table
              columns={orderColumns}
              data={orders}
              keyExtractor={(item, index) => item.id || `order-${index}`}
              onRowClick={handleSelectOrder}
              emptyMessage={loading ? "Loading..." : "No orders need review"}
            />
          </TableCard>
        </div>

        {/* Review Panel */}
        <div className="lg:col-span-2">
          {selectedOrder ? (
            <Card>
              <CardHeader
                title={`Review Order`}
                description={selectedOrder.data?.main_order_information?.business_client || 'Order Details'}
                action={
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push(`/app/orders/${selectedOrder.id}`)}
                    leftIcon={<EyeIcon className="w-4 h-4" />}
                  >
                    View Details
                  </Button>
                }
              />

              {/* Order Summary */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6 p-4 bg-slate-50 rounded-md">
                <div>
                  <p className="text-xs text-slate-500 mb-1">Client</p>
                  <Input
                    value={editedOrderData.client_name || ''}
                    onChange={(e) => handleOrderDataChange('client_name', e.target.value)}
                    className="h-8 text-sm"
                  />
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Requested Date</p>
                  <Input
                    value={editedOrderData.requested_pick_up_date || ''}
                    onChange={(e) => handleOrderDataChange('requested_pick_up_date', e.target.value)}
                    className="h-8 text-sm"
                  />
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Guests</p>
                  <Input
                    type="number"
                    value={editedOrderData.number_of_guests || ''}
                    onChange={(e) => handleOrderDataChange('number_of_guests', parseInt(e.target.value) || 0)}
                    className="h-8 text-sm"
                  />
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Subtotal</p>
                  <div className="relative">
                    <span className="absolute left-2 top-1.5 text-slate-400 text-sm">$</span>
                    <Input
                      type="number"
                      step="0.01"
                      value={editedOrderData.order_subtotal || ''}
                      onChange={(e) => handleOrderDataChange('order_subtotal', parseFloat(e.target.value) || 0)}
                      className="h-8 text-sm pl-5"
                    />
                  </div>
                </div>
              </div>

              {/* Editable Items Table */}
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-slate-900 mb-3">
                  Guest Items ({editedItems.length})
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200">
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase">
                          Guest Name
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase">
                          Item
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase">
                          Modifications
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase">
                          Comments
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {editedItems.map((item, idx) => (
                        <tr key={item.id || idx}>
                          <td className="px-3 py-2">
                            <Input
                              value={item.guest_name || ''}
                              onChange={(e) => handleItemChange(item.id, 'guest_name', e.target.value)}
                              className="text-sm"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <Input
                              value={item.item_name || ''}
                              onChange={(e) => handleItemChange(item.id, 'item_name', e.target.value)}
                              className="text-sm"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <Input
                              value={
                                Array.isArray(item.modifications)
                                  ? item.modifications.join(', ')
                                  : (item.modifications || '')
                              }
                              onChange={(e) => handleItemChange(item.id, 'modifications', e.target.value)}
                              className="text-sm"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <Input
                              value={item.comments || ''}
                              onChange={(e) => handleItemChange(item.id, 'comments', e.target.value)}
                              className="text-sm"
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t border-slate-200">
                <Button
                  variant="secondary"
                  onClick={handleSaveCorrections}
                  isLoading={isSaving}
                  leftIcon={<CheckIcon className="w-4 h-4" />}
                >
                  Save Corrections
                </Button>
                <Button
                  variant="primary"
                  onClick={handleApproveAndSend}
                  isLoading={isSaving}
                  leftIcon={<SendIcon className="w-4 h-4" />}
                >
                  Approve & Mark Ready
                </Button>
              </div>
            </Card>
          ) : (
            <Card>
              <div className="text-center py-12">
                <p className="text-slate-500">
                  {loading ? "Loading..." : "Select an order from the list to review"}
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </PageContainer>
  );
}

