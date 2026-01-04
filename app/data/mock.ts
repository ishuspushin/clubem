import {
  User,
  Platform,
  Upload,
  Order,
  DashboardStats,
  FieldConfig,
  ProcessConfig,
  GuestItem
} from '@/app/types';

// Mock Users
export const mockUsers: User[] = [
  {
    id: '1',
    name: 'Admin User',
    email: 'admin@clubem.com',
    role: 'admin',
    status: 'active',
    createdAt: '2024-01-15',
  },
  {
    id: '2',
    name: 'Sarah Johnson',
    email: 'sarah@clubem.com',
    role: 'staff',
    status: 'active',
    createdAt: '2024-02-20',
  },
  {
    id: '3',
    name: 'Mike Chen',
    email: 'mike@clubem.com',
    role: 'staff',
    status: 'active',
    createdAt: '2024-03-10',
  },
  {
    id: '4',
    name: 'Emily Davis',
    email: 'emily@clubem.com',
    role: 'staff',
    status: 'inactive',
    createdAt: '2024-01-25',
  },
];

// Mock Platforms
export const mockPlatforms: Platform[] = [
  { id: '1', name: 'Grubhub', status: 'active', lastUpdated: '2024-12-15' },
  { id: '2', name: 'Forkable', status: 'active', lastUpdated: '2024-12-14' },
  { id: '3', name: 'Sharebite', status: 'active', lastUpdated: '2024-12-10' },
  { id: '4', name: 'CaterCow', status: 'active', lastUpdated: '2024-12-08' },
  { id: '5', name: 'EzCater', status: 'active', lastUpdated: '2024-12-05' },
  { id: '6', name: 'Hungry', status: 'active', lastUpdated: '2024-12-01' },
  { id: '7', name: 'ClubFeast', status: 'disabled', lastUpdated: '2024-11-20' },
];

// Mock Uploads
export const mockUploads: Upload[] = [
  {
    id: '1',
    fileName: 'grubhub_order_2024_001.pdf',
    platform: 'Grubhub',
    uploadedBy: 'Sarah Johnson',
    uploadedAt: '2024-12-19 09:30',
    status: 'completed',
  },
  {
    id: '2',
    fileName: 'ezcater_group_lunch.pdf',
    platform: 'EzCater',
    uploadedBy: 'Mike Chen',
    uploadedAt: '2024-12-19 10:15',
    status: 'processing',
  },
  {
    id: '3',
    fileName: 'sharebite_holiday_party.pdf',
    platform: 'Sharebite',
    uploadedBy: 'Sarah Johnson',
    uploadedAt: '2024-12-19 11:00',
    status: 'pending',
  },
  {
    id: '4',
    fileName: 'catercow_team_meeting.pdf',
    platform: 'CaterCow',
    uploadedBy: 'Emily Davis',
    uploadedAt: '2024-12-18 14:30',
    status: 'failed',
  },
  {
    id: '5',
    fileName: 'forkable_weekly_order.pdf',
    platform: 'Forkable',
    uploadedBy: 'Mike Chen',
    uploadedAt: '2024-12-18 16:45',
    status: 'completed',
  },
];

// Mock Guest Items
const mockGuestItems1: GuestItem[] = [
  {
    id: 'g1',
    guest_name: 'John Smith',
    item_name: 'Grilled Chicken Sandwich',
    modifications: ['No mayo', 'extra pickles'],
    comments: 'Gluten-free bun if available',
  },
  {
    id: 'g2',
    guest_name: 'Jane Doe',
    item_name: 'Caesar Salad',
    modifications: ['Dressing on the side'],
    comments: '',
  },
  {
    id: 'g3',
    guest_name: 'Bob Wilson',
    item_name: 'Turkey Club',
    modifications: ['Whole wheat bread'],
    comments: 'Extra napkins please',
  },
  {
    id: 'g4',
    guest_name: 'Alice Brown',
    item_name: 'Veggie Wrap',
    modifications: ['No onions', 'add avocado'],
    comments: 'Nut allergy - no cross contamination',
  },
];

const mockGuestItems2: GuestItem[] = [
  {
    id: 'g5',
    guest_name: 'Tom Harris',
    item_name: 'BBQ Pulled Pork',
    modifications: ['Extra sauce'],
    comments: '',
  },
  {
    id: 'g6',
    guest_name: 'Lisa Wang',
    item_name: 'Garden Salad',
    modifications: ['Vegan dressing'],
    comments: 'Vegan diet',
  },
];

// Mock Orders
export const mockOrders: Order[] = [
  {
    id: 'ORD-001',
    businessClient: 'Acme Corp',
    clientName: 'Jennifer Martinez',
    groupOrderNumber: 'GRP-2024-1201',
    requestedDate: '2024-12-20',
    numberOfGuests: 4,
    deliveryMode: 'delivery',
    status: 'confirmed',
    currentStep: 'email',
    orderSubtotal: 87.50,
    clientInfo: '123 Business Ave, Suite 400',
    pickupTime: '12:00 PM',
    items: mockGuestItems1,
    uploadedBy: 'Sarah Johnson',
    createdAt: '2024-12-19 09:30',
  },
  {
    id: 'ORD-002',
    businessClient: 'TechStart Inc',
    clientName: 'David Kim',
    groupOrderNumber: 'GRP-2024-1202',
    requestedDate: '2024-12-20',
    numberOfGuests: 2,
    deliveryMode: 'pickup',
    status: 'processing',
    currentStep: 'extraction',
    orderSubtotal: 42.00,
    clientInfo: '456 Innovation Blvd',
    pickupTime: '1:30 PM',
    items: mockGuestItems2,
    uploadedBy: 'Mike Chen',
    createdAt: '2024-12-19 10:15',
  },
  {
    id: 'ORD-003',
    businessClient: 'Global Finance',
    clientName: 'Robert Taylor',
    groupOrderNumber: 'GRP-2024-1203',
    requestedDate: '2024-12-21',
    numberOfGuests: 25,
    deliveryMode: 'delivery',
    status: 'needs_review',
    currentStep: 'formatting',
    orderSubtotal: 525.00,
    clientInfo: '789 Wall Street, Floor 12',
    pickupTime: '11:30 AM',
    items: [
      ...mockGuestItems1,
      ...mockGuestItems2,
      {
        id: 'g7',
        guest_name: 'Chris Anderson',
        item_name: 'Steak Burrito',
        modifications: ['No sour cream'],
        comments: '',
      },
    ],
    uploadedBy: 'Sarah Johnson',
    createdAt: '2024-12-19 11:00',
  },
  {
    id: 'ORD-004',
    businessClient: 'Creative Agency',
    clientName: 'Amanda Lee',
    groupOrderNumber: 'GRP-2024-1204',
    requestedDate: '2024-12-19',
    numberOfGuests: 8,
    deliveryMode: 'delivery',
    status: 'failed',
    currentStep: 'ocr',
    orderSubtotal: 156.00,
    clientInfo: '321 Design District',
    pickupTime: '12:30 PM',
    items: mockGuestItems1,
    uploadedBy: 'Emily Davis',
    createdAt: '2024-12-18 14:30',
  },
  {
    id: 'ORD-005',
    businessClient: 'Law Partners LLP',
    clientName: 'Michael Scott',
    groupOrderNumber: 'GRP-2024-1205',
    requestedDate: '2024-12-22',
    numberOfGuests: 12,
    deliveryMode: 'pickup',
    status: 'confirmed',
    currentStep: 'email',
    orderSubtotal: 284.00,
    clientInfo: '555 Legal Plaza',
    pickupTime: '12:00 PM',
    items: [...mockGuestItems1, ...mockGuestItems2],
    uploadedBy: 'Mike Chen',
    createdAt: '2024-12-18 16:45',
  },
];

// Dashboard Stats
export const mockDashboardStats: DashboardStats = {
  totalUploads: 156,
  ordersProcessedToday: 12,
  failedOrders: 3,
  pendingReview: 7,
};

// Mock Field Configurations
export const mockFieldConfigs: FieldConfig[] = [
  {
    id: '1',
    name: 'Business Client',
    type: 'text',
    required: true,
    description: 'Name of the business placing the order',
  },
  {
    id: '2',
    name: 'Client Name',
    type: 'text',
    required: true,
    description: 'Contact person name',
  },
  {
    id: '3',
    name: 'Group Order Number',
    type: 'text',
    required: true,
    description: 'Unique identifier for the group order',
  },
  {
    id: '4',
    name: 'Requested Date',
    type: 'date',
    required: true,
    description: 'Date when order is needed',
  },
  {
    id: '5',
    name: 'Number of Guests',
    type: 'number',
    required: true,
    description: 'Total number of guests in the order',
  },
  {
    id: '6',
    name: 'Delivery Mode',
    type: 'select',
    required: true,
    description: 'Pickup or Delivery',
  },
  {
    id: '7',
    name: 'Order Subtotal',
    type: 'number',
    required: false,
    description: 'Total order amount before tax',
  },
  {
    id: '8',
    name: 'Pickup Time',
    type: 'text',
    required: true,
    description: 'Scheduled pickup or delivery time',
  },
];

// Mock Process Configurations
export const mockProcessConfigs: ProcessConfig[] = [
  {
    id: '1',
    name: 'Standard Processing',
    description: 'Default processing flow for all orders',
    steps: ['OCR Scan', 'Data Extraction', 'Validation', 'Formatting', 'Email Delivery'],
    isActive: true,
  },
  {
    id: '2',
    name: 'Express Processing',
    description: 'Fast-track processing for urgent orders',
    steps: ['Quick Scan', 'Auto-Extract', 'Send'],
    isActive: true,
  },
  {
    id: '3',
    name: 'Manual Review',
    description: 'Orders requiring human verification',
    steps: ['OCR Scan', 'Data Extraction', 'Manual Review', 'Approval', 'Formatting', 'Email Delivery'],
    isActive: true,
  },
];

// Helper to get user by email (for mock auth)
export const findUserByEmail = (email: string): User | undefined => {
  return mockUsers.find(u => u.email === email);
};

// Helper to get orders by user
export const getOrdersByUser = (email: string): Order[] => {
  return mockOrders.filter(o => o.uploadedBy === email);
};

// Helper to get uploads by user
export const getUploadsByUser = (email: string): Upload[] => {
  return mockUploads.filter(u => u.uploadedBy === email);
}

