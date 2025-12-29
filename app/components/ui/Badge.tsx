import React from 'react';

type BadgeVariant =
  | 'default'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'processing';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-slate-100 text-slate-700',
  success: 'bg-emerald-100 text-emerald-700',
  warning: 'bg-amber-100 text-amber-700',
  danger: 'bg-red-100 text-red-700',
  info: 'bg-sky-100 text-sky-700',
  processing: 'bg-violet-100 text-violet-700',
};

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-0.5 
        rounded-full text-xs font-medium
        ${variantStyles[variant]}
        ${className}
      `}
    >
      {children}
    </span>
  );
}

// Helper function to get badge variant from status
export function getStatusBadgeVariant(status: string): BadgeVariant {
  const normalizedStatus = status.toLowerCase();
  const statusMap: Record<string, BadgeVariant> = {
    // Order statuses
    processing: 'processing',
    needs_review: 'warning',
    needs_manual_review: 'warning',
    ready_to_send: 'info',
    sent: 'success',
    failed: 'danger',
    // Upload statuses
    pending: 'default',
    completed: 'success',
    // User/Platform statuses
    active: 'success',
    inactive: 'default',
    disabled: 'default',
  };

  return statusMap[normalizedStatus] || 'default';
}

// Helper to format status for display
export function formatStatus(status: string): string {
  return status
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

