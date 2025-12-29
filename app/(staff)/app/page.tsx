'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { PageContainer } from '@/app/components/layout/PageContainer';
import { Card, CardHeader } from '@/app/components/ui/Card';
import { Button } from '@/app/components/ui/Button';
import { Badge } from '@/app/components/ui/Badge';
import { FileDropzone } from '@/app/components/ui/FileDropzone';
import { Platform } from '@/app/types';
import { UploadIcon, CheckIcon, XIcon } from '@/app/components/icons';
import { useAuth } from '@/app/context/AuthContext';
import { useToast } from '@/app/components/ui/Toast';
import { Modal } from '@/app/components/ui/Modal';
import { Input } from '@/app/components/ui/Input';

export default function UploadOrdersPage() {
  const router = useRouter();
  const { user } = useAuth();
  const toast = useToast();
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [allPlatforms, setAllPlatforms] = useState<Platform[]>([]); // All platforms including disabled
  const [selectedPlatform, setSelectedPlatform] = useState<string>('');
  const [platformFiles, setPlatformFiles] = useState<Record<string, File[]>>({});
  const [isLoadingPlatforms, setIsLoadingPlatforms] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState(false);
  const [newOrderId, setNewOrderId] = useState<string | null>(null);
  const [isCreateOrderModalOpen, setIsCreateOrderModalOpen] = useState(false);
  const [platformSearch, setPlatformSearch] = useState('');

  const fetchPlatforms = useCallback(async () => {
    try {
      setIsLoadingPlatforms(true);
      if (!user?.id) {
        setIsLoadingPlatforms(false);
        return;
      }

      const response = await fetch(`/api/platforms?userId=${user.id}`);
      if (!response.ok) throw new Error('Failed to fetch platforms');
      const data = await response.json();
      // Set all platforms for main page display
      setAllPlatforms(data.platforms);
      // Set only active platforms for modal
      const activePlatforms = data.platforms.filter((p: Platform) => p.status === 'active');
      setPlatforms(activePlatforms);
    } catch (error) {
      console.error('Error fetching platforms:', error);
      toast.error('Failed to load platforms');
    } finally {
      setIsLoadingPlatforms(false);
    }
  }, [user?.id, toast]);

  // Fetch platforms from API
  useEffect(() => {
    fetchPlatforms();
  }, [fetchPlatforms]);

  const handleFilesSelected = (selectedFiles: File[]) => {
    if (!selectedPlatform) {
      toast.warning('Please select a platform first');
      return;
    }

    setPlatformFiles(prev => ({
      ...prev,
      [selectedPlatform]: [...(prev[selectedPlatform] || []), ...selectedFiles],
    }));
    setUploadComplete(false);

    // Clear selected platform after files are uploaded to show all uploads
    setSelectedPlatform('');
  };

  const handleRemoveFile = (platformId: string, index: number) => {
    setPlatformFiles(prev => ({
      ...prev,
      [platformId]: prev[platformId]?.filter((_, i) => i !== index) || [],
    }));
  };

  const handleClearPlatform = (platformId: string) => {
    setPlatformFiles(prev => {
      const updated = { ...prev };
      delete updated[platformId];
      return updated;
    });
  };

  const getTotalFiles = () => {
    return Object.values(platformFiles).reduce((sum, files) => sum + files.length, 0);
  };

  const handleUpload = async () => {
    const totalFiles = getTotalFiles();
    if (totalFiles === 0) {
      toast.warning('Please upload at least one file');
      return;
    }

    if (!user?.id) {
      toast.error('You must be logged in to upload');
      return;
    }

    setIsUploading(true);

    try {
      // We'll process each platform's files as separate orders or merge them?
      // For now, the schema supports one platform per order.
      // If multiple platforms were selected, we might need to handle that.
      // The current UI allows multiple platforms. Let's create one order per platform for now
      // OR just pick the first platform for the order.
      
      const platformIds = Object.keys(platformFiles);
      
      for (const pId of platformIds) {
        const files = platformFiles[pId];
        if (files.length === 0) continue;

        const formData = new FormData();
        formData.append('userId', user.id);
        formData.append('platformId', pId);
        files.forEach(file => {
          formData.append('files', file);
        });

        const response = await fetch('/api/orders', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || `Failed to upload files for platform ${pId}`);
        }

        const data = await response.json();
        setNewOrderId(data.orderId);
      }

      setIsUploading(false);
      setUploadComplete(true);
      toast.success('Order(s) created successfully');

      // Clear files but keep modal open to show success message
      setPlatformFiles({});
      setSelectedPlatform('');
    } catch (error: any) {
      console.error('Upload error:', error);
      toast.error(error.message || 'Failed to upload files');
      setIsUploading(false);
    }
  };

  const handleViewOrder = () => {
    if (newOrderId) {
      router.push(`/app/orders/${newOrderId}`);
    }
  };

  const handleNewUpload = () => {
    setPlatformFiles({});
    setSelectedPlatform('');
    setUploadComplete(false);
    setNewOrderId(null);
    setIsCreateOrderModalOpen(false);
  };

  const handleCloseAfterSuccess = () => {
    setUploadComplete(false);
    setNewOrderId(null);
    setIsCreateOrderModalOpen(false);
  };

  const handleOpenCreateOrder = () => {
    setIsCreateOrderModalOpen(true);
  };

  const handleCloseCreateOrder = () => {
    if (!isUploading) {
      setIsCreateOrderModalOpen(false);
    }
  };

  // Filter platforms based on search
  const filteredPlatforms = platforms.filter(platform =>
    platform.name.toLowerCase().includes(platformSearch.toLowerCase())
  );

  return (
    <PageContainer
      title="Upload Orders"
      description="Upload PDF files from supported food ordering platforms"
    >
      {!uploadComplete ? (
        <div className="space-y-6">
          {/* Main Action Card */}
          <Card>
            <CardHeader
              title="Create New Order"
              description="Click the button below to start uploading PDF files from multiple platforms"
            />
            <div className="pt-4">
              <Button
                onClick={handleOpenCreateOrder}
                size="lg"
                leftIcon={<UploadIcon className="w-5 h-5" />}
                className="w-full sm:w-auto"
              >
                Create Order
              </Button>
            </div>
          </Card>

          {/* Supported Platforms Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader
                title="Supported Platforms"
                description="We accept PDF orders from these platforms"
              />
              {isLoadingPlatforms ? (
                <div className="p-4 text-center text-slate-500">Loading platforms...</div>
              ) : (
                <ul className="space-y-2">
                  {allPlatforms.map(platform => (
                    <li
                      key={platform.id}
                      className={`flex items-center justify-between px-3 py-2 rounded-md ${platform.status === 'active' ? 'bg-slate-50' : 'bg-slate-100 opacity-60'
                        }`}
                    >
                      <span className={`text-sm font-medium ${platform.status === 'active' ? 'text-slate-700' : 'text-slate-500'
                        }`}>
                        {platform.name}
                      </span>
                      <Badge variant={platform.status === 'active' ? 'success' : 'default'}>
                        {platform.status === 'active' ? 'Active' : 'Disabled'}
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card>
              <CardHeader title="Upload Tips" />
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-start gap-2">
                  <span className="text-slate-400">•</span>
                  Select a platform, upload files, then select another platform to add more
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-400">•</span>
                  Upload up to 7 PDF files per platform
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-400">•</span>
                  Maximum file size: 10MB per file
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-400">•</span>
                  Include cover sheets and order labels
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-slate-400">•</span>
                  All files from all platforms will be included in one order
                </li>
              </ul>
            </Card>
          </div>
        </div>
      ) : (
        <Card>
          <div className="text-center py-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 rounded-full mb-4">
              <CheckIcon className="w-8 h-8 text-emerald-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">
              Upload Successful!
            </h3>
            <p className="text-sm text-slate-600 mb-6">
              Your files have been uploaded and order <span className="font-mono font-medium">{newOrderId}</span> is now being processed.
            </p>
            <div className="flex justify-center gap-3">
              <Button onClick={handleViewOrder}>
                View Order
              </Button>
              <Button variant="secondary" onClick={handleNewUpload}>
                Upload More
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Create Order Modal - Full Page */}
      <Modal
        isOpen={isCreateOrderModalOpen}
        onClose={handleCloseCreateOrder}
        title="Create New Order"
        size="xl"
        footer={
          <div className="flex items-center justify-between w-full min-w-0 h-[72px]">
            {getTotalFiles() > 0 ? (
              <>
                <div className="min-w-0 shrink">
                  <p className="text-sm font-medium text-slate-900 truncate">
                    {getTotalFiles()} file{getTotalFiles() > 1 ? 's' : ''} from {Object.keys(platformFiles).length} platform{Object.keys(platformFiles).length > 1 ? 's' : ''}
                  </p>
                </div>
                <div className="flex gap-3 shrink-0">
                  <Button
                    variant="secondary"
                    onClick={handleNewUpload}
                    disabled={isUploading}
                  >
                    Clear All
                  </Button>
                  <Button
                    onClick={handleUpload}
                    isLoading={isUploading}
                    leftIcon={<UploadIcon className="w-4 h-4" />}
                    size="lg"
                  >
                    {isUploading
                      ? 'Creating Order...'
                      : `Create Order with ${getTotalFiles()} File${getTotalFiles() > 1 ? 's' : ''}`
                    }
                  </Button>
                </div>
              </>
            ) : (
              <div className="w-full" /> // Empty spacer to maintain height
            )}
          </div>
        }
      >
        {uploadComplete ? (
          // Show success message full width
          <div className="flex flex-col items-center justify-center h-[calc(100vh-15rem)] w-full">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 rounded-full mb-4">
                <CheckIcon className="w-8 h-8 text-emerald-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                Order Created Successfully!
              </h3>
              <p className="text-sm text-slate-600 mb-6">
                Your order <span className="font-mono font-medium">{newOrderId}</span> has been created and is now being processed.
              </p>
              <div className="flex justify-center gap-3">
                <Button onClick={handleViewOrder}>
                  View Order
                </Button>
                <Button variant="secondary" onClick={handleNewUpload}>
                  Create Another Order
                </Button>
                <Button variant="ghost" onClick={handleCloseAfterSuccess}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex gap-6 h-[calc(100vh-15rem)] overflow-hidden">
            {/* Left Side - Platform Selection */}
            <div className="w-80 shrink-0 border-r border-slate-200 pr-6 flex flex-col">
              <div className="shrink-0">
                <h3 className="text-sm font-semibold text-slate-900 mb-4">Select Platform</h3>

                {/* Search Input */}
                <div className="mb-4 w-full pl-1">
                  <Input
                    type="text"
                    placeholder="Search platforms..."
                    value={platformSearch}
                    onChange={(e) => setPlatformSearch(e.target.value)}
                    disabled={isLoadingPlatforms || isUploading}
                    className="w-full"
                  />
                </div>
              </div>

              {/* Platform List - Clickable with scroll */}
              <div className="flex-1 overflow-y-auto min-h-0">
                <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wide mb-3">
                  Platforms
                </h4>
                {isLoadingPlatforms ? (
                  <div className="p-4 text-center text-slate-500 text-sm">Loading platforms...</div>
                ) : filteredPlatforms.length === 0 ? (
                  <div className="p-4 text-center text-slate-500 text-sm">No platforms found</div>
                ) : (
                  <ul className="space-y-2">
                    {filteredPlatforms.map(platform => (
                      <li
                        key={platform.id}
                        className={`
                          px-4 py-3 rounded-lg cursor-pointer transition-all
                          border-2
                          ${selectedPlatform === platform.id
                            ? 'bg-slate-100 border-slate-400 shadow-sm'
                            : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50 hover:shadow-sm'
                          }
                          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
                        `}
                        onClick={() => {
                          if (isUploading) return;
                          // Toggle platform selection
                          if (selectedPlatform === platform.id) {
                            setSelectedPlatform('');
                          } else {
                            setSelectedPlatform(platform.id);
                          }
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`text-sm font-medium ${selectedPlatform === platform.id ? 'text-slate-900' : 'text-slate-700'}`}>
                            {platform.name}
                          </span>
                          {platformFiles[platform.id] && platformFiles[platform.id].length > 0 && (
                            <CheckIcon className="w-4 h-4 text-emerald-600" />
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Right Side - Upload Area or Uploaded Files */}
            <div className="flex-1 min-w-0 overflow-y-auto">
              {selectedPlatform && Object.keys(platformFiles).length === 0 ? (
                // Show upload area when platform is selected but no files yet
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 mb-4">
                    Upload Files - {platforms.find(p => p.id === selectedPlatform)?.name}
                  </h3>
                  <div className="flex flex-col items-center justify-center h-96 border-2 border-dashed border-slate-300 rounded-lg bg-slate-50">
                    <FileDropzone
                      onFilesSelected={handleFilesSelected}
                      accept=".pdf"
                      multiple
                      maxFiles={7}
                      maxSize={10 * 1024 * 1024}
                      disabled={isUploading}
                    />
                  </div>
                </div>
              ) : selectedPlatform && Object.keys(platformFiles).length > 0 && !platformFiles[selectedPlatform]?.length ? (
                // Show upload area when platform is selected but no files for this platform yet
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 mb-4">
                    Upload Files - {platforms.find(p => p.id === selectedPlatform)?.name}
                  </h3>
                  <div className="flex flex-col items-center justify-center h-96 border-2 border-dashed border-slate-300 rounded-lg bg-slate-50">
                    <FileDropzone
                      onFilesSelected={handleFilesSelected}
                      accept=".pdf"
                      multiple
                      maxFiles={7}
                      maxSize={10 * 1024 * 1024}
                      disabled={isUploading}
                    />
                  </div>
                </div>
              ) : !selectedPlatform && Object.keys(platformFiles).length === 0 ? (
                // Show empty state when no platform selected and no files
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 mb-4">
                    Uploaded Files
                  </h3>
                  <div className="flex flex-col items-center justify-center h-96 border-2 border-dashed border-slate-300 rounded-lg bg-slate-50">
                    <div className="p-3 bg-slate-200 rounded-full mb-4">
                      <UploadIcon className="w-8 h-8 text-slate-500" />
                    </div>
                    <p className="text-sm font-medium text-slate-700 mb-1">
                      Click a platform to upload files
                    </p>
                    <p className="text-xs text-slate-500 text-center max-w-sm">
                      Select a platform on the left to start uploading PDF files
                    </p>
                  </div>
                </div>
              ) : (
                // Show all uploaded files
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 mb-4">
                    Uploaded Files
                    {getTotalFiles() > 0 && (
                      <span className="ml-2 text-slate-500 font-normal">
                        ({getTotalFiles()} total)
                      </span>
                    )}
                  </h3>
                  <div className="space-y-6">
                    {Object.entries(platformFiles).map(([platformId, files]) => {
                      const platform = platforms.find(p => p.id === platformId);
                      if (!files.length) return null;

                      return (
                        <div key={platformId} className="border border-slate-200 rounded-lg p-4 bg-slate-50">
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                              <h4 className="font-semibold text-slate-900">{platform?.name}</h4>
                              <Badge variant="info">{files.length} file{files.length > 1 ? 's' : ''}</Badge>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleClearPlatform(platformId)}
                              disabled={isUploading}
                            >
                              <XIcon className="w-4 h-4" />
                            </Button>
                          </div>

                          {/* Files Grid - Side by Side */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                            {files.map((file, index) => (
                              <div
                                key={`${platformId}-${index}`}
                                className="flex items-center gap-3 p-3 bg-white rounded-md border border-slate-200 shadow-sm"
                              >
                                <div className="shrink-0">
                                  <svg
                                    className="w-8 h-8 text-red-500"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                  >
                                    <path
                                      strokeLinecap="round"
                                      strokeLinejoin="round"
                                      strokeWidth={1.5}
                                      d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                                    />
                                  </svg>
                                </div>
                                <div className="min-w-0 flex-1">
                                  <p className="text-sm font-medium text-slate-700 truncate">
                                    {file.name}
                                  </p>
                                  <p className="text-xs text-slate-500">
                                    {(file.size / 1024).toFixed(1)} KB
                                  </p>
                                </div>
                                <button
                                  onClick={() => handleRemoveFile(platformId, index)}
                                  disabled={isUploading}
                                  className="shrink-0 p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                                >
                                  <XIcon className="w-4 h-4" />
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </PageContainer>
  );
}

