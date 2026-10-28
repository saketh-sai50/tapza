import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert
} from "react-native";
import { useCart } from "../../context/CartContext";
import { useAuth } from "../../context/AuthContext";
import { Colors, Config } from "../../constants/Config";

export default function CartScreen({ navigation }: any) {
  const { items, updateQuantity, removeFromCart, totalMRP, clearCart } = useCart();
  const { user } = useAuth();

  const [address, setAddress] = useState<string>("123 Main Street, Apt 4B");
  const [zone, setZone] = useState<string>(user?.zone || Config.DEFAULT_ZONE);

  const handleProceed = () => {
    if (!address.trim()) {
      Alert.alert("Missing Address", "Please enter a delivery address.");
      return;
    }
    navigation?.navigate?.("checkout", { address, zone });
  };

  if (items.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyTitle}>Your cart is empty</Text>
        <Text style={styles.emptySubtitle}>
          Search our medicine catalogue to add prescriptions and wellness products.
        </Text>
        <TouchableOpacity
          style={styles.browseBtn}
          onPress={() => navigation?.navigate?.("index")}
        >
          <Text style={styles.browseBtnText}>Browse Catalogue</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={items}
        keyExtractor={(item) => String(item.medicine.id)}
        contentContainerStyle={{ padding: 16, paddingBottom: 160 }}
        ListHeaderComponent={
          <View style={styles.sectionHeader}>
            <Text style={styles.heading}>Review Cart Items</Text>
            <TouchableOpacity onPress={clearCart}>
              <Text style={styles.clearText}>Clear All</Text>
            </TouchableOpacity>
          </View>
        }
        renderItem={({ item }) => (
          <View style={styles.cartCard}>
            <View style={styles.cardHeader}>
              <View style={{ flex: 1 }}>
                <Text style={styles.medName}>{item.medicine.name}</Text>
                <Text style={styles.medSub}>
                  Unit MRP: ${item.medicine.mrp.toFixed(2)} • {item.medicine.pack_size || "1 Unit"}
                </Text>
              </View>
              <Text style={styles.itemSubtotal}>${item.subtotal_mrp.toFixed(2)}</Text>
            </View>

            <View style={styles.cardActions}>
              <View style={styles.qtyContainer}>
                <TouchableOpacity
                  style={styles.qtyBtn}
                  onPress={() => updateQuantity(item.medicine.id, item.quantity - 1)}
                >
                  <Text style={styles.qtyBtnText}>-</Text>
                </TouchableOpacity>
                <Text style={styles.qtyText}>{item.quantity}</Text>
                <TouchableOpacity
                  style={styles.qtyBtn}
                  onPress={() => updateQuantity(item.medicine.id, item.quantity + 1)}
                >
                  <Text style={styles.qtyBtnText}>+</Text>
                </TouchableOpacity>
              </View>

              <TouchableOpacity
                onPress={() => removeFromCart(item.medicine.id)}
                style={styles.removeBtn}
              >
                <Text style={styles.removeText}>Remove</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
        ListFooterComponent={
          <View style={styles.deliverySection}>
            <Text style={styles.heading}>Delivery Information</Text>

            <Text style={styles.inputLabel}>Delivery Address</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter full street address"
              value={address}
              onChangeText={setAddress}
            />

            <Text style={styles.inputLabel}>Delivery Zone (Local Broadcast Area)</Text>
            <View style={styles.zoneRow}>
              {Config.AVAILABLE_ZONES.map((z) => (
                <TouchableOpacity
                  key={z}
                  style={[styles.zonePill, zone === z && styles.zonePillActive]}
                  onPress={() => setZone(z)}
                >
                  <Text style={[styles.zoneText, zone === z && styles.zoneTextActive]}>
                    {z}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.mrpSummaryBox}>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Total Standard MRP:</Text>
                <Text style={styles.summaryValue}>${totalMRP.toFixed(2)}</Text>
              </View>
              <Text style={styles.mrpNotice}>
                * This is the catalogue MRP. Local pharmacies will quote competitive selling prices during the 4-minute broadcast. You will only be charged for available items.
              </Text>
            </View>
          </View>
        }
      />

      {/* Checkout Action Bar */}
      <View style={styles.bottomBar}>
        <View>
          <Text style={styles.barLabel}>Total Catalogue MRP</Text>
          <Text style={styles.barValue}>${totalMRP.toFixed(2)}</Text>
        </View>
        <TouchableOpacity style={styles.proceedBtn} onPress={handleProceed}>
          <Text style={styles.proceedBtnText}>Continue to Broadcast &rarr;</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text
  },
  emptySubtitle: {
    fontSize: 13,
    color: Colors.textSecondary,
    textAlign: "center",
    marginVertical: 8
  },
  browseBtn: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 12
  },
  browseBtnText: {
    color: "#ffffff",
    fontWeight: "700"
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12
  },
  heading: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text
  },
  clearText: {
    color: Colors.danger,
    fontSize: 13,
    fontWeight: "600"
  },
  cartCard: {
    backgroundColor: "#ffffff",
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between"
  },
  medName: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text
  },
  medSub: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2
  },
  itemSubtotal: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text
  },
  cardActions: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 12,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#f1f5f9"
  },
  qtyContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#f1f5f9",
    borderRadius: 6,
    borderWidth: 1,
    borderColor: Colors.border
  },
  qtyBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6
  },
  qtyBtnText: {
    fontSize: 16,
    fontWeight: "700"
  },
  qtyText: {
    paddingHorizontal: 8,
    fontSize: 14,
    fontWeight: "700"
  },
  removeBtn: {
    padding: 6
  },
  removeText: {
    color: Colors.danger,
    fontSize: 13,
    fontWeight: "600"
  },
  deliverySection: {
    backgroundColor: "#ffffff",
    borderRadius: 10,
    padding: 16,
    marginTop: 16,
    borderWidth: 1,
    borderColor: Colors.border
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: "700",
    color: Colors.textSecondary,
    marginTop: 12,
    marginBottom: 4
  },
  input: {
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: Colors.text,
    backgroundColor: "#f8fafc"
  },
  zoneRow: {
    flexDirection: "row",
    gap: 8,
    marginTop: 6
  },
  zonePill: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: "#f1f5f9",
    borderWidth: 1,
    borderColor: Colors.border
  },
  zonePillActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary
  },
  zoneText: {
    fontSize: 13,
    fontWeight: "700",
    color: Colors.textSecondary
  },
  zoneTextActive: {
    color: "#ffffff"
  },
  mrpSummaryBox: {
    backgroundColor: "#f0fdf4",
    padding: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#bbf7d0",
    marginTop: 16
  },
  summaryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  summaryLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: "#166534"
  },
  summaryValue: {
    fontSize: 18,
    fontWeight: "800",
    color: "#166534"
  },
  mrpNotice: {
    fontSize: 11,
    color: "#15803d",
    marginTop: 6,
    lineHeight: 16
  },
  bottomBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "#ffffff",
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  barLabel: {
    fontSize: 11,
    color: Colors.textSecondary
  },
  barValue: {
    fontSize: 18,
    fontWeight: "800",
    color: Colors.text
  },
  proceedBtn: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 18,
    paddingVertical: 12,
    borderRadius: 8
  },
  proceedBtnText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 14
  }
});
