'use client';

import React, { useEffect, useCallback } from 'react';
import { Button } from './Button';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

const sizeStyles = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'w-[calc(100vw-2rem)] max-w-6xl max-h-[calc(100vh - 2rem)]',
  full: 'max-w-[95vw] max-h-[95vh]',
};

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
}: ModalProps) {
  const handleEscape = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, handleEscape]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className={`flex ${size === 'full' ? 'min-h-full' : 'min-h-full items-center justify-center'} ${size === 'full' ? 'p-4' : 'p-4'}`}>
        <div
          className={`
            relative w-full ${sizeStyles[size]} 
            ${size === 'full' ? 'rounded-lg' : 'rounded-lg'} shadow-xl 
            transform transition-all bg-white
            ${size === 'full' || size === 'xl' ? 'flex flex-col' : ''}
          `}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className={`flex items-center justify-between ${size === 'full' ? 'px-8 py-6' : 'px-6 py-4'} border-b border-slate-200 bg-white`}>
            <h2 className={`${size === 'full' ? 'text-xl' : 'text-lg'} font-semibold text-slate-900`}>{title}</h2>
            <button
              onClick={onClose}
              className="p-1 text-slate-400 hover:text-slate-600 transition-colors rounded-md hover:bg-slate-100"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className={`${size === 'full' ? 'flex-1 overflow-hidden px-8 py-6 bg-white' : 'px-6 py-4 bg-white overflow-hidden'}`}>{children}</div>

          {/* Footer - Always render to maintain consistent modal size */}
          <div className={`${size === 'full' ? 'px-8 py-6' : 'px-6 py-4'} border-t border-slate-200 bg-white shrink-0`}>
            {footer}
          </div>
        </div>
      </div>
    </div>
  );
}

// Confirm dialog variant
interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'default';
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'default',
}: ConfirmDialogProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            {cancelText}
          </Button>
          <Button
            variant={variant === 'danger' ? 'danger' : 'primary'}
            onClick={() => {
              onConfirm();
              onClose();
            }}
          >
            {confirmText}
          </Button>
        </>
      }
    >
      <p className="text-sm text-slate-600">{message}</p>
    </Modal>
  );
}

