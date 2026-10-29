import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  RefreshControl
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useApp } from "../context/AppContext";
import { ordersApi, pharmacyApi } from "../services/api";

export const OrdersScreen = ({ onOpenAuth }) => {
  const { token, user, setQuotesModalOrder } = useApp();
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchOrders = async () => {
    if (!token) {
      setOrders([]);
      setIsLoading(false);
      return;
    }

    try {
      if (user?.role === "PHARMACY") {
        const d = await pharmacyApi.getAssignedOrders(token);
        setOrders(d.orders || []);
      } else {
        const d = await ordersApi.getMyOrders(token);
        setOrders(d.orders || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [token, user]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchOrders();
  };

  if (!token) {
    return (
      <View style={styles.centerBox}>
        <Ionicons name="receipt-outline" size={44} color="#94a3b8" />
        <Text style={styles.emptyTitle}>Log In to View Orders</Text>
        <Text style={styles.emptySub}>
          Track live reverse auctions, compare pharmacy quotes, and view past delivery history.
        </Text>
        <TouchableOpacity style={styles.loginBtn} onPress={onOpenAuth}>
          <Text style={styles.loginBtnText}>Log In / Register</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (isLoading) {
    return (
      <View style={styles.centerBox}>
        <ActivityIndicator size="large" color="#16a34a" />
        <Text style={styles.loadingText}>Fetching orders...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={orders}
        keyExtractor={(item) => String(item.id || item.order_id)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.centerBox}>
            <Ionicons name="receipt-outline" size={44} color="#94a3b8" />
            <Text style={styles.emptyTitle}>No Orders Yet</Text>
            <Text style={styles.emptySub}>
              {user?.role === "PHARMACY"
                ? "You haven't been awarded any orders yet. Check the Pharmacy Radar to bid on live customer requests!"
                : "You haven't placed any orders yet. Search medicines and broadcast to local pharmacies!"}
            </Text>
          </View>
        }
        renderItem={({ item }) => {
          const isBroadcasting = item.status === "BROADCASTING";
          const orderId = item.id || item.order_id;
          const totalAmount = Number(item.final_amount || item.total_mrp || 0);

          return (
            <View style={styles.orderCard}>
              <View style={styles.cardTop}>
                <View>
                  <Text style={styles.orderTitle}>Order #{orderId}</Text>
                  <Text style={styles.orderDate}>{item.created_at || "Recent"}</Text>
                </View>
                <View
                  style={[
                    styles.statusBadge,
                    isBroadcasting ? styles.statusBroadcasting : styles.statusStandard
                  ]}
                >
                  <Text
                    style={[
                      styles.statusText,
                      isBroadcasting && styles.statusTextBroadcasting
                    ]}
                  >
                    {isBroadcasting ? "AUCTION LIVE" : item.status}
                  </Text>
                </View>
              </View>

              {/* Items Summary */}
              <View style={styles.itemsSummary}>
                {(item.items || []).map((it, idx) => (
                  <Text key={idx} style={styles.itemSummaryText} numberOfLines={1}>
                    • {it.name || it.medicine_name} ({it.quantity}x)
                  </Text>
                ))}
              </View>

              <View style={styles.cardBottom}>
                <View>
                  <Text style={styles.totalLabel}>
                    {isBroadcasting ? "Starting MRP Ceiling" : "Final Payable"}
                  </Text>
                  <Text style={styles.totalVal}>₹{totalAmount.toFixed(2)}</Text>
                </View>

                {isBroadcasting && (
                  <TouchableOpacity
                    style={styles.viewQuotesBtn}
                    onPress={() => setQuotesModalOrder(item)}
                  >
                    <Text style={styles.viewQuotesBtnText}>
                      View Quotes ({item.quote_count || 0})
                    </Text>
                    <Ionicons name="chevron-forward" size={14} color="#fff" />
                  </TouchableOpacity>
                )}
              </View>
            </View>
          );
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc"
  },
  listContent: {
    padding: 14,
    paddingBottom: 110
  },
  centerBox: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 30
  },
  loadingText: {
    fontSize: 12.5,
    color: "#64748b",
    marginTop: 10
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
  loginBtn: {
    backgroundColor: "#16a34a",
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 16
  },
  loginBtnText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "800"
  },
  orderCard: {
    backgroundColor: "#ffffff",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    padding: 14,
    marginBottom: 12,
    shadowColor: "#000",
    shadowOpacity: 0.03,
    shadowRadius: 4,
    elevation: 1
  },
  cardTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 8
  },
  orderTitle: {
    fontSize: 14.5,
    fontWeight: "900",
    color: "#0f172a"
  },
  orderDate: {
    fontSize: 11,
    color: "#94a3b8",
    marginTop: 2
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6
  },
  statusBroadcasting: {
    backgroundColor: "#dcfce7",
    borderWidth: 1,
    borderColor: "#86efac"
  },
  statusStandard: {
    backgroundColor: "#f1f5f9"
  },
  statusText: {
    fontSize: 10,
    fontWeight: "800",
    color: "#475569"
  },
  statusTextBroadcasting: {
    color: "#166534"
  },
  itemsSummary: {
    backgroundColor: "#f8fafc",
    padding: 8,
    borderRadius: 8,
    marginVertical: 8,
    gap: 3
  },
  itemSummaryText: {
    fontSize: 11.5,
    color: "#334155"
  },
  cardBottom: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 4,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#f1f5f9"
  },
  totalLabel: {
    fontSize: 10,
    color: "#64748b",
    fontWeight: "700",
    textTransform: "uppercase"
  },
  totalVal: {
    fontSize: 15,
    fontWeight: "900",
    color: "#065f46"
  },
  viewQuotesBtn: {
    backgroundColor: "#16a34a",
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingVertical: 7,
    paddingHorizontal: 12,
    borderRadius: 8
  },
  viewQuotesBtnText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "800"
  }
});
