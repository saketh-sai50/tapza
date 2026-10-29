import { API_BASE_URL } from "../config";

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  try {
    const res = await fetch(url, { ...options, headers });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || `Request failed with status ${res.status}`);
    }
    return data;
  } catch (err) {
    console.error(`API Error on [${options.method || "GET"}] ${url}:`, err.message);
    throw err;
  }
}

// 1. Authentication
export const authApi = {
  login: (email, password, role) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, role })
    }),
  register: (payload) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  getMe: (token) =>
    request("/auth/me", {
      headers: { Authorization: `Bearer ${token}` }
    })
};

// 2. Medicines Catalog
export const medicinesApi = {
  search: (query = "", category = "", limit = 50) => {
    const params = new URLSearchParams();
    if (query) params.append("q", query);
    if (category) params.append("category", category);
    if (limit) params.append("limit", String(limit));
    return request(`/medicines?${params.toString()}`);
  }
};

// 3. Customer Orders
export const ordersApi = {
  createOrder: (items, deliveryAddress, zone, token) =>
    request("/orders", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        items,
        delivery_address: deliveryAddress,
        zone
      })
    }),
  createPrescriptionOrder: (prescriptionImage, notes, deliveryAddress, zone, token) =>
    request("/orders/prescription", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        prescription_image: prescriptionImage,
        notes,
        delivery_address: deliveryAddress,
        zone
      })
    }),
  getMyOrders: (token) =>
    request("/orders/my-orders", {
      headers: { Authorization: `Bearer ${token}` }
    }),
  getOrderDetails: (orderId, token) =>
    request(`/orders/${orderId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
};

// 4. Reverse Auction Quotes
export const quotesApi = {
  getOrderQuotes: (orderId, token) =>
    request(`/orders/${orderId}/quotes`, {
      headers: { Authorization: `Bearer ${token}` }
    }),
  selectWinningQuote: (orderId, quoteId, token) =>
    request(`/orders/${orderId}/select`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ quote_id: quoteId })
    }),
  mockPay: (orderId, token) =>
    request(`/orders/${orderId}/mock-pay`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` }
    })
};

// 5. Pharmacy Radar & Bidding
export const pharmacyApi = {
  getBroadcasts: (token) =>
    request("/pharmacy/broadcasts", {
      headers: { Authorization: `Bearer ${token}` }
    }),
  submitQuote: (orderId, items, notes, token) =>
    request("/quotes", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        order_id: orderId,
        items,
        notes: notes || null
      })
    }),
  getAssignedOrders: (token) =>
    request("/pharmacy/orders", {
      headers: { Authorization: `Bearer ${token}` }
    })
};
