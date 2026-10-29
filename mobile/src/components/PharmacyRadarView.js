import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useApp } from "../context/AppContext";
import { pharmacyApi } from "../services/api";

export const PharmacyRadarView = () => {
  const { token, user } = useApp();
  const [broadcasts, setBroadcasts] = useState([]);
  const [drafts, setDrafts] = useState({});
  const [substituteBox, setSubstituteBox] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [submittingOrderId, setSubmittingOrderId] = useState(null);

  const fetchBroadcasts = async () => {
    if (!token || user?.role !== "PHARMACY") return;
    try {
      const d = await pharmacyApi.getBroadcasts(token);
      setBroadcasts(d.broadcasts || []);
      setIsLoading(false);
    } catch (e) {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBroadcasts();
    const interval = setInterval(fetchBroadcasts, 4000);
    return () => clearInterval(interval);
  }, [token, user]);

  const updateItemDraft = (orderId, itemId, field, value) => {
    setDrafts((prev) => {
      const oDraft = prev[orderId] || { items: {}, note: "" };
      const itDraft = oDraft.items[itemId] || {};
      return {
        ...prev,
        [orderId]: {
          ...oDraft,
          items: {
            ...oDraft.items,
            [itemId]: {
              ...itDraft,
              [field]: value
            }
          }
        }
      };
    });
  };

  const updateOrderNoteDraft = (orderId, value) => {
    setDrafts((prev) => {
      const oDraft = prev[orderId] || { items: {}, note: "" };
      return {
        ...prev,
        [orderId]: {
          ...oDraft,
          note: value
        }
      };
    });
  };

  const handleSubmitQuote = async (order) => {
    const orderId = order.order_id || order.id;
    const oDraft = drafts[orderId] || { items: {}, note: "" };

    const itemsPayload = (order.items || []).map((it) => {
      const itemDraft = oDraft.items[it.id] || {};
      const isAvail = itemDraft.is_available !== undefined ? itemDraft.is_available : true;
      const priceVal = itemDraft.price !== undefined ? parseFloat(itemDraft.price) : it.unit_mrp;
      let itemNote = itemDraft.note || "";

      if (itemDraft.custom_name && !itemNote.includes(itemDraft.custom_name)) {
        itemNote = itemNote ? `[Alt: ${itemDraft.custom_name}] ${itemNote}` : `[Alt: ${itemDraft.custom_name}]`;
      }

      return {
        order_item_id: it.id,
        is_available: isAvail,
        unit_selling_price: isAvail ? (priceVal || it.unit_mrp) : 0,
        notes: itemNote || null
      };
    });

    const overallNote = oDraft.note ? oDraft.note.trim() : null;

    setSubmittingOrderId(orderId);
    try {
      await pharmacyApi.submitQuote(orderId, itemsPayload, overallNote, token);
      Alert.alert(
        "Quote Submitted! 🏷️",
        `Your quote for Order #${orderId} was submitted to the customer successfully.`
      );
      // Clear draft for this order
      setDrafts((prev) => {
        const copy = { ...prev };
        delete copy[orderId];
        return copy;
      });
      fetchBroadcasts();
    } catch (e) {
      Alert.alert("Quote Error", e.message || "Failed to submit quote.");
    } finally {
      setSubmittingOrderId(null);
    }
  };

  if (isLoading && broadcasts.length === 0) {
    return (
      <View style={styles.centerBox}>
        <ActivityIndicator size="large" color="#16a34a" />
        <Text style={styles.loadingText}>Scanning {user?.zone || "Warangal"} Zone Broadcasts...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 14 }}>
      <View style={styles.topBanner}>
        <Ionicons name="radio" size={20} color="#16a34a" />
        <View style={{ flex: 1 }}>
          <Text style={styles.bannerTitle}>Pharmacy Live Radar ({user?.zone || "Warangal"})</Text>
          <Text style={styles.bannerSub}>
            Real-time customer orders broadcasting in your zone. Review items and submit your bids!
          </Text>
        </View>
      </View>

      {broadcasts.length === 0 ? (
        <View style={styles.emptyCard}>
          <Ionicons name="medical-outline" size={44} color="#94a3b8" />
          <Text style={styles.emptyTitle}>No Active Broadcasts</Text>
          <Text style={styles.emptySub}>
            There are no customer orders in {user?.zone || "your zone"} right now. New requests will appear here automatically.
          </Text>
        </View>
      ) : (
        broadcasts.map((b) => {
          const orderId = b.order_id || b.id;
          const oDraft = drafts[orderId] || { items: {}, note: "" };

          let computedTotal = 0;
          let totalMrpSum = 0;

          (b.items || []).forEach((it) => {
            const itemDraft = oDraft.items[it.id] || {};
            const isAvail = itemDraft.is_available !== undefined ? itemDraft.is_available : true;
            const priceVal = itemDraft.price !== undefined ? parseFloat(itemDraft.price) : it.unit_mrp;
            if (isAvail) {
              computedTotal += (priceVal || it.unit_mrp) * it.quantity;
              totalMrpSum += it.unit_mrp * it.quantity;
            }
          });

          const savings = Math.max(0, totalMrpSum - computedTotal);
          const savingsPct = totalMrpSum > 0 ? Math.round((savings / totalMrpSum) * 100) : 0;
          const isSubmittingThis = submittingOrderId === orderId;

          return (
            <View key={orderId} style={styles.orderCard}>
              {/* Order Header */}
              <View style={styles.cardHeader}>
                <View>
                  <Text style={styles.orderNumber}>Order #{orderId}</Text>
                  <Text style={styles.orderAddress} numberOfLines={1}>
                    📍 {b.delivery_address}
                  </Text>
                </View>
                <View style={styles.timerBadge}>
                  <Text style={styles.timerText}>{b.remaining_broadcast_seconds}s left</Text>
                </View>
              </View>

              {/* Items List for Bidding */}
              <View style={styles.itemsSection}>
                {(b.items || []).map((it) => {
                  const itemDraft = oDraft.items[it.id] || {};
                  const isAvail = itemDraft.is_available !== undefined ? itemDraft.is_available : true;
                  const priceVal = itemDraft.price !== undefined ? itemDraft.price : String(it.unit_mrp);
                  const showSubBox = substituteBox[`${orderId}_${it.id}`];
                  const displayName = itemDraft.custom_name || it.medicine_name;
                  const isSubstitute = !!itemDraft.custom_name && itemDraft.custom_name !== it.medicine_name;

                  return (
                    <View key={it.id} style={styles.radarItem}>
                      <View style={styles.radarItemTop}>
                        <View style={{ flex: 1 }}>
                          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                            <Text style={styles.itemMedName}>{displayName}</Text>
                            {isSubstitute && (
                              <View style={styles.subBadge}>
                                <Text style={styles.subBadgeText}>Substitute</Text>
                              </View>
                            )}
                          </View>
                          {isSubstitute && (
                            <Text style={styles.origRequested}>
                              Customer requested: {it.medicine_name}
                            </Text>
                          )}
                          <Text style={styles.itemMrpTag}>
                            MRP: ₹{it.unit_mrp.toFixed(2)} • Qty: {it.quantity}
                          </Text>
                        </View>

                        <TouchableOpacity
                          style={styles.substituteBtn}
                          onPress={() =>
                            setSubstituteBox((prev) => ({
                              ...prev,
                              [`${orderId}_${it.id}`]: !showSubBox
                            }))
                          }
                        >
                          <Text style={styles.substituteBtnText}>✏️ Substitute</Text>
                        </TouchableOpacity>
                      </View>

                      {/* Stock Toggle & Selling Price Input */}
                      <View style={styles.stockPriceRow}>
                        <TouchableOpacity
                          style={[styles.stockToggle, isAvail && styles.stockToggleActive]}
                          onPress={() => updateItemDraft(orderId, it.id, "is_available", !isAvail)}
                        >
                          <Ionicons
                            name={isAvail ? "checkbox" : "square-outline"}
                            size={16}
                            color={isAvail ? "#166534" : "#94a3b8"}
                          />
                          <Text style={[styles.stockText, isAvail && styles.stockTextActive]}>
                            {isAvail ? "In Stock" : "Out of Stock"}
                          </Text>
                        </TouchableOpacity>

                        {isAvail && (
                          <View style={styles.sellingPriceBox}>
                            <Text style={styles.spLabel}>Selling Price: ₹</Text>
                            <TextInput
                              style={styles.spInput}
                              keyboardType="numeric"
                              value={String(priceVal)}
                              onChangeText={(val) => updateItemDraft(orderId, it.id, "price", val)}
                            />
                          </View>
                        )}
                      </View>

                      {/* Note for this medicine */}
                      <View style={styles.itemNoteRow}>
                        <Text style={styles.itemNoteLabel}>📝 Note for medicine:</Text>
                        <TextInput
                          style={styles.itemNoteInput}
                          placeholder="e.g. 1 tablet after food, substitute brand..."
                          placeholderTextColor="#94a3b8"
                          value={itemDraft.note || ""}
                          onChangeText={(val) => updateItemDraft(orderId, it.id, "note", val)}
                        />
                      </View>

                      {/* Substitute Box */}
                      {showSubBox && (
                        <View style={styles.substituteBox}>
                          <Text style={styles.subBoxTitle}>
                            Offer Substitute Medicine (from your shelf stock):
                          </Text>
                          <TextInput
                            style={styles.subInput}
                            placeholder="Enter substitute medicine name..."
                            placeholderTextColor="#94a3b8"
                            defaultValue={displayName}
                            onChangeText={(val) => updateItemDraft(orderId, it.id, "custom_name", val)}
                          />
                        </View>
                      )}
                    </View>
                  );
                })}
              </View>

              {/* Main Overall Pharmacist Advice / Remarks */}
              <View style={styles.overallNoteSection}>
                <Text style={styles.overallNoteLabel}>
                  💬 Overall Pharmacist Message / Advice for Customer (Optional):
                </Text>
                <TextInput
                  style={styles.overallNoteInput}
                  placeholder="e.g. Free fast delivery in 15 mins, calling you to confirm..."
                  placeholderTextColor="#94a3b8"
                  value={oDraft.note || ""}
                  onChangeText={(val) => updateOrderNoteDraft(orderId, val)}
                  multiline
                />
              </View>

              {/* Financials & Submit */}
              <View style={styles.cardFooter}>
                <View>
                  <Text style={styles.footerTotalLabel}>Total Quoted</Text>
                  <Text style={styles.footerTotalVal}>₹{computedTotal.toFixed(2)}</Text>
                  <Text style={styles.footerSavings}>
                    {savings > 0 ? `Customer saves ${savingsPct}% OFF` : "Standard MRP"}
                  </Text>
                </View>

                {b.already_quoted ? (
                  <View style={styles.alreadyQuotedBadge}>
                    <Text style={styles.alreadyQuotedText}>ALREADY QUOTED ✓</Text>
                  </View>
                ) : (
                  <TouchableOpacity
                    style={styles.submitBtn}
                    activeOpacity={0.85}
                    disabled={isSubmittingThis}
                    onPress={() => handleSubmitQuote(b)}
                  >
                    {isSubmittingThis ? (
                      <ActivityIndicator size="small" color="#fff" />
                    ) : (
                      <Text style={styles.submitBtnText}>Submit Quote</Text>
                    )}
                  </TouchableOpacity>
                )}
              </View>
            </View>
          );
        })
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc"
  },
  centerBox: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 30
  },
  loadingText: {
    fontSize: 13,
    color: "#64748b",
    marginTop: 10
  },
  topBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: "#ecfdf5",
    borderWidth: 1,
    borderColor: "#a7f3d0",
    padding: 12,
    borderRadius: 12,
    marginBottom: 14
  },
  bannerTitle: {
    fontSize: 13.5,
    fontWeight: "900",
    color: "#065f46"
  },
  bannerSub: {
    fontSize: 11,
    color: "#047857",
    marginTop: 2
  },
  emptyCard: {
    backgroundColor: "#ffffff",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    padding: 30,
    alignItems: "center",
    marginTop: 20
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: "800",
    color: "#0f172a",
    marginTop: 10
  },
  emptySub: {
    fontSize: 12,
    color: "#64748b",
    textAlign: "center",
    marginTop: 4,
    lineHeight: 16
  },
  orderCard: {
    backgroundColor: "#ffffff",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    padding: 14,
    marginBottom: 14,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 12,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#f1f5f9"
  },
  orderNumber: {
    fontSize: 15,
    fontWeight: "900",
    color: "#0f172a"
  },
  orderAddress: {
    fontSize: 11.5,
    color: "#64748b",
    marginTop: 2,
    maxWidth: 200
  },
  timerBadge: {
    backgroundColor: "#fef3c7",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#fde68a"
  },
  timerText: {
    color: "#92400e",
    fontSize: 11,
    fontWeight: "800"
  },
  itemsSection: {
    gap: 10
  },
  radarItem: {
    backgroundColor: "#f8fafc",
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 10,
    padding: 10
  },
  radarItemTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 6
  },
  itemMedName: {
    fontSize: 13,
    fontWeight: "800",
    color: "#0f172a"
  },
  subBadge: {
    backgroundColor: "#fef3c7",
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 4
  },
  subBadgeText: {
    color: "#92400e",
    fontSize: 9.5,
    fontWeight: "800"
  },
  origRequested: {
    fontSize: 10.5,
    color: "#64748b",
    marginTop: 2
  },
  itemMrpTag: {
    fontSize: 11,
    color: "#065f46",
    fontWeight: "700",
    marginTop: 2
  },
  substituteBtn: {
    backgroundColor: "#eff6ff",
    borderWidth: 1,
    borderColor: "#bfdbfe",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6
  },
  substituteBtnText: {
    color: "#1d4ed8",
    fontSize: 11,
    fontWeight: "800"
  },
  stockPriceRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 6,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: "#e2e8f0"
  },
  stockToggle: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6
  },
  stockToggleActive: {},
  stockText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#94a3b8"
  },
  stockTextActive: {
    color: "#166534"
  },
  sellingPriceBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4
  },
  spLabel: {
    fontSize: 11,
    color: "#0f172a",
    fontWeight: "700"
  },
  spInput: {
    backgroundColor: "#ffffff",
    borderWidth: 1.5,
    borderColor: "#059669",
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 2,
    fontSize: 12,
    fontWeight: "800",
    minWidth: 60,
    textAlign: "right"
  },
  itemNoteRow: {
    marginTop: 6
  },
  itemNoteLabel: {
    fontSize: 10.5,
    fontWeight: "800",
    color: "#334155",
    marginBottom: 3
  },
  itemNoteInput: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
    fontSize: 11,
    color: "#0f172a"
  },
  substituteBox: {
    marginTop: 8,
    backgroundColor: "#f0fdf4",
    borderWidth: 1,
    borderColor: "#86efac",
    padding: 8,
    borderRadius: 6
  },
  subBoxTitle: {
    fontSize: 10.5,
    fontWeight: "800",
    color: "#166534",
    marginBottom: 4
  },
  subInput: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#86efac",
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
    fontSize: 11.5
  },
  overallNoteSection: {
    marginTop: 10,
    backgroundColor: "#f8fafc",
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 8,
    padding: 10
  },
  overallNoteLabel: {
    fontSize: 11,
    fontWeight: "800",
    color: "#0f172a",
    marginBottom: 4
  },
  overallNoteInput: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 6,
    fontSize: 11.5,
    minHeight: 40
  },
  cardFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#e2e8f0"
  },
  footerTotalLabel: {
    fontSize: 9.5,
    color: "#64748b",
    fontWeight: "800",
    textTransform: "uppercase"
  },
  footerTotalVal: {
    fontSize: 16,
    fontWeight: "900",
    color: "#065f46"
  },
  footerSavings: {
    fontSize: 10,
    color: "#16a34a",
    fontWeight: "700"
  },
  submitBtn: {
    backgroundColor: "#16a34a",
    paddingVertical: 9,
    paddingHorizontal: 18,
    borderRadius: 8
  },
  submitBtnText: {
    color: "#ffffff",
    fontSize: 12.5,
    fontWeight: "800"
  },
  alreadyQuotedBadge: {
    backgroundColor: "#ecfdf5",
    borderWidth: 1,
    borderColor: "#86efac",
    paddingVertical: 7,
    paddingHorizontal: 12,
    borderRadius: 8
  },
  alreadyQuotedText: {
    color: "#166534",
    fontSize: 11,
    fontWeight: "900"
  }
});
