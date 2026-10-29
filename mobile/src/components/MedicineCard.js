import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useApp } from "../context/AppContext";

export const MedicineCard = ({ medicine }) => {
  const { cart, addToCart, updateCartQty } = useApp();
  const cartItem = cart[medicine.id];
  const qty = cartItem ? cartItem.quantity : 0;
  const mrp = Number(medicine.mrp || 0).toFixed(2);

  return (
    <View style={styles.card}>
      <View style={styles.topInfo}>
        <View style={styles.textWrap}>
          <Text style={styles.name} numberOfLines={2}>
            {medicine.name}
          </Text>
          <Text style={styles.details} numberOfLines={1}>
            {medicine.dosage_form || "Tablet"}
            {medicine.pack_size ? ` • ${medicine.pack_size}` : ""}
            {medicine.strength ? ` • ${medicine.strength}` : ""}
          </Text>
          {medicine.generic_name && (
            <Text style={styles.generic} numberOfLines={1}>
              {medicine.generic_name}
            </Text>
          )}
        </View>

        <View style={styles.badgeWrap}>
          {medicine.requires_prescription ? (
            <View style={styles.rxBadge}>
              <Text style={styles.rxText}>Rx Required</Text>
            </View>
          ) : (
            <View style={styles.otcBadge}>
              <Text style={styles.otcText}>OTC</Text>
            </View>
          )}
        </View>
      </View>

      <View style={styles.footer}>
        <View style={styles.priceWrap}>
          <Text style={styles.mrpLabel}>Standard MRP</Text>
          <Text style={styles.mrpPrice}>₹{mrp}</Text>
        </View>

        {qty === 0 ? (
          <TouchableOpacity
            style={styles.addBtn}
            activeOpacity={0.8}
            onPress={() => addToCart(medicine)}
          >
            <Ionicons name="add" size={16} color="#166534" />
            <Text style={styles.addBtnText}>ADD</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.qtyControls}>
            <TouchableOpacity
              style={styles.qtyBtn}
              onPress={() => updateCartQty(medicine.id, -1)}
            >
              <Ionicons name="remove" size={14} color="#166534" />
            </TouchableOpacity>
            <Text style={styles.qtyValue}>{qty}</Text>
            <TouchableOpacity
              style={styles.qtyBtn}
              onPress={() => updateCartQty(medicine.id, 1)}
            >
              <Ionicons name="add" size={14} color="#166534" />
            </TouchableOpacity>
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    padding: 12,
    marginBottom: 10,
    shadowColor: "#000",
    shadowOpacity: 0.03,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1
  },
  topInfo: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 8
  },
  textWrap: {
    flex: 1
  },
  name: {
    fontSize: 14,
    fontWeight: "800",
    color: "#0f172a",
    lineHeight: 18
  },
  details: {
    fontSize: 11.5,
    color: "#64748b",
    marginTop: 3,
    fontWeight: "500"
  },
  generic: {
    fontSize: 10.5,
    color: "#94a3b8",
    fontStyle: "italic",
    marginTop: 2
  },
  badgeWrap: {
    flexShrink: 0
  },
  rxBadge: {
    backgroundColor: "#fef3c7",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: "#fde68a"
  },
  rxText: {
    color: "#92400e",
    fontSize: 9.5,
    fontWeight: "800"
  },
  otcBadge: {
    backgroundColor: "#f0fdf4",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: "#bbf7d0"
  },
  otcText: {
    color: "#166534",
    fontSize: 9.5,
    fontWeight: "800"
  },
  footer: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#f1f5f9"
  },
  priceWrap: {
    display: "flex"
  },
  mrpLabel: {
    fontSize: 10,
    color: "#64748b",
    fontWeight: "600",
    textTransform: "uppercase"
  },
  mrpPrice: {
    fontSize: 15,
    fontWeight: "900",
    color: "#065f46"
  },
  addBtn: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ecfdf5",
    borderWidth: 1.5,
    borderColor: "#86efac",
    paddingVertical: 6,
    paddingHorizontal: 16,
    borderRadius: 8,
    gap: 4
  },
  addBtnText: {
    color: "#166534",
    fontSize: 12,
    fontWeight: "900"
  },
  qtyControls: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ecfdf5",
    borderWidth: 1.5,
    borderColor: "#86efac",
    borderRadius: 8,
    overflow: "hidden"
  },
  qtyBtn: {
    paddingHorizontal: 10,
    paddingVertical: 6
  },
  qtyValue: {
    fontSize: 12.5,
    fontWeight: "900",
    color: "#166534",
    paddingHorizontal: 4
  }
});
