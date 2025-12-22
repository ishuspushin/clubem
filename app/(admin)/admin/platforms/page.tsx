'use client';

import React, { useState, useEffect } from 'react';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Table, TableCard } from '@/app/components/ui/Table';
import { Badge, getStatusBadgeVariant } from '@/app/components/ui/Badge';
import { Button } from '@/app/components/ui/Button';
import { Input } from '@/app/components/ui/Input';
import { Modal, ConfirmDialog } from '@/app/components/ui/Modal';
import { Platform } from '@/app/types';
import { PlusIcon, EditIcon, TrashIcon } from '@/app/components/icons';
import { useAuth } from '@/app/context/AuthContext';
import { useToast } from '@/app/components/ui/Toast';

export default function PlatformsPage() {
  const { user } = useAuth();
  const toast = useToast();
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [platformToDelete, setPlatformToDelete] = useState<Platform | null>(null);
  const [editingPlatform, setEditingPlatform] = useState<Platform | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    status: 'active' as 'active' | 'disabled',
  });
  const [error, setError] = useState('');

  // Fetch platforms from API
  useEffect(() => {
    fetchPlatforms();
  }, []);

  const fetchPlatforms = async () => {
    try {
      setIsLoading(true);
      if (!user?.id) {
        setIsLoading(false);
        return;
      }

      const response = await fetch(`/api/platforms?userId=${user.id}`);
      if (!response.ok) throw new Error('Failed to fetch platforms');
      const data = await response.json();
      setPlatforms(data.platforms);
    } catch (error) {
      console.error('Error fetching platforms:', error);
      toast.error('Failed to load platforms');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenModal = (platform?: Platform) => {
    setError('');
    if (platform) {
      setEditingPlatform(platform);
      setFormData({
        name: platform.name,
        status: platform.status,
      });
    } else {
      setEditingPlatform(null);
      setFormData({
        name: '',
        status: 'active',
      });
    }
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    setError('');

    if (!formData.name.trim()) {
      setError('Platform name is required');
      return;
    }

    if (!user?.id) {
      setError('User not authenticated');
      return;
    }

    try {
      if (editingPlatform) {
        // Update platform
        const response = await fetch(`/api/platforms/${editingPlatform.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: formData.name,
            status: formData.status,
            userId: user.id,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          setError(errorData.error || 'Failed to update platform');
          return;
        }

        toast.success('Platform updated successfully');
      } else {
        // Create platform
        const response = await fetch('/api/platforms', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: formData.name,
            status: formData.status,
            userId: user.id,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          setError(errorData.error || 'Failed to create platform');
          return;
        }

        toast.success('Platform created successfully');
      }

      await fetchPlatforms();
      setIsModalOpen(false);
      setFormData({ name: '', status: 'active' });
    } catch (error) {
      console.error('Error saving platform:', error);
      setError('An error occurred');
    }
  };

  const handleDeleteClick = (platform: Platform) => {
    setPlatformToDelete(platform);
    setIsDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!platformToDelete || !user?.id) return;

    try {
      const response = await fetch(`/api/platforms/${platformToDelete.id}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: user.id }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        toast.error(errorData.error || 'Failed to delete platform');
        return;
      }

      toast.success('Platform deleted successfully');
      await fetchPlatforms();
      setIsDeleteConfirmOpen(false);
      setPlatformToDelete(null);
    } catch (error) {
      console.error('Error deleting platform:', error);
      toast.error('An error occurred while deleting the platform');
    }
  };

  const toggleStatus = async (platform: Platform) => {
    if (!user?.id) return;

    const newStatus = platform.status === 'active' ? 'disabled' : 'active';

    try {
      const response = await fetch(`/api/platforms/${platform.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: newStatus,
          userId: user.id,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        toast.error(errorData.error || 'Failed to update platform status');
        return;
      }

      toast.success(`Platform ${newStatus === 'active' ? 'enabled' : 'disabled'} successfully`);
      await fetchPlatforms();
    } catch (error) {
      console.error('Error updating platform status:', error);
      toast.error('An error occurred while updating platform status');
    }
  };

  const columns = [
    {
      key: 'name',
      header: 'Platform Name',
      render: (platform: Platform) => (
        <span className="font-medium text-slate-900">{platform.name}</span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (platform: Platform) => (
        <Badge variant={getStatusBadgeVariant(platform.status)}>
          {platform.status === 'active' ? 'Active' : 'Disabled'}
        </Badge>
      ),
    },
    {
      key: 'lastUpdated',
      header: 'Last Updated',
      render: (platform: Platform) => (
        <span className="text-slate-600">{platform.lastUpdated}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (platform: Platform) => (
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleOpenModal(platform)}
          >
            <EditIcon className="w-4 h-4" />
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => toggleStatus(platform)}
          >
            {platform.status === 'active' ? 'Disable' : 'Enable'}
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => handleDeleteClick(platform)}
            title="Delete Platform"
          >
            <TrashIcon className="w-4 h-4" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <PageContainer
      title="Supported Platforms"
      description="Manage the food ordering platforms supported by the system"
      action={
        <Button
          leftIcon={<PlusIcon className="w-4 h-4" />}
          onClick={() => handleOpenModal()}
        >
          Add Platform
        </Button>
      }
    >
      <TableCard>
        {isLoading ? (
          <div className="p-8 text-center text-slate-600">Loading platforms...</div>
        ) : (
          <Table
            columns={columns}
            data={platforms}
            keyExtractor={(platform) => platform.id}
            emptyMessage="No platforms configured"
          />
        )}
      </TableCard>

      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setError('');
        }}
        title={editingPlatform ? 'Edit Platform' : 'Add Platform'}
        footer={
          <>
            <Button variant="secondary" onClick={() => {
              setIsModalOpen(false);
              setError('');
            }}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!formData.name.trim()}>
              {editingPlatform ? 'Save Changes' : 'Add Platform'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {error && (
            <div className="p-3 rounded-md bg-red-50 border border-red-200">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}
          <Input
            label="Platform Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            placeholder="e.g., Grubhub"
          />
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="platformStatus"
              checked={formData.status === 'active'}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                status: e.target.checked ? 'active' : 'disabled' 
              }))}
              className="w-4 h-4 text-slate-900 border-slate-300 rounded focus:ring-slate-500"
            />
            <label htmlFor="platformStatus" className="text-sm text-slate-700">
              Platform is active
            </label>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={isDeleteConfirmOpen}
        onClose={() => {
          setIsDeleteConfirmOpen(false);
          setPlatformToDelete(null);
        }}
        onConfirm={handleDeleteConfirm}
        title="Delete Platform"
        message={`Are you sure you want to delete platform "${platformToDelete?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </PageContainer>
  );
}

