'use client';

import React, { useState } from 'react';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Table, TableCard } from '@/app/components/ui/Table';
import { Badge, getStatusBadgeVariant } from '@/app/components/ui/Badge';
import { Button } from '@/app/components/ui/Button';
import { Input } from '@/app/components/ui/Input';
import { Select } from '@/app/components/ui/Select';
import { Modal } from '@/app/components/ui/Modal';
import { mockUsers } from '@/app/data/mock';
import { User, UserRole } from '@/app/types';
import { PlusIcon, EditIcon } from '@/app/components/icons';

interface UserFormData {
  name: string;
  email: string;
  role: UserRole;
  status: 'active' | 'inactive';
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>(mockUsers);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState<UserFormData>({
    name: '',
    email: '',
    role: 'staff',
    status: 'active',
  });

  const handleOpenModal = (user?: User) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        name: user.name,
        email: user.email,
        role: user.role,
        status: user.status,
      });
    } else {
      setEditingUser(null);
      setFormData({
        name: '',
        email: '',
        role: 'staff',
        status: 'active',
      });
    }
    setIsModalOpen(true);
  };

  const handleSave = () => {
    if (editingUser) {
      setUsers(prev =>
        prev.map(u =>
          u.id === editingUser.id
            ? { ...u, name: formData.name, email: formData.email, role: formData.role, status: formData.status }
            : u
        )
      );
    } else {
      const newUser: User = {
        id: String(Date.now()),
        name: formData.name,
        email: formData.email,
        role: formData.role,
        status: formData.status,
        createdAt: new Date().toISOString().split('T')[0],
      };
      setUsers(prev => [...prev, newUser]);
    }
    setIsModalOpen(false);
  };

  const toggleStatus = (id: string) => {
    setUsers(prev =>
      prev.map(u =>
        u.id === id 
          ? { ...u, status: (u.status === 'active' ? 'inactive' : 'active') as 'active' | 'inactive' } 
          : u
      )
    );
  };

  const columns = [
    {
      key: 'name',
      header: 'Name',
      render: (user: User) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center text-sm font-medium text-slate-600">
            {user.name.charAt(0)}
          </div>
          <span className="font-medium text-slate-900">{user.name}</span>
        </div>
      ),
    },
    {
      key: 'email',
      header: 'Email',
      render: (user: User) => (
        <span className="text-slate-600">{user.email}</span>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      render: (user: User) => (
        <Badge variant={user.role === 'admin' ? 'info' : 'default'}>
          {user.role === 'admin' ? 'Admin' : 'Staff'}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (user: User) => (
        <Badge variant={getStatusBadgeVariant(user.status)}>
          {user.status === 'active' ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'createdAt',
      header: 'Created',
      render: (user: User) => (
        <span className="text-slate-600">{user.createdAt}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (user: User) => (
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleOpenModal(user)}
          >
            <EditIcon className="w-4 h-4" />
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => toggleStatus(user.id)}
          >
            {user.status === 'active' ? 'Disable' : 'Enable'}
          </Button>
        </div>
      ),
    },
  ];

  const roleOptions = [
    { value: 'staff', label: 'Staff' },
    { value: 'admin', label: 'Admin' },
  ];

  return (
    <PageContainer
      title="User Management"
      description="Manage system users and their roles"
      action={
        <Button
          leftIcon={<PlusIcon className="w-4 h-4" />}
          onClick={() => handleOpenModal()}
        >
          Add User
        </Button>
      }
    >
      <TableCard>
        <Table
          columns={columns}
          data={users}
          keyExtractor={(user) => user.id}
          emptyMessage="No users found"
        />
      </TableCard>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingUser ? 'Edit User' : 'Add User'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!formData.name || !formData.email}>
              {editingUser ? 'Save Changes' : 'Add User'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Full Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            placeholder="John Doe"
          />
          <Input
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
            placeholder="john@clubem.com"
          />
          <Select
            label="Role"
            options={roleOptions}
            value={formData.role}
            onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value as UserRole }))}
          />
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="userStatus"
              checked={formData.status === 'active'}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                status: e.target.checked ? 'active' : 'inactive' 
              }))}
              className="w-4 h-4 text-slate-900 border-slate-300 rounded focus:ring-slate-500"
            />
            <label htmlFor="userStatus" className="text-sm text-slate-700">
              User is active
            </label>
          </div>
        </div>
      </Modal>
    </PageContainer>
  );
}

