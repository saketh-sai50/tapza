import React, { useState } from "react";
import {
  StyleSheet,
  View,
  TouchableOpacity,
  Text,
  StatusBar
} from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";

import { AppProvider, useApp } from "./src/context/AppContext";
import { Header } from "./src/components/Header";
import { FloatingCart } from "./src/components/FloatingCart";
import { LiveOrderTracker } from "./src/components/LiveOrderTracker";
import { CartModal } from "./src/components/CartModal";
import { QuotesModal } from "./src/components/QuotesModal";
import { AuthModal } from "./src/components/AuthModal";

import { HomeScreen } from "./src/screens/HomeScreen";
import { OrdersScreen } from "./src/screens/OrdersScreen";
import { ProfileScreen } from "./src/screens/ProfileScreen";
import { PharmacyRadarView } from "./src/components/PharmacyRadarView";

const MainContent = () => {
  const { user, activeOrder } = useApp();
  const [currentTab, setCurrentTab] = useState("HOME");
  const [authModalVisible, setAuthModalVisible] = useState(false);

  const isPharmacy = user?.role === "PHARMACY";

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1e1b4b" />

      {/* Top Header */}
      <Header onOpenAuth={() => setAuthModalVisible(true)} />

      {/* Main Screen Content */}
      <View style={styles.screenWrapper}>
        {isPharmacy ? (
          <>
            {currentTab === "HOME" && <PharmacyRadarView />}
            {currentTab === "ORDERS" && <OrdersScreen onOpenAuth={() => setAuthModalVisible(true)} />}
            {currentTab === "PROFILE" && <ProfileScreen onOpenAuth={() => setAuthModalVisible(true)} />}
          </>
        ) : (
          <>
            {currentTab === "HOME" && <HomeScreen onOpenAuth={() => setAuthModalVisible(true)} />}
            {currentTab === "ORDERS" && <OrdersScreen onOpenAuth={() => setAuthModalVisible(true)} />}
            {currentTab === "PROFILE" && <ProfileScreen onOpenAuth={() => setAuthModalVisible(true)} />}
          </>
        )}
      </View>

      {/* Floating Cart (Customer only) */}
      {!isPharmacy && currentTab === "HOME" && <FloatingCart />}

      {/* Persistent Live Order Floating Tracker (Customer only) */}
      {!isPharmacy && <LiveOrderTracker />}

      {/* Modals */}
      <CartModal onOpenAuth={() => setAuthModalVisible(true)} />
      <QuotesModal />
      <AuthModal
        visible={authModalVisible}
        onClose={() => setAuthModalVisible(false)}
      />

      {/* Bottom Navigation Bar */}
      <View style={styles.bottomNav}>
        <TouchableOpacity
          style={styles.navItem}
          activeOpacity={0.7}
          onPress={() => setCurrentTab("HOME")}
        >
          <Ionicons
            name={isPharmacy ? "radio-outline" : "home-outline"}
            size={22}
            color={currentTab === "HOME" ? "#16a34a" : "#64748b"}
          />
          <Text style={[styles.navText, currentTab === "HOME" && styles.navTextActive]}>
            {isPharmacy ? "Live Radar" : "Home"}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.navItem}
          activeOpacity={0.7}
          onPress={() => setCurrentTab("ORDERS")}
        >
          <View>
            <Ionicons
              name={isPharmacy ? "trophy-outline" : "bag-handle-outline"}
              size={22}
              color={currentTab === "ORDERS" ? "#16a34a" : "#64748b"}
            />
            {activeOrder && !isPharmacy && (
              <View style={styles.navBadge}>
                <Text style={styles.navBadgeText}>1</Text>
              </View>
            )}
          </View>
          <Text style={[styles.navText, currentTab === "ORDERS" && styles.navTextActive]}>
            {isPharmacy ? "Awarded" : "My Orders"}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.navItem}
          activeOpacity={0.7}
          onPress={() => setCurrentTab("PROFILE")}
        >
          <Ionicons
            name="person-outline"
            size={22}
            color={currentTab === "PROFILE" ? "#16a34a" : "#64748b"}
          />
          <Text style={[styles.navText, currentTab === "PROFILE" && styles.navTextActive]}>
            Profile
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default function App() {
  return (
    <SafeAreaProvider>
      <AppProvider>
        <MainContent />
      </AppProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff"
  },
  screenWrapper: {
    flex: 1
  },
  bottomNav: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-around",
    backgroundColor: "#ffffff",
    borderTopWidth: 1,
    borderTopColor: "#e2e8f0",
    paddingVertical: 8,
    paddingBottom: 14,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 8
  },
  navItem: {
    alignItems: "center",
    justifyContent: "center",
    minWidth: 70
  },
  navText: {
    fontSize: 10.5,
    fontWeight: "700",
    color: "#64748b",
    marginTop: 2
  },
  navTextActive: {
    color: "#16a34a",
    fontWeight: "800"
  },
  navBadge: {
    position: "absolute",
    top: -3,
    right: -6,
    backgroundColor: "#16a34a",
    width: 14,
    height: 14,
    borderRadius: 7,
    alignItems: "center",
    justifyContent: "center"
  },
  navBadgeText: {
    color: "#ffffff",
    fontSize: 9,
    fontWeight: "900"
  }
});
