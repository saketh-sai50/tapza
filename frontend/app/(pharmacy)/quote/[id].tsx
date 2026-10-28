import React, { useState, useEffect, useMemo } from "react";
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Switch,
  StyleSheet,
  ActivityIndicator,
  Alert
} from "react-native";
import { api } from "../../../services/api";
import { Order, OrderItem } from "../../../types";
import { CountdownTimer } from "../../../components/CountdownTimer";
import { Colors } from "../../../constants/Config";

export default function SubmitQuoteScreen({ route, navigation }: any) {
  const orderId = route?.params?.id;

  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [notes, setNotes] = useState<string>("");

  // Quoting state per item
  const [itemQuotes, setItemQuotes] = useState<
    Record<number, { is_available: boolean; unit_selling_price: string; notes: string }>
  >({});

  const fetchOrder = async () => {
    try {
      const res = await api.get<{ order: Order }>(`/orders/${orderId}`);
      setOrder(res.order);

      // Prepopulate item quotes
      const initialMap: Record<number, any> = {};
      res.order.items?.forEach((item) => {
        initialMap[item.id] = {
          is_available: true,
          unit_selling_price: String(item.unit_mrp),
          notes: ""
        };
      });
      setItemQuotes(initialMap);
    } catch (err) {
      console.error("Failed to load order:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrder();
  }, [orderId]);

  const toggleAvailability = (itemId: number) => {
    setItemQuotes((prev) => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        is_available: !prev[itemId]?.is_available
      }
    }));
  };

  const updatePrice = (itemId: number, priceStr: string) => {
    setItemQuotes((prev) => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        unit_selling_price: priceStr
      }
    }));
  };

  // Live calculation of quoted total (strictly zero for unavailable items)
  const quoteCalculation = useMemo(() => {
    if (!order?.items) return { total: 0, availableCount: 0, totalCount: 0, isFull: false };

    let sum = 0;
    let availCount = 0;
    const totalCount = order.items.length;

    order.items.forEach((item) => {
      const q = itemQuotes[item.id];
      if (q && q.is_available) {
        const unit = parseFloat(q.unit_selling_price) || 0;
        sum += unit * item.quantity;
        availCount += 1;
      }
    });

    return {
      total: Number(sum.toFixed(2)),
      availableCount: availCount,
      totalCount,
      isFull: availCount === totalCount
    };
  }, [order, itemQuotes]);

  const handleSubmitQuote = async () => {
    if (quoteCalculation.availableCount === 0) {
      Alert.alert("Invalid Quote", "You must mark at least one medicine as available to quote.");
      return;
    }

    try {
      setSubmitting(true);
      const itemsPayload = order?.items?.map((item) => {
        const q = itemQuotes[item.id] || { is_available: false, unit_selling_price: "0", notes: "" };
        return {
          order_item_id: item.id,
          is_available: q.is_available,
          unit_selling_price: q.is_available ? parseFloat(q.unit_selling_price) || item.unit_mrp : 0,
          notes: q.notes || undefined
        };
      });

      await api.post("/quotes", {
        order_id: Number(orderId),
        items: itemsPayload,
        notes: notes.trim() || undefined
      });

      Alert.alert("Quote Submitted!", "The customer has been notified with your pricing.", [
        {
          text: "Back to Broadcasts",
          onPress: () => navigation?.replace?.("broadcasts")
        }
      ]);
    } catch (err: any) {
      Alert.alert("Submission Failed", err.message || "Failed to submit quote.");
    } finally {
      setSubmitting(false);
    }
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
        <Text style={styles.errorText}>Order not found or window expired.</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 120 }}>
      {/* 4-Minute Timer */}
      <CountdownTimer
        initialSeconds={order.remaining_broadcast_seconds}
        onExpire={() => {
          Alert.alert("Window Closed", "The 4-minute broadcast window for this order has expired.");
          navigation?.goBack?.();
        }}
      />

      <View style={styles.orderHeaderCard}>
        <Text style={styles.headerTitle}>Order #{order.id} Quotation</Text>
        <Text style={styles.headerSub}>Destination: {order.delivery_address}</Text>
        <Text style={styles.headerSub}>Total Catalogue MRP: ${order.total_mrp.toFixed(2)}</Text>
      </View>

      <Text style={styles.sectionHeading}>Item Availability & Selling Price</Text>

      {/* Item-by-item quote inputs */}
      {order.items?.map((item: OrderItem) => {
        const qState = itemQuotes[item.id] || { is_available: true, unit_selling_price: String(item.unit_mrp), notes: "" };
        const isAvail = qState.is_available;
        const unitP = parseFloat(qState.unit_selling_price) || 0;
        const subtotal = isAvail ? (unitP * item.quantity).toFixed(2) : "0.00";

        return (
          <View key={item.id} style={[styles.itemCard, !isAvail && styles.itemCardUnavailable]}>
            <View style={styles.itemTopRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.medName}>{item.medicine_name}</Text>
                <Text style={styles.medMeta}>
                  Qty: {item.quantity} • Standard MRP: ${item.unit_mrp.toFixed(2)}
                </Text>
              </View>

              <View style={styles.switchCol}>
                <Text style={[styles.switchLabel, { color: isAvail ? Colors.success : Colors.danger }]}>
                  {isAvail ? "IN STOCK" : "OUT OF STOCK"}
                </Text>
                <Switch
                  value={isAvail}
                  onValueChange={() => toggleAvailability(item.id)}
                  trackColor={{ false: "#cbd5e1", true: "#bbf7d0" }}
                  thumbColor={isAvail ? Colors.secondary : "#94a3b8"}
                />
              </View>
            </View>

            {isAvail ? (
              <View style={styles.priceRow}>
                <View style={{ flex: 1, marginRight: 12 }}>
                  <Text style={styles.inputLabel}>Your Quoted Selling Price / Unit ($)</Text>
                  <TextInput
                    style={styles.priceInput}
                    keyboardType="decimal-pad"
                    value={qState.unit_selling_price}
                    onChangeText={(val) => updatePrice(item.id, val)}
                  />
                </View>
                <View style={{ alignItems: "flex-end", justifyContent: "center" }}>
                  <Text style={styles.subtotalLabel}>Quoted Subtotal</Text>
                  <Text style={styles.subtotalVal}>${subtotal}</Text>
                </View>
              </View>
            ) : (
              <View style={styles.unavailableRow}>
                <Text style={styles.unavailableNotice}>
                  * Marked unavailable. Customer will be billed strictly $0.00 for this item.
                </Text>
              </View>
            )}
          </View>
        );
      })}

      {/* Pharmacy Note */}
      <View style={styles.noteCard}>
        <Text style={styles.inputLabel}>Pharmacy Notes / Delivery remarks (Optional)</Text>
        <TextInput
          style={styles.noteInput}
          placeholder="e.g. Can dispatch immediately, includes free pill organizer..."
          value={notes}
          onChangeText={setNotes}
        />
      </View>

      {/* Floating Submit Bar */}
      <View style={styles.submitBar}>
        <View>
          <View style={styles.fulfillmentBadge}>
            <Text style={styles.fulfillmentText}>
              {quoteCalculation.isFull
                ? "FULL FULFILLMENT"
                : `PARTIAL (${quoteCalculation.availableCount}/${quoteCalculation.totalCount})`}
            </Text>
          </View>
          <Text style={styles.quotedTotalVal}>${quoteCalculation.total.toFixed(2)}</Text>
        </View>

        <TouchableOpacity
          style={[styles.submitBtn, submitting && styles.btnDisabled]}
          onPress={handleSubmitQuote}
          disabled={submitting}
        >
          {submitting ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.submitBtnText}>Submit Quote</Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background
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
  orderHeaderCard: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: Colors.border
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.text
  },
  headerSub: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 3
  },
  sectionHeading: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 10
  },
  itemCard: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.border
  },
  itemCardUnavailable: {
    backgroundColor: "#f8fafc",
    borderColor: "#e2e8f0"
  },
  itemTopRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  medName: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text
  },
  medMeta: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2
  },
  switchCol: {
    alignItems: "center"
  },
  switchLabel: {
    fontSize: 9,
    fontWeight: "800",
    marginBottom: 2
  },
  priceRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#f1f5f9"
  },
  inputLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: Colors.textSecondary,
    marginBottom: 4
  },
  priceInput: {
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 14,
    fontWeight: "700",
    color: Colors.text,
    backgroundColor: "#f8fafc"
  },
  subtotalLabel: {
    fontSize: 11,
    color: Colors.textSecondary
  },
  subtotalVal: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.primaryDark
  },
  unavailableRow: {
    marginTop: 10,
    padding: 8,
    backgroundColor: "#fee2e2",
    borderRadius: 6
  },
  unavailableNotice: {
    fontSize: 11,
    color: Colors.danger,
    fontWeight: "600"
  },
  noteCard: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border
  },
  noteInput: {
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 13,
    color: Colors.text,
    backgroundColor: "#f8fafc"
  },
  submitBar: {
    backgroundColor: "#ffffff",
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 10
  },
  fulfillmentBadge: {
    backgroundColor: "#e0f2fe",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: "flex-start",
    marginBottom: 2
  },
  fulfillmentText: {
    fontSize: 10,
    fontWeight: "800",
    color: Colors.primaryDark
  },
  quotedTotalVal: {
    fontSize: 20,
    fontWeight: "800",
    color: Colors.text
  },
  submitBtn: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 22,
    paddingVertical: 12,
    borderRadius: 8
  },
  btnDisabled: {
    opacity: 0.6
  },
  submitBtnText: {
    color: "#ffffff",
    fontWeight: "800",
    fontSize: 14
  }
});
