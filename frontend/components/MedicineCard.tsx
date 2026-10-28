import React, { useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Medicine } from "../types";
import { Colors } from "../constants/Config";

interface MedicineCardProps {
  medicine: Medicine;
  onAddToCart: (medicine: Medicine, quantity: number) => void;
  inCartCount?: number;
}

export const MedicineCard: React.FC<MedicineCardProps> = ({ medicine, onAddToCart, inCartCount = 0 }) => {
  const [qty, setQty] = useState(1);

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.titleCol}>
          <Text style={styles.name}>{medicine.name}</Text>
          {medicine.generic_name ? (
            <Text style={styles.generic}>{medicine.generic_name}</Text>
          ) : null}
          {medicine.manufacturer ? (
            <Text style={styles.manufacturer}>By {medicine.manufacturer}</Text>
          ) : null}
        </View>

        {medicine.requires_prescription && (
          <View style={styles.rxBadge}>
            <Text style={styles.rxText}>Rx Required</Text>
          </View>
        )}
      </View>

      <View style={styles.tagRow}>
        <View style={styles.tag}>
          <Text style={styles.tagText}>{medicine.category}</Text>
        </View>
        {medicine.pack_size ? (
          <View style={styles.tagSecondary}>
            <Text style={styles.tagSecondaryText}>{medicine.pack_size}</Text>
          </View>
        ) : null}
      </View>

      <View style={styles.footerRow}>
        <View>
          <Text style={styles.mrpLabel}>Standard MRP</Text>
          <Text style={styles.mrpValue}>₹{medicine.mrp.toFixed(2)}</Text>
        </View>

        <View style={styles.actionRow}>
          <View style={styles.qtyContainer}>
            <TouchableOpacity
              style={styles.qtyBtn}
              onPress={() => setQty((q) => Math.max(1, q - 1))}
            >
              <Text style={styles.qtyBtnText}>-</Text>
            </TouchableOpacity>
            <Text style={styles.qtyDisplay}>{qty}</Text>
            <TouchableOpacity
              style={styles.qtyBtn}
              onPress={() => setQty((q) => q + 1)}
            >
              <Text style={styles.qtyBtnText}>+</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={styles.addBtn}
            onPress={() => onAddToCart(medicine, qty)}
          >
            <Text style={styles.addBtnText}>
              {inCartCount > 0 ? `Add (+${qty})` : "Add to Cart"}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.card,
    borderRadius: 12,
    padding: 16,
    marginVertical: 6,
    marginHorizontal: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start"
  },
  titleCol: {
    flex: 1,
    paddingRight: 8
  },
  name: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text
  },
  generic: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 2
  },
  manufacturer: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 1
  },
  rxBadge: {
    backgroundColor: "#fee2e2",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6
  },
  rxText: {
    color: Colors.danger,
    fontSize: 11,
    fontWeight: "700"
  },
  tagRow: {
    flexDirection: "row",
    gap: 6,
    marginVertical: 10
  },
  tag: {
    backgroundColor: "#e0f2fe",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4
  },
  tagText: {
    fontSize: 11,
    color: Colors.primaryDark,
    fontWeight: "600"
  },
  tagSecondary: {
    backgroundColor: "#f1f5f9",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4
  },
  tagSecondaryText: {
    fontSize: 11,
    color: Colors.textSecondary
  },
  footerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 4,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.border
  },
  mrpLabel: {
    fontSize: 11,
    color: Colors.textSecondary
  },
  mrpValue: {
    fontSize: 18,
    fontWeight: "800",
    color: Colors.text
  },
  actionRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8
  },
  qtyContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#f1f5f9",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border
  },
  qtyBtn: {
    paddingHorizontal: 10,
    paddingVertical: 6
  },
  qtyBtnText: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text
  },
  qtyDisplay: {
    fontSize: 14,
    fontWeight: "700",
    paddingHorizontal: 6,
    minWidth: 24,
    textAlign: "center"
  },
  addBtn: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8
  },
  addBtnText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 13
  }
});
