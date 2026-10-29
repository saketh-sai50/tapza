import React, { useState } from "react";
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
  ActivityIndicator
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useApp } from "../context/AppContext";
import { ordersApi } from "../services/api";

export const CartModal = ({ onOpenAuth }) => {
  const {
    cartModalVisible,
    setCartModalVisible,
    cartItems,
    cartTotalMrp,
    updateCartQty,
    clearCart,
    token,
    zone,
    setActiveOrder,
    setQuotesModalOrder
  } = useApp();

  const [address, setAddress] = useState("Flat 402, Green Avenue, Warangal");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleBroadcastOrder = async () => {
    if (!token) {
      setCartModalVisible(false);
      Alert.alert(
        "Login Required",
        "Please log in or register to broadcast your order to local pharmacies.",
        [
          { text: "Cancel", style: "cancel" },
          { text: "Log In", onPress: onOpenAuth }
        ]
      );
      return;
    }

    if (!address.trim()) {
      Alert.alert("Address Required", "Please enter your delivery address.");
      return;
    }

    if (cartItems.length === 0) {
      Alert.alert("Empty Cart", "Add at least one medicine to your cart.");
      return;
    }

    setIsSubmitting(true);
    try {
      const itemsPayload = cartItems.map((it) => ({
        medicine_id: it.id,
        quantity: it.quantity
      }));

      const res = await ordersApi.createOrder(itemsPayload, address.trim(), zone, token);
      const createdOrder = res.order;

      clearCart();
      setCartModalVisible(false);
      setActiveOrder(createdOrder);
      setQuotesModalOrder(createdOrder);

      Alert.alert(
        "Order Broadcasted! 📡",
        `Order #${createdOrder.order_id} is now live! Local pharmacies in ${zone} have 4 minutes to submit their best bids.`
      );
    } catch (e) {
      Alert.alert("Broadcast Failed", e.message || "Failed to broadcast order.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      visible={cartModalVisible}
      animationType="slide"
      transparent
      onRequestClose={() => setCartModalVisible(false)}
    >
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          {/* Header */}
          <View style={styles.header}>
            <View>
              <Text style={styles.title}>Your Medicine Cart</Text>
              <Text style={styles.subtitle}>
                {cartItems.length} {cartItems.length === 1 ? "medicine" : "medicines"} selected
              </Text>
            </View>
            <TouchableOpacity
              style={styles.closeBtn}
              onPress={() => setCartModalVisible(false)}
            >
              <Ionicons name="close" size={20} color="#64748b" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.body} showsVerticalScrollIndicator={false}>
            {/* Cart Items List */}
            {cartItems.map((item) => (
              <View key={item.id} style={styles.itemRow}>
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName} numberOfLines={1}>
                    {item.name}
                  </Text>
                  <Text style={styles.itemMeta}>
                    ₹{item.mrp.toFixed(2)} / unit • {item.dosage_form}
                  </Text>
                </View>

                <View style={styles.itemActions}>
                  <View style={styles.qtyBox}>
                    <TouchableOpacity
                      style={styles.qtyAction}
                      onPress={() => updateCartQty(item.id, -1)}
                    >
                      <Ionicons name="remove" size={13} color="#166534" />
                    </TouchableOpacity>
                    <Text style={styles.qtyText}>{item.quantity}</Text>
                    <TouchableOpacity
                      style={styles.qtyAction}
                      onPress={() => updateCartQty(item.id, 1)}
                    >
                      <Ionicons name="add" size={13} color="#166534" />
                    </TouchableOpacity>
                  </View>
                  <Text style={styles.itemSubtotal}>
                    ₹{(item.mrp * item.quantity).toFixed(2)}
                  </Text>
                </View>
              </View>
            ))}

            {/* Delivery Address Input */}
            <View style={styles.section}>
              <View style={styles.sectionHeader}>
                <Ionicons name="location-outline" size={16} color="#0f172a" />
                <Text style={styles.sectionTitle}>Delivery Address</Text>
              </View>
              <TextInput
                style={styles.addressInput}
                value={address}
                onChangeText={setAddress}
                placeholder="House/Flat No, Landmark, Street Name..."
                placeholderTextColor="#94a3b8"
                multiline
              />
              <View style={styles.zoneTag}>
                <Text style={styles.zoneTagText}>
                  Broadcasting to: <Text style={{ fontWeight: "800" }}>{zone}</Text> Zone
                </Text>
              </View>
            </View>

            {/* How Reverse Auction Works Banner */}
            <View style={styles.auctionBanner}>
              <Ionicons name="flash" size={18} color="#d97706" />
              <View style={{ flex: 1 }}>
                <Text style={styles.auctionTitle}>Live Reverse Auction</Text>
                <Text style={styles.auctionDesc}>
                  Local licensed pharmacies will compete in real-time. You will receive multiple quotes with discounts to choose from!
                </Text>
              </View>
            </View>

            {/* Price Summary */}
            <View style={styles.billBox}>
              <View style={styles.billRow}>
                <Text style={styles.billLabel}>Estimated Maximum MRP</Text>
                <Text style={styles.billVal}>₹{cartTotalMrp.toFixed(2)}</Text>
              </View>
              <View style={styles.billRow}>
                <Text style={styles.billLabel}>Pharmacy Bidding Discount</Text>
                <Text style={styles.discountHint}>Applied live by pharmacies</Text>
              </View>
              <View style={[styles.billRow, styles.billTotalRow]}>
                <Text style={styles.billTotalLabel}>Starting Order Ceiling</Text>
                <Text style={styles.billTotalVal}>₹{cartTotalMrp.toFixed(2)}</Text>
              </View>
            </View>
          </ScrollView>

          {/* Bottom Broadcast CTA */}
          <View style={styles.footer}>
            <TouchableOpacity
              style={[styles.broadcastBtn, isSubmitting && styles.broadcastBtnDisabled]}
              activeOpacity={0.85}
              disabled={isSubmitting}
              onPress={handleBroadcastOrder}
            >
              {isSubmitting ? (
                <ActivityIndicator color="#ffffff" />
              ) : (
                <>
                  <Ionicons name="radio" size={18} color="#ffffff" />
                  <Text style={styles.broadcastText}>
                    Broadcast Order to Local Pharmacies (4 Mins)
                  </Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    justifyContent: "flex-end"
  },
  sheet: {
    backgroundColor: "#ffffff",
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: "85%",
    paddingBottom: 20
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 18,
    borderBottomWidth: 1,
    borderBottomColor: "#f1f5f9"
  },
  title: {
    fontSize: 17,
    fontWeight: "900",
    color: "#0f172a"
  },
  subtitle: {
    fontSize: 12,
    color: "#64748b",
    marginTop: 2
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#f1f5f9",
    alignItems: "center",
    justifyContent: "center"
  },
  body: {
    padding: 16
  },
  itemRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#f8fafc"
  },
  itemInfo: {
    flex: 1,
    paddingRight: 10
  },
  itemName: {
    fontSize: 13.5,
    fontWeight: "700",
    color: "#1e293b"
  },
  itemMeta: {
    fontSize: 11,
    color: "#64748b",
    marginTop: 2
  },
  itemActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12
  },
  qtyBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ecfdf5",
    borderWidth: 1,
    borderColor: "#a7f3d0",
    borderRadius: 6
  },
  qtyAction: {
    paddingHorizontal: 8,
    paddingVertical: 4
  },
  qtyText: {
    fontSize: 12,
    fontWeight: "800",
    color: "#166534",
    paddingHorizontal: 4
  },
  itemSubtotal: {
    fontSize: 13,
    fontWeight: "800",
    color: "#0f172a",
    minWidth: 55,
    textAlign: "right"
  },
  section: {
    marginTop: 14,
    backgroundColor: "#f8fafc",
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#e2e8f0"
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 6
  },
  sectionTitle: {
    fontSize: 12.5,
    fontWeight: "800",
    color: "#0f172a"
  },
  addressInput: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 8,
    padding: 8,
    fontSize: 12,
    color: "#0f172a",
    minHeight: 46
  },
  zoneTag: {
    marginTop: 6
  },
  zoneTagText: {
    fontSize: 11,
    color: "#047857"
  },
  auctionBanner: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    backgroundColor: "#fffbeb",
    borderWidth: 1,
    borderColor: "#fde68a",
    padding: 10,
    borderRadius: 10,
    marginTop: 14
  },
  auctionTitle: {
    fontSize: 12,
    fontWeight: "800",
    color: "#92400e"
  },
  auctionDesc: {
    fontSize: 11,
    color: "#78350f",
    marginTop: 2,
    lineHeight: 15
  },
  billBox: {
    marginTop: 14,
    padding: 12,
    backgroundColor: "#f8fafc",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#e2e8f0"
  },
  billRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6
  },
  billLabel: {
    fontSize: 12,
    color: "#64748b"
  },
  billVal: {
    fontSize: 12,
    fontWeight: "700",
    color: "#0f172a"
  },
  discountHint: {
    fontSize: 11,
    fontWeight: "700",
    color: "#16a34a"
  },
  billTotalRow: {
    borderTopWidth: 1,
    borderTopColor: "#e2e8f0",
    paddingTop: 8,
    marginTop: 4,
    marginBottom: 0
  },
  billTotalLabel: {
    fontSize: 13,
    fontWeight: "800",
    color: "#0f172a"
  },
  billTotalVal: {
    fontSize: 15,
    fontWeight: "900",
    color: "#065f46"
  },
  footer: {
    paddingHorizontal: 16,
    paddingTop: 10
  },
  broadcastBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "#16a34a",
    paddingVertical: 14,
    borderRadius: 12,
    shadowColor: "#16a34a",
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4
  },
  broadcastBtnDisabled: {
    opacity: 0.7
  },
  broadcastText: {
    color: "#ffffff",
    fontSize: 13.5,
    fontWeight: "900"
  }
});
