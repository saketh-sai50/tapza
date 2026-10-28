import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl
} from "react-native";
import { AppNotification } from "../../types";
import { api } from "../../services/api";
import { Colors } from "../../constants/Config";

export default function NotificationsScreen() {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchNotifications = async () => {
    try {
      const res = await api.get<{ notifications: AppNotification[] }>("/notifications");
      setNotifications(res.notifications);
    } catch (err) {
      console.error("Failed to fetch notifications:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleMarkRead = async (id: number) => {
    try {
      await api.post(`/notifications/${id}/read`, {});
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (err) {
      console.error("Failed to mark read:", err);
    }
  };

  const getEventBadge = (type: string) => {
    switch (type) {
      case "ORDER_CONFIRMED":
        return { label: "CONFIRMED", color: Colors.secondary, bg: "#dcfce7" };
      case "NEW_QUOTE_RECEIVED":
        return { label: "NEW QUOTE", color: Colors.primaryDark, bg: "#e0f2fe" };
      case "STATUS_UPDATE":
        return { label: "STATUS", color: Colors.accent, bg: "#ede9fe" };
      case "MOCK_PAYMENT_COMPLETED":
        return { label: "MOCK PAID", color: Colors.warning, bg: "#fef3c7" };
      case "ORDER_REJECTED":
        return { label: "REJECTED", color: Colors.danger, bg: "#fee2e2" };
      default:
        return { label: "UPDATE", color: Colors.textSecondary, bg: "#f1f5f9" };
    }
  };

  return (
    <View style={styles.container}>
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : notifications.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No notifications yet</Text>
          <Text style={styles.emptySubtitle}>
            Updates regarding quotes, confirmations, and deliveries will appear here.
          </Text>
        </View>
      ) : (
        <FlatList
          data={notifications}
          keyExtractor={(item) => String(item.id)}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchNotifications(); }} />
          }
          contentContainerStyle={{ padding: 14 }}
          renderItem={({ item }) => {
            const badge = getEventBadge(item.event_type);

            return (
              <TouchableOpacity
                style={[styles.card, !item.is_read && styles.cardUnread]}
                onPress={() => handleMarkRead(item.id)}
                activeOpacity={0.7}
              >
                <View style={styles.cardHeader}>
                  <View style={[styles.badge, { backgroundColor: badge.bg }]}>
                    <Text style={[styles.badgeText, { color: badge.color }]}>{badge.label}</Text>
                  </View>
                  <Text style={styles.dateText}>{item.created_at}</Text>
                </View>

                <Text style={styles.title}>{item.title}</Text>
                <Text style={styles.message}>{item.message}</Text>

                {!item.is_read && (
                  <View style={styles.unreadDot} />
                )}
              </TouchableOpacity>
            );
          }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center"
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 30
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
    marginTop: 6
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border,
    shadowColor: "#000",
    shadowOpacity: 0.03,
    shadowOffset: { width: 0, height: 1 },
    shadowRadius: 3,
    elevation: 1
  },
  cardUnread: {
    borderColor: "#bfdbfe",
    backgroundColor: "#f8fafc"
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6
  },
  badgeText: {
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.5
  },
  dateText: {
    fontSize: 11,
    color: Colors.textSecondary
  },
  title: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text
  },
  message: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 4,
    lineHeight: 18
  },
  unreadDot: {
    position: "absolute",
    top: 14,
    right: 14,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.primary
  }
});
