'use client';

import React, { useState, useEffect } from 'react';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Table, TableCard } from '@/app/components/ui/Table';
import { Badge, getStatusBadgeVariant } from '@/app/components/ui/Badge';
import { Button } from '@/app/components/ui/Button';
import { Input } from '@/app/components/ui/Input';
import { Select } from '@/app/components/ui/Select';
import { Modal } from '@/app/components/ui/Modal';
import { User, UserRole } from '@/app/types';
import { PlusIcon, EditIcon, TrashIcon, CheckIcon } from '@/app/components/icons';
import { useAuth } from '@/app/context/AuthContext';
import { useToast } from '@/app/components/ui/Toast';
import { ConfirmDialog } from '@/app/components/ui/Modal';

interface UserWithApproval extends User {
  isApproved?: boolean;
}

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const toast = useToast();
  const [users, setUsers] = useState<UserWithApproval[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<UserWithApproval | null>(null);
  const [editingUser, setEditingUser] = useState<UserWithApproval | null>(null);
  const [passwordUser, setPasswordUser] = useState<UserWithApproval | null>(null);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    role: 'staff' as UserRole,
  });
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // Fetch users from API
  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/users');
      if (!response.ok) throw new Error('Failed to fetch users');
      const data = await response.json();
      setUsers(data.users);
    } catch (error) {
      console.error('Error fetching users:', error);
      setError('Failed to load users');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenModal = (user?: UserWithApproval) => {
    setError('');
    if (user) {
      setEditingUser(user);
      setFormData({
        email: user.email,
        password: '',
        role: user.role,
      });
    } else {
      setEditingUser(null);
      setFormData({
        email: '',
        password: '',
        role: 'staff',
      });
    }
    setIsModalOpen(true);
  };

  const handleOpenPasswordModal = (user: UserWithApproval) => {
    setPasswordError('');
    setPasswordUser(user);
    setPasswordData({
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    });
    setIsPasswordModalOpen(true);
  };

  const handleSave = async () => {
    setError('');

    if (!formData.email || (!editingUser && !formData.password)) {
      setError('Email and password are required');
      return;
    }

    if (!editingUser && formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    try {
      if (editingUser) {
        // For editing, we'd need an update endpoint - for now, just show error
        setError('Editing users is not yet implemented. Please delete and recreate.');
        return;
      } else {
        // Create new user
        const response = await fetch('/api/users', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            password: formData.password,
            role: formData.role,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          setError(errorData.error || 'Failed to create user');
          return;
        }

        await fetchUsers();
        setIsModalOpen(false);
        setFormData({ email: '', password: '', role: 'staff' });
        toast.success('User created successfully');
      }
    } catch (error) {
      console.error('Error saving user:', error);
      setError('An error occurred');
    }
  };

  const handleDeleteClick = (user: UserWithApproval) => {
    setUserToDelete(user);
    setIsDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!userToDelete) return;

    try {
      const response = await fetch(`/api/users/${userToDelete.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        toast.error(errorData.error || 'Failed to delete user');
        return;
      }

      await fetchUsers();
      toast.success('User deleted successfully');
      setIsDeleteConfirmOpen(false);
      setUserToDelete(null);
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error('An error occurred while deleting the user');
    }
  };

  const handleApprove = async (id: string) => {
    try {
      const response = await fetch(`/api/users/${id}/approve`, {
        method: 'PATCH',
      });

      if (!response.ok) {
        const errorData = await response.json();
        toast.error(errorData.error || 'Failed to approve user');
        return;
      }

      await fetchUsers();
      toast.success('User approved successfully');
    } catch (error) {
      console.error('Error approving user:', error);
      toast.error('An error occurred while approving the user');
    }
  };

  const handleChangePassword = async () => {
    setPasswordError('');

    if (!passwordData.newPassword || !passwordData.confirmPassword) {
      setPasswordError('All fields are required');
      return;
    }

    if (passwordData.newPassword.length < 6) {
      setPasswordError('Password must be at least 6 characters long');
      return;
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }

    try {
      const response = await fetch(`/api/users/${passwordUser?.id}/password`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          currentPassword: passwordData.currentPassword || undefined,
          newPassword: passwordData.newPassword,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        setPasswordError(errorData.error || 'Failed to change password');
        return;
      }

      setIsPasswordModalOpen(false);
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      toast.success('Password changed successfully');
    } catch (error) {
      console.error('Error changing password:', error);
      setPasswordError('An error occurred');
    }
  };

  const columns = [
    {
      key: 'name',
      header: 'Name',
      render: (user: UserWithApproval) => (
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
      render: (user: UserWithApproval) => (
        <span className="text-slate-600">{user.email}</span>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      render: (user: UserWithApproval) => (
        <Badge variant={user.role === 'admin' ? 'info' : 'default'}>
          {user.role === 'admin' ? 'Admin' : 'Staff'}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (user: UserWithApproval) => {
        const isApproved = user.isApproved !== undefined ? user.isApproved : user.status === 'active';
        return (
          <Badge variant={isApproved ? 'success' : 'warning'}>
            {isApproved ? 'Approved' : 'Pending Approval'}
          </Badge>
        );
      },
    },
    {
      key: 'createdAt',
      header: 'Created',
      render: (user: UserWithApproval) => (
        <span className="text-slate-600">{user.createdAt}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (user: UserWithApproval) => {
        const isApproved = user.isApproved !== undefined ? user.isApproved : user.status === 'active';
        const isCurrentUser = currentUser?.id === user.id;

        return (
          <div className="flex gap-2">
            {!isApproved && (
              <Button
                variant="success"
                size="sm"
                onClick={() => handleApprove(user.id)}
                title="Approve User"
              >
                <CheckIcon className="w-4 h-4" />
              </Button>
            )}
            {isCurrentUser && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleOpenPasswordModal(user)}
                title="Change Password"
              >
                <EditIcon className="w-4 h-4" />
              </Button>
            )}
            {!isCurrentUser && (
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleDeleteClick(user)}
                title="Delete User"
              >
                <TrashIcon className="w-4 h-4" />
              </Button>
            )}
          </div>
        );
      },
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
        {isLoading ? (
          <div className="p-8 text-center text-slate-600">Loading users...</div>
        ) : (
          <Table
            columns={columns}
            data={users}
            keyExtractor={(item, index) => item.id || `user-${index}`}
            emptyMessage="No users found"
          />
        )}
      </TableCard>

      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setError('');
        }}
        title={editingUser ? 'Edit User' : 'Add User'}
        footer={
          <>
            <Button variant="secondary" onClick={() => {
              setIsModalOpen(false);
              setError('');
            }}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!formData.email || (!editingUser && !formData.password)}>
              {editingUser ? 'Save Changes' : 'Add User'}
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
            label="Email"
            value={formData.email}
            onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
            placeholder="john@example.com"
            disabled={!!editingUser}
          />
          {!editingUser && (
            <>
              <Input
                label="Password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                placeholder="Enter password (min 6 characters)"
              />
            </>
          )}
          <Select
            label="Role"
            options={roleOptions}
            value={formData.role}
            onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value as UserRole }))}
          />
          {editingUser && (
            <p className="text-sm text-slate-500">
              Note: User editing is not yet implemented. Please delete and recreate if needed.
            </p>
          )}
        </div>
      </Modal>

      <Modal
        isOpen={isPasswordModalOpen}
        onClose={() => {
          setIsPasswordModalOpen(false);
          setPasswordError('');
        }}
        title="Change Password"
        footer={
          <>
            <Button variant="secondary" onClick={() => {
              setIsPasswordModalOpen(false);
              setPasswordError('');
            }}>
              Cancel
            </Button>
            <Button onClick={handleChangePassword} disabled={!passwordData.newPassword || !passwordData.confirmPassword}>
              Change Password
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {passwordError && (
            <div className="p-3 rounded-md bg-red-50 border border-red-200">
              <p className="text-sm text-red-600">{passwordError}</p>
            </div>
          )}
          <p className="text-sm text-slate-600 mb-4">
            Changing password for: <strong>{passwordUser?.name}</strong>
          </p>
          {passwordUser?.id === currentUser?.id && (
            <Input
              label="Current Password"
              type="password"
              value={passwordData.currentPassword}
              onChange={(e) => setPasswordData(prev => ({ ...prev, currentPassword: e.target.value }))}
              placeholder="Enter current password"
            />
          )}
          <Input
            label="New Password"
            type="password"
            value={passwordData.newPassword}
            onChange={(e) => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
            placeholder="Enter new password (min 6 characters)"
          />
          <Input
            label="Confirm New Password"
            type="password"
            value={passwordData.confirmPassword}
            onChange={(e) => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
            placeholder="Confirm new password"
          />
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={isDeleteConfirmOpen}
        onClose={() => {
          setIsDeleteConfirmOpen(false);
          setUserToDelete(null);
        }}
        onConfirm={handleDeleteConfirm}
        title="Delete User"
        message={`Are you sure you want to delete user "${userToDelete?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </PageContainer>
  );
}

