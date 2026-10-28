import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert
} from "react-native";
import { Order, Quote } from "../../../types";
import { api } from "../../../services/api";
import { CountdownTimer } from "../../../components/CountdownTimer";
import { QuoteCard } from "../../../components/QuoteCard";
import { MockPaymentModal } from "../../../components/MockPaymentModal";
import { Colors } from "../../../constants/Config";

export default function OrderDetailsScreen({ route, navigation }: any) {
  const orderId = route?.params?.id;
  const [order, setOrder] = useState<Order | null>(null);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectingQuoteId, setSelectingQuoteId] = useState<number | null>(null);
  const [showPaymentModal, setShowPaymentModal] = useState<boolean>(false);

  const fetchOrderAndQuotes = async () => {
    try {
      const [orderRes, quotesRes] = await Promise.all([
        api.get<{ order: Order }>(`/orders/${orderId}`),
        api.get<{ quotes: Quote[] }>(`/orders/${orderId}/quotes`).catch(() => ({ quotes: [] }))
      ]);
      setOrder(orderRes.order);
      setQuotes(quotesRes.quotes);
    } catch (err: any) {
      console.error("Failed to load order details:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrderAndQuotes();
    const interval = setInterval(fetchOrderAndQuotes, 3500);
    return () => clearInterval(interval);
  }, [orderId]);

  const handleSelectPharmacy = (quote: Quote) => {
    const isPartial = !quote.is_full_fulfillment;
    const fulfillmentWarning = isPartial
      ? `\n\nNotice: This is a Partial Quote (${quote.available_items_count}/${quote.total_items_count} items). You will only be charged for available items ($${quote.total_quoted_price.toFixed(2)}).`
      : "";

    Alert.alert(
      "Confirm Pharmacy Selection",
      `Are you sure you want to award Order #${orderId} to ${quote.pharmacy_name} for $${quote.total_quoted_price.toFixed(2)}?${fulfillmentWarning}`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Select This Pharmacy",
          style: "default",
          onPress: async () => {
            try {
              setSelectingQuoteId(quote.id);
              await api.post(`/orders/${orderId}/select`, { quote_id: quote.id });
              Alert.alert(
                "Pharmacy Awarded!",
                `${quote.pharmacy_name} has received your order and was notified to confirm dispatch.`
              );
              fetchOrderAndQuotes();
            } catch (err: any) {
              Alert.alert("Selection Failed", err.message || "Failed to select pharmacy");
            } finally {
              setSelectingQuoteId(null);
            }
          }
        }
      ]
    );
  };

  const handleCancelOrder = async () => {
    Alert.alert(
      "Cancel Order",
      "Are you sure you want to cancel this broadcast? Participating pharmacies will be notified.",
      [
        { text: "No", style: "cancel" },
        {
          text: "Yes, Cancel",
          style: "destructive",
          onPress: async () => {
            try {
              await api.post(`/orders/${orderId}/cancel`, {});
              fetchOrderAndQuotes();
            } catch (err: any) {
              Alert.alert("Cancellation Failed", err.message || "Could not cancel");
            }
          }
        }
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  if (!order) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Order not found.</Text>
      </View>
    );
  }

  const isBroadcasting = order.status === "BROADCASTING";
  const isPendingSelection = order.status === "PENDING_SELECTION";
  const canSelectQuote = (isBroadcasting || isPendingSelection) && !order.assigned_pharmacy;
  const canCancel = (isBroadcasting || isPendingSelection) && !order.assigned_pharmacy;
  const isAwarded = !!order.assigned_pharmacy;
  const isPaid = order.mock_payment_status === "MOCK_PAID";

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 100 }}>
      {/* Live Quotes Status Banner (Customer Experience) */}
      {isBroadcasting && (
        <View style={styles.matchingBanner}>
          <Text style={styles.matchingTitle}>🟢 Requesting Quotes from Local Pharmacies</Text>
          <Text style={styles.matchingDesc}>
            Licensed pharmacies in {order.zone} are reviewing your medicine list and preparing competitive quotes.
          </Text>
        </View>
      )}

      {/* Status Bar */}
      <View style={styles.statusCard}>
        <View style={styles.statusHeader}>
          <Text style={styles.orderTitle}>Order #{order.id}</Text>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{order.status.replace(/_/g, " ")}</Text>
          </View>
        </View>

        <Text style={styles.metaText}>Delivery Zone: {order.zone}</Text>
        <Text style={styles.metaText}>Address: {order.delivery_address}</Text>

        {order.assigned_pharmacy && (
          <View style={styles.assignedBox}>
            <Text style={styles.assignedTitle}>AWARDED PHARMACY</Text>
            <Text style={styles.assignedName}>{order.assigned_pharmacy.name}</Text>
            <Text style={styles.assignedStatus}>
              Confirmation: {order.assigned_pharmacy.confirmation_status}
            </Text>
            <Text style={styles.finalPayableText}>
              Payable Total: ${order.final_amount.toFixed(2)}
            </Text>
          </View>
        )}

        {/* Mock Payment Status Card */}
        {isAwarded && (
          <View style={styles.paymentSection}>
            {isPaid ? (
              <View style={styles.paidBadge}>
                <Text style={styles.paidBadgeText}>✓ MOCK PAYMENT COMPLETED (SIMULATED)</Text>
              </View>
            ) : (
              <TouchableOpacity
                style={styles.mockPayBtn}
                onPress={() => setShowPaymentModal(true)}
              >
                <Text style={styles.mockPayBtnText}>
                  Proceed to Simulated Payment (${order.final_amount.toFixed(2)}) &rarr;
                </Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      </View>

      {/* Prescriptions & Line Items */}
      <View style={styles.itemsCard}>
        <Text style={styles.sectionTitle}>Catalogue Items Requested</Text>
        {order.items?.map((item) => (
          <View key={item.id} style={styles.itemRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.itemName}>{item.medicine_name}</Text>
              <Text style={styles.itemMeta}>
                Catalogue MRP: ${item.unit_mrp.toFixed(2)} • Qty: {item.quantity}
              </Text>
            </View>
            <Text style={styles.itemSubtotal}>${item.subtotal_mrp.toFixed(2)}</Text>
          </View>
        ))}

        <View style={styles.divider} />
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>Total Catalogue MRP:</Text>
          <Text style={styles.totalValue}>${order.total_mrp.toFixed(2)}</Text>
        </View>
      </View>

      {/* Submitted Pharmacy Quotes Section */}
      <View style={styles.quotesSection}>
        <View style={styles.quotesHeader}>
          <Text style={styles.sectionTitle}>Pharmacy Quotes ({quotes.length})</Text>
          {canSelectQuote && (
            <Text style={styles.selectHint}>Tap 'Select Pharmacy' to award the order</Text>
          )}
        </View>

        {quotes.length === 0 ? (
          <View style={styles.noQuotesBox}>
            <ActivityIndicator size="small" color={Colors.primary} style={{ marginBottom: 6 }} />
            <Text style={styles.noQuotesText}>
              Awaiting quotes from verified pharmacies in {order.zone}...
            </Text>
          </View>
        ) : (
          quotes.map((q) => {
            const isWinner = order.assigned_pharmacy?.quote_id === q.id;
            return (
              <QuoteCard
                key={q.id}
                quote={q}
                isSelectable={canSelectQuote && !isWinner}
                isWinningQuote={isWinner}
                onSelect={handleSelectPharmacy}
              />
            );
          })
        )}
      </View>

      {/* Cancel Order Action */}
      {canCancel && (
        <TouchableOpacity style={styles.cancelBtn} onPress={handleCancelOrder}>
          <Text style={styles.cancelBtnText}>Cancel Order Broadcast</Text>
        </TouchableOpacity>
      )}

      {/* Mock Payment Modal */}
      {showPaymentModal && (
        <MockPaymentModal
          visible={showPaymentModal}
          orderId={order.id}
          amount={order.final_amount}
          onClose={() => setShowPaymentModal(false)}
          onSuccess={fetchOrderAndQuotes}
        />
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background
  },
  matchingBanner: {
    backgroundColor: "#f0fdf4",
    borderWidth: 1.5,
    borderColor: "#bbf7d0",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16
  },
  matchingTitle: {
    fontSize: 14.5,
    fontWeight: "800",
    color: "#065f46",
    marginBottom: 4
  },
  matchingDesc: {
    fontSize: 12.5,
    color: Colors.textSecondary,
    lineHeight: 18
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center"
  },
  errorText: {
    fontSize: 16,
    color: Colors.danger
  },
  statusCard: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: Colors.border
  },
  statusHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8
  },
  orderTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: Colors.text
  },
  badge: {
    backgroundColor: "#e0f2fe",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6
  },
  badgeText: {
    color: Colors.primaryDark,
    fontSize: 11,
    fontWeight: "800"
  },
  metaText: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 3
  },
  assignedBox: {
    marginTop: 12,
    padding: 12,
    backgroundColor: "#f0fdf4",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#bbf7d0"
  },
  assignedTitle: {
    fontSize: 10,
    fontWeight: "800",
    color: "#166534",
    letterSpacing: 0.8
  },
  assignedName: {
    fontSize: 16,
    fontWeight: "800",
    color: "#166534",
    marginTop: 2
  },
  assignedStatus: {
    fontSize: 12,
    color: "#15803d",
    marginTop: 2
  },
  finalPayableText: {
    fontSize: 14,
    fontWeight: "800",
    color: "#166534",
    marginTop: 4
  },
  paymentSection: {
    marginTop: 12
  },
  paidBadge: {
    backgroundColor: "#dcfce7",
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#86efac"
  },
  paidBadgeText: {
    color: "#166534",
    fontSize: 12,
    fontWeight: "800"
  },
  mockPayBtn: {
    backgroundColor: Colors.secondary,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: "center"
  },
  mockPayBtnText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "800"
  },
  itemsCard: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: Colors.border
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text
  },
  itemRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#f1f5f9"
  },
  itemName: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text
  },
  itemMeta: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2
  },
  itemSubtotal: {
    fontSize: 14,
    fontWeight: "700",
    color: Colors.text
  },
  divider: {
    height: 1,
    backgroundColor: Colors.border,
    marginVertical: 12
  },
  totalRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  totalLabel: {
    fontSize: 14,
    fontWeight: "700",
    color: Colors.text
  },
  totalValue: {
    fontSize: 18,
    fontWeight: "800",
    color: Colors.primaryDark
  },
  quotesSection: {
    marginBottom: 14
  },
  quotesHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8
  },
  selectHint: {
    fontSize: 11,
    color: Colors.primaryDark,
    fontWeight: "600"
  },
  noQuotesBox: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 24,
    alignItems: "center",
    borderWidth: 1,
    borderColor: Colors.border
  },
  noQuotesText: {
    fontSize: 13,
    color: Colors.textSecondary,
    textAlign: "center"
  },
  cancelBtn: {
    backgroundColor: "#fee2e2",
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: "center",
    marginTop: 6
  },
  cancelBtnText: {
    color: Colors.danger,
    fontWeight: "700",
    fontSize: 14
  }
});
