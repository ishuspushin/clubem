'use client';

import React, { useState } from 'react';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Table, TableCard } from '@/app/components/ui/Table';
import { Badge, getStatusBadgeVariant, formatStatus } from '@/app/components/ui/Badge';
import { Input } from '@/app/components/ui/Input';
import { Select } from '@/app/components/ui/Select';
import { mockUploads } from '@/app/data/mock';
import { Upload } from '@/app/types';
import { useAuth } from '@/app/context/AuthContext';

export default function MyUploadsPage() {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Filter uploads to only show current user's uploads
  // In real app, this would be filtered by backend
  const userUploads = mockUploads.filter(upload => 
    upload.uploadedBy === user?.name || upload.uploadedBy === 'Sarah Johnson'
  );

  const filteredUploads = userUploads.filter(upload => {
    const matchesSearch = 
      upload.fileName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      upload.platform.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || upload.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const columns = [
    {
      key: 'fileName',
      header: 'File Name',
      render: (upload: Upload) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-red-100 rounded flex items-center justify-center">
            <svg className="w-4 h-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
          <span className="font-medium text-slate-900">{upload.fileName}</span>
        </div>
      ),
    },
    {
      key: 'platform',
      header: 'Platform',
      render: (upload: Upload) => (
        <span className="text-slate-600">{upload.platform}</span>
      ),
    },
    {
      key: 'uploadedAt',
      header: 'Upload Date',
      render: (upload: Upload) => (
        <span className="text-slate-600">{upload.uploadedAt}</span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (upload: Upload) => (
        <Badge variant={getStatusBadgeVariant(upload.status)}>
          {formatStatus(upload.status)}
        </Badge>
      ),
    },
  ];

  const statusOptions = [
    { value: 'all', label: 'All Statuses' },
    { value: 'pending', label: 'Pending' },
    { value: 'processing', label: 'Processing' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
  ];

  return (
    <PageContainer
      title="My Uploads"
      description="View all PDF files you have uploaded"
    >
      {/* Filters */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1 max-w-md">
          <Input
            placeholder="Search by file name or platform..."
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
          data={filteredUploads}
          keyExtractor={(item, index) => item.id || `upload-${index}`}
          emptyMessage="No uploads found"
        />
      </TableCard>
    </PageContainer>
  );
}

