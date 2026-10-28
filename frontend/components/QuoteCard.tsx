import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Quote } from "../types";
import { Colors } from "../constants/Config";

interface QuoteCardProps {
  quote: Quote;
  onSelect?: (quote: Quote) => void;
  isSelectable?: boolean;
  isWinningQuote?: boolean;
}

export const QuoteCard: React.FC<QuoteCardProps> = ({
  quote,
  onSelect,
  isSelectable = false,
  isWinningQuote = false
}) => {
  const isFull = quote.is_full_fulfillment;

  return (
    <View style={[styles.card, isWinningQuote && styles.winningCard]}>
      {/* Pharmacy Header & Fulfillment Pill */}
      <View style={styles.headerRow}>
        <View style={{ flex: 1 }}>
          <Text style={styles.pharmacyName}>{quote.pharmacy_name}</Text>
          <Text style={styles.pharmacyAddress}>{quote.pharmacy_address}</Text>
        </View>

        <View style={[styles.badge, isFull ? styles.fullBadge : styles.partialBadge]}>
          <Text style={[styles.badgeText, isFull ? styles.fullBadgeText : styles.partialBadgeText]}>
            {isFull ? "FULL FULFILLMENT" : `PARTIAL (${quote.available_items_count}/${quote.total_items_count})`}
          </Text>
        </View>
      </View>

      {/* Item-by-item breakdown */}
      <View style={styles.itemsTable}>
        {quote.items?.map((item) => (
          <View key={item.id} style={styles.itemRow}>
            <View style={{ flex: 1, paddingRight: 8 }}>
              <Text
                style={[
                  styles.itemName,
                  !item.is_available && styles.unavailableItemName
                ]}
              >
                {item.medicine_name} (Qty: {item.quantity})
              </Text>
              <Text style={styles.mrpText}>
                Catalogue MRP: ₹{item.unit_mrp.toFixed(2)}
              </Text>
              {!item.is_available && (
                <Text style={styles.notChargedNote}>Unavailable • ₹0.00 (Not Charged)</Text>
              )}
            </View>

            <View style={{ alignItems: "flex-end" }}>
              {item.is_available ? (
                <>
                  <Text style={styles.quotedPrice}>₹{item.subtotal_price.toFixed(2)}</Text>
                  <Text style={styles.unitQuotedPrice}>
                    @ ₹{item.unit_selling_price.toFixed(2)}/unit
                  </Text>
                </>
              ) : (
                <Text style={styles.zeroPrice}>₹0.00</Text>
              )}
            </View>
          </View>
        ))}
      </View>

      {/* Pharmacist Advice / Remarks */}
      {quote.notes ? (
        <View style={styles.pharmacistNoteBox}>
          <Text style={styles.pharmacistNoteLabel}>💬 Pharmacist Note:</Text>
          <Text style={styles.pharmacistNoteText}>{quote.notes}</Text>
        </View>
      ) : null}

      {/* Total & Action */}
      <View style={styles.footerRow}>
        <View>
          <Text style={styles.totalLabel}>Quoted Total Payable</Text>
          <Text style={styles.totalValue}>₹{quote.total_quoted_price.toFixed(2)}</Text>
        </View>

        {isSelectable && onSelect && (
          <TouchableOpacity
            style={styles.selectBtn}
            onPress={() => onSelect(quote)}
          >
            <Text style={styles.selectBtnText}>Select Pharmacy</Text>
          </TouchableOpacity>
        )}

        {isWinningQuote && (
          <View style={styles.wonPill}>
            <Text style={styles.wonPillText}>SELECTED WINNER</Text>
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
    padding: 16,
    marginVertical: 8,
    borderWidth: 1,
    borderColor: Colors.border,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2
  },
  winningCard: {
    borderColor: Colors.secondary,
    borderWidth: 2,
    backgroundColor: "#f0fdf4"
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start"
  },
  pharmacyName: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.text
  },
  pharmacyAddress: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6
  },
  fullBadge: {
    backgroundColor: "#dcfce7"
  },
  partialBadge: {
    backgroundColor: "#fef3c7"
  },
  badgeText: {
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.5
  },
  fullBadgeText: {
    color: "#166534"
  },
  partialBadgeText: {
    color: "#92400e"
  },
  itemsTable: {
    marginVertical: 12,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: "#f1f5f9",
    paddingVertical: 8
  },
  itemRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 6
  },
  itemName: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.text
  },
  unavailableItemName: {
    color: "#94a3b8",
    textDecorationLine: "line-through"
  },
  mrpText: {
    fontSize: 11,
    color: Colors.textSecondary
  },
  notChargedNote: {
    fontSize: 11,
    color: Colors.danger,
    fontWeight: "700",
    marginTop: 1
  },
  quotedPrice: {
    fontSize: 14,
    fontWeight: "700",
    color: Colors.text
  },
  unitQuotedPrice: {
    fontSize: 10,
    color: Colors.textSecondary
  },
  zeroPrice: {
    fontSize: 13,
    fontWeight: "700",
    color: Colors.danger
  },
  footerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingTop: 4
  },
  totalLabel: {
    fontSize: 11,
    color: Colors.textSecondary
  },
  totalValue: {
    fontSize: 18,
    fontWeight: "800",
    color: Colors.primaryDark
  },
  selectBtn: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8
  },
  selectBtnText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 13
  },
  wonPill: {
    backgroundColor: Colors.secondary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6
  },
  wonPillText: {
    color: "#ffffff",
    fontSize: 11,
    fontWeight: "800"
  },
  pharmacistNoteBox: {
    backgroundColor: "#f0fdf4",
    borderWidth: 1,
    borderColor: "#bbf7d0",
    borderRadius: 8,
    padding: 10,
    marginVertical: 8
  },
  pharmacistNoteLabel: {
    fontSize: 11.5,
    fontWeight: "800",
    color: "#166534",
    marginBottom: 2
  },
  pharmacistNoteText: {
    fontSize: 12.5,
    color: "#1e293b",
    lineHeight: 17
  }
});
