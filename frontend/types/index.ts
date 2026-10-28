export type UserRole = "CUSTOMER" | "PHARMACY" | "ADMIN";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  phone?: string;
  zone: string;
  pharmacy?: PharmacyProfile;
}

export interface PharmacyProfile {
  pharmacy_name: string;
  license_number: string;
  address: string;
  zone: string;
  is_active: boolean;
}

export interface Medicine {
  id: number;
  name: string;
  generic_name?: string;
  manufacturer?: string;
  category: string;
  dosage_form?: string;
  pack_size?: string;
  mrp: number;
  requires_prescription: boolean;
  is_active?: boolean;
}

export interface CartItem {
  medicine: Medicine;
  quantity: number;
  subtotal_mrp: number;
}

export type OrderStatus =
  | "BROADCASTING"
  | "PENDING_SELECTION"
  | "CONFIRMED_PENDING_PHARMACY"
  | "CONFIRMED"
  | "REJECTED"
  | "PREPARING"
  | "DISPATCHED"
  | "DELIVERED"
  | "EXPIRED"
  | "CANCELLED";

export interface OrderItem {
  id: number;
  medicine_id: number;
  medicine_name: string;
  dosage_form?: string;
  pack_size?: string;
  requires_prescription: boolean;
  quantity: number;
  unit_mrp: number;
  subtotal_mrp: number;
}

export interface Order {
  id: number;
  customer_id?: number;
  customer_name?: string;
  customer_phone?: string;
  zone: string;
  delivery_address: string;
  status: OrderStatus;
  broadcast_started_at: string;
  broadcast_expires_at: string;
  remaining_broadcast_seconds: number;
  total_mrp: number;
  final_amount: number;
  mock_payment_status: "UNPAID" | "MOCK_PAID";
  item_count?: number;
  quote_count?: number;
  assigned_pharmacy?: {
    id: number;
    name: string;
    quote_id?: number;
    confirmation_status: "PENDING" | "CONFIRMED" | "REJECTED";
  } | null;
  items?: OrderItem[];
  created_at: string;
}

export interface QuoteItem {
  id: number;
  order_item_id: number;
  medicine_name: string;
  quantity: number;
  unit_mrp: number;
  is_available: boolean;
  unit_selling_price: number;
  subtotal_price: number;
  notes?: string;
}

export interface Quote {
  id: number;
  order_id: number;
  pharmacy_id: number;
  pharmacy_name: string;
  pharmacy_address: string;
  status: "SUBMITTED" | "SELECTED" | "REJECTED" | "EXPIRED";
  total_quoted_price: number;
  available_items_count: number;
  total_items_count: number;
  is_full_fulfillment: boolean;
  notes?: string;
  submitted_at: string;
  items?: QuoteItem[];
}

export interface AppNotification {
  id: number;
  title: string;
  message: string;
  event_type: string;
  reference_id?: number;
  is_read: boolean;
  created_at: string;
}
