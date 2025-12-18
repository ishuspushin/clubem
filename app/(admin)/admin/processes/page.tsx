'use client';

import React, { useState } from 'react';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Card, CardHeader } from '@/app/components/ui/Card';
import { Badge } from '@/app/components/ui/Badge';
import { Button } from '@/app/components/ui/Button';
import { Input } from '@/app/components/ui/Input';
import { Textarea } from '@/app/components/ui/Textarea';
import { Modal } from '@/app/components/ui/Modal';
import { mockProcessConfigs } from '@/app/data/mock';
import { ProcessConfig } from '@/app/types';
import { PlusIcon, EditIcon, TrashIcon } from '@/app/components/icons';

interface ProcessFormData {
  name: string;
  description: string;
  steps: string;
  isActive: boolean;
}

export default function ProcessesPage() {
  const [processes, setProcesses] = useState<ProcessConfig[]>(mockProcessConfigs);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProcess, setEditingProcess] = useState<ProcessConfig | null>(null);
  const [formData, setFormData] = useState<ProcessFormData>({
    name: '',
    description: '',
    steps: '',
    isActive: true,
  });

  const handleOpenModal = (process?: ProcessConfig) => {
    if (process) {
      setEditingProcess(process);
      setFormData({
        name: process.name,
        description: process.description,
        steps: process.steps.join('\n'),
        isActive: process.isActive,
      });
    } else {
      setEditingProcess(null);
      setFormData({
        name: '',
        description: '',
        steps: '',
        isActive: true,
      });
    }
    setIsModalOpen(true);
  };

  const handleSave = () => {
    const stepsArray = formData.steps.split('\n').filter(s => s.trim());
    
    if (editingProcess) {
      setProcesses(prev =>
        prev.map(p =>
          p.id === editingProcess.id
            ? { ...p, name: formData.name, description: formData.description, steps: stepsArray, isActive: formData.isActive }
            : p
        )
      );
    } else {
      const newProcess: ProcessConfig = {
        id: String(Date.now()),
        name: formData.name,
        description: formData.description,
        steps: stepsArray,
        isActive: formData.isActive,
      };
      setProcesses(prev => [...prev, newProcess]);
    }
    setIsModalOpen(false);
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this process?')) {
      setProcesses(prev => prev.filter(p => p.id !== id));
    }
  };

  const toggleActive = (id: string) => {
    setProcesses(prev =>
      prev.map(p =>
        p.id === id ? { ...p, isActive: !p.isActive } : p
      )
    );
  };

  return (
    <PageContainer
      title="Process Configuration"
      description="Define processing workflows for orders"
      action={
        <Button
          leftIcon={<PlusIcon className="w-4 h-4" />}
          onClick={() => handleOpenModal()}
        >
          Add Process
        </Button>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {processes.map(process => (
          <Card key={process.id}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold text-slate-900">{process.name}</h3>
                <p className="text-sm text-slate-500 mt-1">{process.description}</p>
              </div>
              <Badge variant={process.isActive ? 'success' : 'default'}>
                {process.isActive ? 'Active' : 'Inactive'}
              </Badge>
            </div>

            <div className="mb-4">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Processing Steps
              </p>
              <ol className="space-y-2">
                {process.steps.map((step, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-sm text-slate-700">
                    <span className="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center text-xs font-medium text-slate-600">
                      {idx + 1}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>

            <div className="flex gap-2 pt-4 border-t border-slate-200">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleOpenModal(process)}
                leftIcon={<EditIcon className="w-4 h-4" />}
              >
                Edit
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => toggleActive(process.id)}
              >
                {process.isActive ? 'Disable' : 'Enable'}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDelete(process.id)}
              >
                <TrashIcon className="w-4 h-4 text-red-500" />
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingProcess ? 'Edit Process' : 'Add Process'}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!formData.name || !formData.steps}>
              {editingProcess ? 'Save Changes' : 'Add Process'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Process Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            placeholder="e.g., Standard Processing"
          />
          <Textarea
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Describe what this process is used for..."
          />
          <Textarea
            label="Processing Steps (one per line)"
            value={formData.steps}
            onChange={(e) => setFormData(prev => ({ ...prev, steps: e.target.value }))}
            placeholder="OCR Scan&#10;Data Extraction&#10;Validation&#10;..."
            className="min-h-[120px]"
            helperText="Enter each step on a new line"
          />
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isActive"
              checked={formData.isActive}
              onChange={(e) => setFormData(prev => ({ ...prev, isActive: e.target.checked }))}
              className="w-4 h-4 text-slate-900 border-slate-300 rounded focus:ring-slate-500"
            />
            <label htmlFor="isActive" className="text-sm text-slate-700">
              Active process
            </label>
          </div>
        </div>
      </Modal>
    </PageContainer>
  );
}

