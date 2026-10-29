import React, { useState, useEffect } from "react";
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useApp } from "../context/AppContext";
import { quotesApi } from "../services/api";

export const QuotesModal = () => {
  const { quotesModalOrder, setQuotesModalOrder, token, setActiveOrder } = useApp();
  const [quotes, setQuotes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSelecting, setIsSelecting] = useState(false);

  const orderId = quotesModalOrder?.id || quotesModalOrder?.order_id;

  // Poll for incoming pharmacy bids every 3.5s
  useEffect(() => {
    if (!orderId || !token) {
      setQuotes([]);
      return;
    }

    let isMounted = true;
    const fetchBids = async () => {
      try {
        const d = await quotesApi.getOrderQuotes(orderId, token);
        if (isMounted) {
          setQuotes(d.quotes || []);
          setIsLoading(false);
        }
      } catch (e) {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchBids();
    const interval = setInterval(fetchBids, 3500);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [orderId, token]);

  const handleSelectPharmacy = async (quoteId, pharmacyName) => {
    Alert.alert(
      "Confirm Pharmacy",
      `Award Order #${orderId} to ${pharmacyName}?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Confirm & Award",
          onPress: async () => {
            setIsSelecting(true);
            try {
              await quotesApi.selectWinningQuote(orderId, quoteId, token);
              Alert.alert(
                "Pharmacy Selected! 🎉",
                `${pharmacyName} has been assigned to prepare your order. They will confirm and dispatch shortly!`
              );
              setQuotesModalOrder(null);
              setActiveOrder(null);
            } catch (e) {
              Alert.alert("Selection Failed", e.message || "Failed to select quote.");
            } finally {
              setIsSelecting(false);
            }
          }
        }
      ]
    );
  };

  if (!quotesModalOrder) return null;

  return (
    <Modal
      visible={!!quotesModalOrder}
      animationType="slide"
      transparent
      onRequestClose={() => setQuotesModalOrder(null)}
    >
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          {/* Header */}
          <View style={styles.header}>
            <View>
              <View style={styles.titleRow}>
                <Text style={styles.title}>Order #{orderId} Live Quotes</Text>
                <View style={styles.liveTag}>
                  <View style={styles.liveDot} />
                  <Text style={styles.liveTagText}>AUCTION LIVE</Text>
                </View>
              </View>
              <Text style={styles.subtext}>
                {quotes.length} {quotes.length === 1 ? "pharmacy bid" : "pharmacy bids"} received • Compare prices & advice
              </Text>
            </View>
            <TouchableOpacity
              style={styles.closeBtn}
              onPress={() => setQuotesModalOrder(null)}
            >
              <Ionicons name="close" size={20} color="#64748b" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.body} showsVerticalScrollIndicator={false}>
            {isLoading && quotes.length === 0 ? (
              <View style={styles.loadingBox}>
                <ActivityIndicator size="large" color="#16a34a" />
                <Text style={styles.loadingText}>
                  Waiting for nearby pharmacies to bid on your order...
                </Text>
              </View>
            ) : quotes.length === 0 ? (
              <View style={styles.emptyBox}>
                <Ionicons name="radio-outline" size={40} color="#94a3b8" />
                <Text style={styles.emptyTitle}>Broadcasting in Progress</Text>
                <Text style={styles.emptyText}>
                  Pharmacies in your zone have been notified. Incoming quotes with discounts will appear here automatically.
                </Text>
              </View>
            ) : (
              quotes.map((q) => {
                const totalMrp = Number(q.total_mrp || 0);
                const quotedTotal = Number(q.total_quoted_price || 0);
                const totalSavings = Number(q.total_savings || Math.max(0, totalMrp - quotedTotal));
                const savingsPct = totalMrp > 0 ? Math.round((totalSavings / totalMrp) * 100) : 0;
                const isWinner = q.status === "SELECTED";

                return (
                  <View key={q.id} style={[styles.quoteCard, isWinner && styles.quoteCardWinner]}>
                    {/* Top Savings Banner */}
                    {totalSavings > 0 ? (
                      <View style={styles.savingsBanner}>
                        <View style={styles.savingsLeft}>
                          <Text style={styles.savingsEmoji}>🎉</Text>
                          <Text style={styles.savingsTitle}>
                            TOTAL SAVINGS: ₹{totalSavings.toFixed(2)}
                          </Text>
                        </View>
                        <View style={styles.savingsBadge}>
                          <Text style={styles.savingsBadgeText}>{savingsPct}% OFF MRP</Text>
                        </View>
                      </View>
                    ) : (
                      <View style={styles.mrpBanner}>
                        <Text style={styles.mrpBannerText}>Standard Reference MRP Offer</Text>
                      </View>
                    )}

                    <View style={styles.quoteCardBody}>
                      {/* Pharmacy Info & Full/Partial Badge */}
                      <View style={styles.pharmaHeader}>
                        <View style={{ flex: 1, paddingRight: 8 }}>
                          <Text style={styles.pharmaName}>{q.pharmacy_name}</Text>
                          <Text style={styles.pharmaAddr} numberOfLines={1}>
                            📍 {q.pharmacy_address || "Licensed Local Store"}
                          </Text>
                        </View>
                        <View
                          style={[
                            styles.fulfillBadge,
                            q.is_full_fulfillment
                              ? styles.fulfillBadgeFull
                              : styles.fulfillBadgePartial
                          ]}
                        >
                          <Text
                            style={[
                              styles.fulfillText,
                              q.is_full_fulfillment
                                ? styles.fulfillTextFull
                                : styles.fulfillTextPartial
                            ]}
                          >
                            {q.is_full_fulfillment
                              ? "FULL FULFILLMENT"
                              : `PARTIAL (${q.available_items_count}/${q.total_items_count})`}
                          </Text>
                        </View>
                      </View>

                      {/* 3-Column Metrics Bar (Total MRP | Quoted Price | You Save) */}
                      <View style={styles.metricsBar}>
                        <View style={styles.metricCol}>
                          <Text style={styles.metricLabel}>TOTAL MRP</Text>
                          <Text style={[styles.metricVal, totalSavings > 0 && styles.strikethrough]}>
                            ₹{totalMrp.toFixed(2)}
                          </Text>
                        </View>
                        <View style={styles.metricCol}>
                          <Text style={[styles.metricLabel, { color: "#065f46" }]}>
                            QUOTED SELLING PRICE
                          </Text>
                          <Text style={[styles.metricVal, { color: "#065f46", fontSize: 15 }]}>
                            ₹{quotedTotal.toFixed(2)}
                          </Text>
                        </View>
                        <View style={styles.metricCol}>
                          <Text style={[styles.metricLabel, { color: "#15803d" }]}>YOU SAVE</Text>
                          <Text style={[styles.metricVal, { color: "#15803d" }]}>
                            ₹{totalSavings.toFixed(2)}
                          </Text>
                        </View>
                      </View>

                      {/* Line Items List */}
                      <View style={styles.itemsList}>
                        {q.items.map((it) => {
                          const itemMrp = Number(it.unit_mrp || 0);
                          const itemSubtotalPrice = Number(it.subtotal_price || 0);
                          const itemSubtotalMrp = Number(it.subtotal_mrp || itemMrp * it.quantity);
                          const itemSavings = Math.max(0, itemSubtotalMrp - itemSubtotalPrice);
                          const discPct =
                            itemSubtotalMrp > 0
                              ? Math.round((itemSavings / itemSubtotalMrp) * 100)
                              : 0;

                          return (
                            <View key={it.id} style={styles.itemBox}>
                              <View style={styles.itemTopRow}>
                                <View style={{ flex: 1, paddingRight: 6 }}>
                                  <Text style={styles.itemTitle}>
                                    • {it.medicine_name} ({it.quantity}x)
                                  </Text>
                                  <Text style={styles.itemStandard}>
                                    Standard MRP: ₹{itemMrp.toFixed(2)}/unit (Total MRP: ₹
                                    {itemSubtotalMrp.toFixed(2)})
                                  </Text>
                                </View>

                                <View style={styles.itemRightPrice}>
                                  <Text style={styles.itemMrpStrike}>
                                    MRP: ₹{itemSubtotalMrp.toFixed(2)}
                                  </Text>
                                  <Text style={styles.itemQuotedPrice}>
                                    Quoted: ₹{itemSubtotalPrice.toFixed(2)}
                                  </Text>
                                  {discPct > 0 && (
                                    <View style={styles.itemDiscBadge}>
                                      <Text style={styles.itemDiscText}>
                                        🏷️ {discPct}% OFF (Save ₹{itemSavings.toFixed(2)})
                                      </Text>
                                    </View>
                                  )}
                                </View>
                              </View>

                              {/* Light Green Box: Medicine Specific Pharmacist Note */}
                              {it.notes ? (
                                <View style={styles.greenNoteBox}>
                                  <Text style={styles.greenNoteLabel}>
                                    📝 <Text style={{ fontWeight: "800" }}>Pharmacy Item Note:</Text>{" "}
                                    <Text style={{ fontWeight: "600" }}>{it.notes}</Text>
                                  </Text>
                                </View>
                              ) : null}
                            </View>
                          );
                        })}
                      </View>

                      {/* White Box with Dashed Border: Main Overall Pharmacist Advice / Remarks */}
                      {q.notes ? (
                        <View style={styles.whiteDashedBox}>
                          <Text style={styles.dashedBoxText}>
                            💬 <Text style={styles.dashedBoxHeader}>Pharmacist Advice / Note:</Text>{" "}
                            {q.notes}
                          </Text>
                        </View>
                      ) : null}

                      {/* Final Price Footer & CTA Button */}
                      <View style={styles.quoteCardFooter}>
                        <View>
                          <Text style={styles.finalLabel}>FINAL QUOTED PRICE</Text>
                          <Text style={styles.finalVal}>₹{quotedTotal.toFixed(2)}</Text>
                        </View>

                        {isWinner ? (
                          <View style={styles.selectedBadge}>
                            <Text style={styles.selectedText}>SELECTED WINNER ✓</Text>
                          </View>
                        ) : (
                          <TouchableOpacity
                            style={styles.selectBtn}
                            activeOpacity={0.85}
                            disabled={isSelecting}
                            onPress={() => handleSelectPharmacy(q.id, q.pharmacy_name)}
                          >
                            {isSelecting ? (
                              <ActivityIndicator size="small" color="#fff" />
                            ) : (
                              <Text style={styles.selectBtnText}>Select This Pharmacy</Text>
                            )}
                          </TouchableOpacity>
                        )}
                      </View>
                    </View>
                  </View>
                );
              })
            )}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.55)",
    justifyContent: "flex-end"
  },
  sheet: {
    backgroundColor: "#f8fafc",
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: "92%",
    paddingBottom: 24
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 16,
    backgroundColor: "#ffffff",
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0"
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8
  },
  title: {
    fontSize: 16,
    fontWeight: "900",
    color: "#0f172a"
  },
  liveTag: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#dcfce7",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    gap: 4
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#16a34a"
  },
  liveTagText: {
    fontSize: 9,
    fontWeight: "900",
    color: "#166534"
  },
  subtext: {
    fontSize: 11.5,
    color: "#64748b",
    marginTop: 2
  },
  closeBtn: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: "#f1f5f9",
    alignItems: "center",
    justifyContent: "center"
  },
  body: {
    padding: 14
  },
  loadingBox: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 50
  },
  loadingText: {
    fontSize: 12.5,
    color: "#64748b",
    marginTop: 12,
    textAlign: "center"
  },
  emptyBox: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 40,
    paddingHorizontal: 20
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: "800",
    color: "#0f172a",
    marginTop: 10
  },
  emptyText: {
    fontSize: 12,
    color: "#64748b",
    textAlign: "center",
    marginTop: 4,
    lineHeight: 16
  },
  quoteCard: {
    backgroundColor: "#ffffff",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    marginBottom: 16,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2
  },
  quoteCardWinner: {
    borderColor: "#16a34a",
    borderWidth: 2
  },
  savingsBanner: {
    backgroundColor: "#059669",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 9,
    paddingHorizontal: 14
  },
  savingsLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6
  },
  savingsEmoji: {
    fontSize: 14
  },
  savingsTitle: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "900"
  },
  savingsBadge: {
    backgroundColor: "rgba(255, 255, 255, 0.25)",
    paddingVertical: 2,
    paddingHorizontal: 8,
    borderRadius: 12
  },
  savingsBadgeText: {
    color: "#ffffff",
    fontSize: 10.5,
    fontWeight: "900"
  },
  mrpBanner: {
    backgroundColor: "#f1f5f9",
    paddingVertical: 6,
    paddingHorizontal: 14
  },
  mrpBannerText: {
    fontSize: 11,
    color: "#475569",
    fontWeight: "700"
  },
  quoteCardBody: {
    padding: 12
  },
  pharmaHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 10
  },
  pharmaName: {
    fontSize: 14.5,
    fontWeight: "800",
    color: "#0f172a"
  },
  pharmaAddr: {
    fontSize: 11,
    color: "#64748b",
    marginTop: 2
  },
  fulfillBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6
  },
  fulfillBadgeFull: {
    backgroundColor: "#ecfdf5",
    borderWidth: 1,
    borderColor: "#a7f3d0"
  },
  fulfillBadgePartial: {
    backgroundColor: "#fffbeb",
    borderWidth: 1,
    borderColor: "#fde68a"
  },
  fulfillText: {
    fontSize: 10,
    fontWeight: "800"
  },
  fulfillTextFull: {
    color: "#166534"
  },
  fulfillTextPartial: {
    color: "#92400e"
  },
  metricsBar: {
    flexDirection: "row",
    backgroundColor: "#f8fafc",
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 6,
    marginBottom: 12
  },
  metricCol: {
    flex: 1,
    alignItems: "center"
  },
  metricLabel: {
    fontSize: 9,
    fontWeight: "800",
    color: "#64748b",
    textTransform: "uppercase",
    marginBottom: 2
  },
  metricVal: {
    fontSize: 13,
    fontWeight: "800",
    color: "#0f172a"
  },
  strikethrough: {
    textDecorationLine: "line-through",
    color: "#94a3b8"
  },
  itemsList: {
    marginBottom: 8
  },
  itemBox: {
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#f1f5f9"
  },
  itemTopRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start"
  },
  itemTitle: {
    fontSize: 13,
    fontWeight: "800",
    color: "#0f172a"
  },
  itemStandard: {
    fontSize: 10.5,
    color: "#64748b",
    marginTop: 2
  },
  itemRightPrice: {
    alignItems: "flex-end"
  },
  itemMrpStrike: {
    fontSize: 10.5,
    color: "#94a3b8",
    textDecorationLine: "line-through"
  },
  itemQuotedPrice: {
    fontSize: 13.5,
    fontWeight: "900",
    color: "#065f46",
    marginTop: 1
  },
  itemDiscBadge: {
    backgroundColor: "#dcfce7",
    borderWidth: 1,
    borderColor: "#86efac",
    paddingHorizontal: 5,
    paddingVertical: 1,
    borderRadius: 4,
    marginTop: 3
  },
  itemDiscText: {
    fontSize: 9.5,
    fontWeight: "800",
    color: "#15803d"
  },
  greenNoteBox: {
    backgroundColor: "#f0fdf4",
    borderWidth: 1,
    borderColor: "#bbf7d0",
    borderRadius: 6,
    paddingVertical: 4,
    paddingHorizontal: 8,
    marginTop: 6
  },
  greenNoteLabel: {
    fontSize: 11,
    color: "#166534",
    lineHeight: 15
  },
  whiteDashedBox: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderStyle: "dashed",
    borderColor: "#cbd5e1",
    borderRadius: 8,
    padding: 10,
    marginTop: 6,
    marginBottom: 8
  },
  dashedBoxHeader: {
    fontSize: 11.5,
    fontWeight: "800",
    color: "#065f46"
  },
  dashedBoxText: {
    fontSize: 11.5,
    color: "#1e293b",
    lineHeight: 16
  },
  quoteCardFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 8,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#e2e8f0"
  },
  finalLabel: {
    fontSize: 9.5,
    color: "#64748b",
    fontWeight: "800",
    textTransform: "uppercase"
  },
  finalVal: {
    fontSize: 17,
    fontWeight: "900",
    color: "#065f46"
  },
  selectBtn: {
    backgroundColor: "#059669",
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8
  },
  selectBtnText: {
    color: "#ffffff",
    fontSize: 12.5,
    fontWeight: "800"
  },
  selectedBadge: {
    backgroundColor: "#dcfce7",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#86efac"
  },
  selectedText: {
    color: "#166534",
    fontSize: 11.5,
    fontWeight: "900"
  }
});
