import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert
} from "react-native";
import { useCart } from "../../context/CartContext";
import { api } from "../../services/api";
import { Colors } from "../../constants/Config";

export default function CheckoutScreen({ route, navigation }: any) {
  const { items, totalMRP, clearCart } = useCart();
  const address = route?.params?.address || "123 Main Street, Apt 4B";
  const zone = route?.params?.zone || "ZONE_A";

  const [submitting, setSubmitting] = useState<boolean>(false);

  const handleCreateBroadcastOrder = async () => {
    try {
      setSubmitting(true);
      const payload = {
        delivery_address: address,
        zone,
        items: items.map((i) => ({
          medicine_id: i.medicine.id,
          quantity: i.quantity
        }))
      };

      const res = await api.post<{ message: string; order: any }>("/orders", payload);
      clearCart();
      Alert.alert(
        "Order Placed!",
        "Your order request has been sent to local pharmacies. Quotes will arrive shortly!",
        [
          {
            text: "View Live Quotes",
            onPress: () => navigation?.replace?.("orders/[id]", { id: res.order.order_id })
          }
        ]
      );
    } catch (err: any) {
      Alert.alert("Order Error", err.message || "Failed to place order request");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16 }}>
      {/* Ordering Guide Banner */}
      <View style={styles.broadcastBanner}>
        <Text style={styles.bannerBadge}>LOCAL PHARMACY OFFERS</Text>
        <Text style={styles.bannerTitle}>How Tapza Medicine Ordering Works</Text>
        <Text style={styles.bannerText}>
          1. Verified pharmacies in {zone} receive your medicine request.{"\n"}
          2. Pharmacies verify stock, pack options, and quote their best prices.{"\n"}
          3. You compare quotes side-by-side, read pharmacist notes, and choose your preferred pharmacy.{"\n"}
          4. You are never charged for unavailable items.
        </Text>
      </View>

      {/* Delivery Summary */}
      <View style={styles.sectionCard}>
        <Text style={styles.cardHeader}>Delivery Summary</Text>
        <Text style={styles.detailLabel}>Address:</Text>
        <Text style={styles.detailValue}>{address}</Text>

        <Text style={styles.detailLabel}>Eligible Pharmacy Zone:</Text>
        <Text style={styles.detailValue}>{zone}</Text>
      </View>

      {/* Items Summary */}
      <View style={styles.sectionCard}>
        <Text style={styles.cardHeader}>Medicines Requested ({items.length})</Text>
        {items.map((i) => (
          <View key={i.medicine.id} style={styles.itemRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.itemName}>{i.medicine.name}</Text>
              <Text style={styles.itemMeta}>Qty: {i.quantity} × MRP ${i.medicine.mrp.toFixed(2)}</Text>
            </View>
            <Text style={styles.itemTotal}>${i.subtotal_mrp.toFixed(2)}</Text>
          </View>
        ))}

        <View style={styles.divider} />
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>Total Estimated MRP:</Text>
          <Text style={styles.totalValue}>${totalMRP.toFixed(2)}</Text>
        </View>
      </View>

      {/* Start Broadcast Button */}
      <TouchableOpacity
        style={[styles.startBroadcastBtn, submitting && styles.btnDisabled]}
        onPress={handleCreateBroadcastOrder}
        disabled={submitting}
      >
        {submitting ? (
          <ActivityIndicator color="#ffffff" />
        ) : (
          <Text style={styles.btnText}>Request Quotes from Local Pharmacies</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background
  },
  broadcastBanner: {
    backgroundColor: "#eff6ff",
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: "#bfdbfe",
    marginBottom: 16
  },
  bannerBadge: {
    fontSize: 11,
    fontWeight: "800",
    color: Colors.primaryDark,
    letterSpacing: 0.8,
    marginBottom: 4
  },
  bannerTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1e3a8a",
    marginBottom: 6
  },
  bannerText: {
    fontSize: 12,
    color: "#1e40af",
    lineHeight: 18
  },
  sectionCard: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border
  },
  cardHeader: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 12
  },
  detailLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: Colors.textSecondary,
    marginTop: 6
  },
  detailValue: {
    fontSize: 14,
    color: Colors.text,
    fontWeight: "500",
    marginTop: 2
  },
  itemRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
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
  itemTotal: {
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
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text
  },
  totalValue: {
    fontSize: 20,
    fontWeight: "800",
    color: Colors.primaryDark
  },
  startBroadcastBtn: {
    backgroundColor: Colors.primary,
    paddingVertical: 16,
    borderRadius: 10,
    alignItems: "center",
    marginBottom: 40
  },
  btnDisabled: {
    opacity: 0.6
  },
  btnText: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "800"
  }
});
