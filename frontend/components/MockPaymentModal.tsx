import React, { useState } from "react";
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert
} from "react-native";
import { api } from "../services/api";
import { Colors } from "../constants/Config";

interface MockPaymentModalProps {
  visible: boolean;
  orderId: number;
  amount: number;
  onClose: () => void;
  onSuccess: () => void;
}

export const MockPaymentModal: React.FC<MockPaymentModalProps> = ({
  visible,
  orderId,
  amount,
  onClose,
  onSuccess
}) => {
  const [processing, setProcessing] = useState<boolean>(false);

  const handleSimulatePayment = async () => {
    try {
      setProcessing(true);
      await api.post(`/orders/${orderId}/mock-pay`, {
        payment_method: "SIMULATED_TEST_CARD"
      });
      Alert.alert(
        "Mock Payment Completed",
        "This was a simulated test payment. No real money was charged.",
        [{ text: "OK", onPress: () => { onSuccess(); onClose(); } }]
      );
    } catch (err: any) {
      Alert.alert("Payment Error", err.message || "Failed to process simulated payment.");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.dialog}>
          {/* Mock Disclaimer Banner */}
          <View style={styles.mockBanner}>
            <Text style={styles.mockBannerText}>SIMULATED TEST PAYMENT (MOCK)</Text>
            <Text style={styles.mockSubText}>No real credit card or bank account will be charged</Text>
          </View>

          <Text style={styles.title}>Confirm Simulated Checkout</Text>
          <Text style={styles.subTitle}>Order #{orderId}</Text>

          <View style={styles.amountBox}>
            <Text style={styles.amountLabel}>Total Payable Amount:</Text>
            <Text style={styles.amountValue}>₹{amount.toFixed(2)}</Text>
            <Text style={styles.amountNote}>
              * Calculated strictly from available medicines. Unavailable medicines were billed at ₹0.00.
            </Text>
          </View>

          <View style={styles.mockCardDetails}>
            <Text style={styles.detailTitle}>Simulated Payment Method:</Text>
            <Text style={styles.detailText}>Demo Card: •••• •••• •••• 4242</Text>
            <Text style={styles.detailText}>Status: Sandbox / Simulation Mode</Text>
          </View>

          <View style={styles.btnRow}>
            <TouchableOpacity style={styles.cancelBtn} onPress={onClose} disabled={processing}>
              <Text style={styles.cancelBtnText}>Cancel</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.payBtn, processing && styles.btnDisabled]}
              onPress={handleSimulatePayment}
              disabled={processing}
            >
              {processing ? (
                <ActivityIndicator color="#ffffff" />
              ) : (
                <Text style={styles.payBtnText}>Pay ₹{amount.toFixed(2)} (Simulated)</Text>
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
    backgroundColor: "rgba(0, 0, 0, 0.6)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20
  },
  dialog: {
    backgroundColor: "#ffffff",
    borderRadius: 16,
    padding: 20,
    width: "100%",
    maxWidth: 420,
    shadowColor: "#000",
    shadowOpacity: 0.15,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 10,
    elevation: 6
  },
  mockBanner: {
    backgroundColor: "#fef3c7",
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#fde68a",
    alignItems: "center",
    marginBottom: 16
  },
  mockBannerText: {
    color: "#92400e",
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 0.8
  },
  mockSubText: {
    color: "#b45309",
    fontSize: 10,
    marginTop: 2
  },
  title: {
    fontSize: 18,
    fontWeight: "800",
    color: Colors.text
  },
  subTitle: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 2
  },
  amountBox: {
    backgroundColor: "#f0fdf4",
    padding: 14,
    borderRadius: 10,
    marginVertical: 14,
    borderWidth: 1,
    borderColor: "#bbf7d0"
  },
  amountLabel: {
    fontSize: 12,
    color: "#166534",
    fontWeight: "600"
  },
  amountValue: {
    fontSize: 26,
    fontWeight: "900",
    color: "#166534",
    marginVertical: 2
  },
  amountNote: {
    fontSize: 11,
    color: "#15803d",
    lineHeight: 15,
    marginTop: 4
  },
  mockCardDetails: {
    backgroundColor: "#f8fafc",
    padding: 12,
    borderRadius: 8,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: Colors.border
  },
  detailTitle: {
    fontSize: 11,
    fontWeight: "700",
    color: Colors.textSecondary,
    marginBottom: 4
  },
  detailText: {
    fontSize: 13,
    color: Colors.text,
    fontFamily: "monospace"
  },
  btnRow: {
    flexDirection: "row",
    gap: 10
  },
  cancelBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: "center"
  },
  cancelBtnText: {
    color: Colors.textSecondary,
    fontWeight: "700"
  },
  payBtn: {
    flex: 2,
    backgroundColor: Colors.secondary,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center"
  },
  btnDisabled: {
    opacity: 0.6
  },
  payBtnText: {
    color: "#ffffff",
    fontWeight: "800",
    fontSize: 14
  }
});
