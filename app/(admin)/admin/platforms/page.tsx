'use client';

import React, { useState } from 'react';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Table, TableCard } from '@/app/components/ui/Table';
import { Badge, getStatusBadgeVariant } from '@/app/components/ui/Badge';
import { Button } from '@/app/components/ui/Button';
import { Input } from '@/app/components/ui/Input';
import { Modal } from '@/app/components/ui/Modal';
import { mockPlatforms } from '@/app/data/mock';
import { Platform } from '@/app/types';
import { PlusIcon, EditIcon, TrashIcon } from '@/app/components/icons';

interface PlatformFormData {
  name: string;
  status: 'active' | 'disabled';
}

export default function PlatformsPage() {
  const [platforms, setPlatforms] = useState<Platform[]>(mockPlatforms);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPlatform, setEditingPlatform] = useState<Platform | null>(null);
  const [formData, setFormData] = useState<PlatformFormData>({
    name: '',
    status: 'active',
  });

  const handleOpenModal = (platform?: Platform) => {
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

  const handleSave = () => {
    const today = new Date().toISOString().split('T')[0];
    
    if (editingPlatform) {
      setPlatforms(prev =>
        prev.map(p =>
          p.id === editingPlatform.id
            ? { ...p, name: formData.name, status: formData.status, lastUpdated: today }
            : p
        )
      );
    } else {
      const newPlatform: Platform = {
        id: String(Date.now()),
        name: formData.name,
        status: formData.status,
        lastUpdated: today,
      };
      setPlatforms(prev => [...prev, newPlatform]);
    }
    setIsModalOpen(false);
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this platform?')) {
      setPlatforms(prev => prev.filter(p => p.id !== id));
    }
  };

  const toggleStatus = (id: string) => {
    const today = new Date().toISOString().split('T')[0];
    setPlatforms(prev =>
      prev.map(p =>
        p.id === id 
          ? { ...p, status: (p.status === 'active' ? 'disabled' : 'active') as 'active' | 'disabled', lastUpdated: today } 
          : p
      )
    );
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
            onClick={() => toggleStatus(platform.id)}
          >
            {platform.status === 'active' ? 'Disable' : 'Enable'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleDelete(platform.id)}
          >
            <TrashIcon className="w-4 h-4 text-red-500" />
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
        <Table
          columns={columns}
          data={platforms}
          keyExtractor={(platform) => platform.id}
          emptyMessage="No platforms configured"
        />
      </TableCard>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingPlatform ? 'Edit Platform' : 'Add Platform'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!formData.name}>
              {editingPlatform ? 'Save Changes' : 'Add Platform'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
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
    </PageContainer>
  );
}

