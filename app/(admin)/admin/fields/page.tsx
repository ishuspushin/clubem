'use client';

import React, { useState } from 'react';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Table, TableCard } from '@/app/components/ui/Table';
import { Badge } from '@/app/components/ui/Badge';
import { Button } from '@/app/components/ui/Button';
import { Input } from '@/app/components/ui/Input';
import { Select } from '@/app/components/ui/Select';
import { Textarea } from '@/app/components/ui/Textarea';
import { Modal } from '@/app/components/ui/Modal';
import { mockFieldConfigs } from '@/app/data/mock';
import { FieldConfig } from '@/app/types';
import { PlusIcon, EditIcon, TrashIcon } from '@/app/components/icons';

export default function FieldsPage() {
  const [fields, setFields] = useState<FieldConfig[]>(mockFieldConfigs);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingField, setEditingField] = useState<FieldConfig | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'text',
    required: false,
    description: '',
  });

  const handleOpenModal = (field?: FieldConfig) => {
    if (field) {
      setEditingField(field);
      setFormData({
        name: field.name,
        type: field.type,
        required: field.required,
        description: field.description,
      });
    } else {
      setEditingField(null);
      setFormData({
        name: '',
        type: 'text',
        required: false,
        description: '',
      });
    }
    setIsModalOpen(true);
  };

  const handleSave = () => {
    if (editingField) {
      setFields(prev =>
        prev.map(f =>
          f.id === editingField.id
            ? { ...f, ...formData, type: formData.type as FieldConfig['type'] }
            : f
        )
      );
    } else {
      const newField: FieldConfig = {
        id: String(Date.now()),
        name: formData.name,
        type: formData.type as FieldConfig['type'],
        required: formData.required,
        description: formData.description,
      };
      setFields(prev => [...prev, newField]);
    }
    setIsModalOpen(false);
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this field?')) {
      setFields(prev => prev.filter(f => f.id !== id));
    }
  };

  const columns = [
    {
      key: 'name',
      header: 'Field Name',
      render: (field: FieldConfig) => (
        <span className="font-medium text-slate-900">{field.name}</span>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (field: FieldConfig) => (
        <span className="capitalize font-mono text-sm bg-slate-100 px-2 py-1 rounded">
          {field.type}
        </span>
      ),
    },
    {
      key: 'required',
      header: 'Required',
      render: (field: FieldConfig) => (
        <Badge variant={field.required ? 'info' : 'default'}>
          {field.required ? 'Required' : 'Optional'}
        </Badge>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      render: (field: FieldConfig) => (
        <span className="text-slate-600 text-sm">{field.description}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (field: FieldConfig) => (
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleOpenModal(field)}
          >
            <EditIcon className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleDelete(field.id)}
          >
            <TrashIcon className="w-4 h-4 text-red-500" />
          </Button>
        </div>
      ),
    },
  ];

  const typeOptions = [
    { value: 'text', label: 'Text' },
    { value: 'number', label: 'Number' },
    { value: 'date', label: 'Date' },
    { value: 'select', label: 'Select' },
  ];

  return (
    <PageContainer
      title="Field Configuration"
      description="Define the fields expected in order data extraction"
      action={
        <Button
          leftIcon={<PlusIcon className="w-4 h-4" />}
          onClick={() => handleOpenModal()}
        >
          Add Field
        </Button>
      }
    >
      <TableCard>
        <Table
          columns={columns}
          data={fields}
          keyExtractor={(field) => field.id}
          emptyMessage="No fields configured"
        />
      </TableCard>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingField ? 'Edit Field' : 'Add Field'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!formData.name}>
              {editingField ? 'Save Changes' : 'Add Field'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Field Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            placeholder="e.g., Business Client"
          />
          <Select
            label="Field Type"
            options={typeOptions}
            value={formData.type}
            onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value }))}
          />
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="required"
              checked={formData.required}
              onChange={(e) => setFormData(prev => ({ ...prev, required: e.target.checked }))}
              className="w-4 h-4 text-slate-900 border-slate-300 rounded focus:ring-slate-500"
            />
            <label htmlFor="required" className="text-sm text-slate-700">
              Required field
            </label>
          </div>
          <Textarea
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Describe what this field is used for..."
          />
        </div>
      </Modal>
    </PageContainer>
  );
}

