import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useApp } from "../context/AppContext";

export const FloatingCart = () => {
  const { cartItemCount, cartTotalMrp, setCartModalVisible } = useApp();

  if (cartItemCount === 0) return null;

  return (
    <View style={styles.floatingWrapper}>
      <TouchableOpacity
        style={styles.container}
        activeOpacity={0.9}
        onPress={() => setCartModalVisible(true)}
      >
        <View style={styles.left}>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{cartItemCount}</Text>
          </View>
          <View>
            <Text style={styles.cartLabel}>
              {cartItemCount} {cartItemCount === 1 ? "item" : "items"} in cart
            </Text>
            <Text style={styles.totalText}>Est. MRP ₹{cartTotalMrp.toFixed(2)}</Text>
          </View>
        </View>

        <View style={styles.right}>
          <Text style={styles.viewCartText}>View Cart</Text>
          <Ionicons name="chevron-forward" size={16} color="#ffffff" />
        </View>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  floatingWrapper: {
    position: "absolute",
    bottom: 68,
    left: 14,
    right: 14,
    zIndex: 99
  },
  container: {
    backgroundColor: "#16a34a",
    borderRadius: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 10,
    paddingHorizontal: 14,
    shadowColor: "#16a34a",
    shadowOpacity: 0.35,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6
  },
  left: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10
  },
  badge: {
    backgroundColor: "#ffffff",
    width: 26,
    height: 26,
    borderRadius: 13,
    alignItems: "center",
    justifyContent: "center"
  },
  badgeText: {
    color: "#16a34a",
    fontSize: 12,
    fontWeight: "900"
  },
  cartLabel: {
    color: "rgba(255, 255, 255, 0.9)",
    fontSize: 11,
    fontWeight: "600"
  },
  totalText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "900"
  },
  right: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2
  },
  viewCartText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "800"
  }
});
