import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useApp } from "../context/AppContext";

export const LiveOrderTracker = () => {
  const { activeOrder, setQuotesModalOrder } = useApp();

  if (!activeOrder) return null;

  const isBroadcasting = activeOrder.status === "BROADCASTING";

  return (
    <View style={styles.wrapper}>
      <View style={styles.card}>
        <View style={styles.left}>
          <View style={styles.pulseContainer}>
            <View style={[styles.pulseDot, !isBroadcasting && styles.pulseDotStatic]} />
          </View>
          <View>
            <Text style={styles.orderTitle}>
              Live Order #{activeOrder.id || activeOrder.order_id}
            </Text>
            <Text style={styles.orderSub}>
              {isBroadcasting
                ? "Pharmacies Quoting Live • Best Prices"
                : "Quote Selected • Awaiting Confirmation"}
            </Text>
          </View>
        </View>

        <TouchableOpacity
          style={styles.viewQuotesBtn}
          activeOpacity={0.85}
          onPress={() => setQuotesModalOrder(activeOrder)}
        >
          <Text style={styles.viewQuotesText}>View Quotes</Text>
          <Ionicons name="chevron-forward" size={14} color="#ffffff" />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    position: "absolute",
    bottom: 66,
    left: 12,
    right: 12,
    zIndex: 90
  },
  card: {
    backgroundColor: "#1e1b4b",
    borderRadius: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 10,
    paddingHorizontal: 12,
    shadowColor: "#000",
    shadowOpacity: 0.3,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 3 },
    elevation: 6,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.15)"
  },
  left: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    flex: 1
  },
  pulseContainer: {
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: "rgba(16, 185, 129, 0.25)",
    alignItems: "center",
    justifyContent: "center"
  },
  pulseDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#10b981"
  },
  pulseDotStatic: {
    backgroundColor: "#f59e0b"
  },
  orderTitle: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "900",
    letterSpacing: 0.2
  },
  orderSub: {
    color: "#a5b4fc",
    fontSize: 10.5,
    fontWeight: "600",
    marginTop: 1
  },
  viewQuotesBtn: {
    backgroundColor: "#059669",
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingVertical: 7,
    paddingHorizontal: 12,
    borderRadius: 8
  },
  viewQuotesText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "800"
  }
});
