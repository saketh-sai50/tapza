import React, { createContext, useContext, useState, useEffect } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { authApi, ordersApi } from "../services/api";

const AppContext = createContext(null);

export const AppProvider = ({ children }) => {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [zone, setZone] = useState("Warangal");
  const [cart, setCart] = useState({});
  const [activeOrder, setActiveOrder] = useState(null);
  const [quotesModalOrder, setQuotesModalOrder] = useState(null);
  const [cartModalVisible, setCartModalVisible] = useState(false);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);

  // Load persisted session on boot
  useEffect(() => {
    (async () => {
      try {
        const storedToken = await AsyncStorage.getItem("tapza_token");
        const storedUser = await AsyncStorage.getItem("tapza_user");
        const storedZone = await AsyncStorage.getItem("tapza_zone");
        const storedCart = await AsyncStorage.getItem("tapza_cart");

        if (storedToken) setToken(storedToken);
        if (storedUser) setUser(JSON.parse(storedUser));
        if (storedZone) setZone(storedZone);
        if (storedCart) setCart(JSON.parse(storedCart));
      } catch (e) {
        console.error("Storage restore error:", e);
      } finally {
        setIsLoadingAuth(false);
      }
    })();
  }, []);

  // Sync cart changes to storage
  useEffect(() => {
    AsyncStorage.setItem("tapza_cart", JSON.stringify(cart)).catch(() => {});
  }, [cart]);

  // Poll for active live order if customer is authenticated
  useEffect(() => {
    if (!token || user?.role !== "CUSTOMER") {
      setActiveOrder(null);
      return;
    }

    const checkActive = async () => {
      try {
        const d = await ordersApi.getMyOrders(token);
        const orders = d.orders || [];
        const live = orders.find(
          (o) => o.status === "BROADCASTING" || o.status === "CONFIRMED_PENDING_PHARMACY"
        );
        setActiveOrder(live || null);
      } catch (e) {
        // quiet error on background poll
      }
    };

    checkActive();
    const interval = setInterval(checkActive, 5000);
    return () => clearInterval(interval);
  }, [token, user]);

  const login = async (email, password, role = "CUSTOMER") => {
    const res = await authApi.login(email, password, role);
    setToken(res.token);
    setUser(res.user);
    if (res.user.zone) setZone(res.user.zone);

    await AsyncStorage.setItem("tapza_token", res.token);
    await AsyncStorage.setItem("tapza_user", JSON.stringify(res.user));
    if (res.user.zone) await AsyncStorage.setItem("tapza_zone", res.user.zone);
    return res;
  };

  const logout = async () => {
    setToken(null);
    setUser(null);
    setCart({});
    setActiveOrder(null);
    setQuotesModalOrder(null);
    setCartModalVisible(false);

    await AsyncStorage.removeItem("tapza_token");
    await AsyncStorage.removeItem("tapza_user");
    await AsyncStorage.removeItem("tapza_cart");
  };

  const updateZone = async (newZone) => {
    setZone(newZone);
    await AsyncStorage.setItem("tapza_zone", newZone);
  };

  const addToCart = (med) => {
    setCart((prev) => {
      const existing = prev[med.id];
      const newQty = existing ? existing.quantity + 1 : 1;
      return {
        ...prev,
        [med.id]: {
          id: med.id,
          name: med.name,
          mrp: Number(med.mrp || 0),
          dosage_form: med.dosage_form || "Tablet",
          pack_size: med.pack_size || "1 Unit",
          quantity: newQty
        }
      };
    });
  };

  const updateCartQty = (medId, delta) => {
    setCart((prev) => {
      const existing = prev[medId];
      if (!existing) return prev;
      const nextQty = existing.quantity + delta;
      if (nextQty <= 0) {
        const copy = { ...prev };
        delete copy[medId];
        return copy;
      }
      return {
        ...prev,
        [medId]: { ...existing, quantity: nextQty }
      };
    });
  };

  const clearCart = () => {
    setCart({});
    AsyncStorage.removeItem("tapza_cart").catch(() => {});
  };

  const cartItems = Object.values(cart);
  const cartTotalMrp = cartItems.reduce((acc, it) => acc + it.mrp * it.quantity, 0);
  const cartItemCount = cartItems.reduce((acc, it) => acc + it.quantity, 0);

  return (
    <AppContext.Provider
      value={{
        token,
        user,
        zone,
        cart,
        cartItems,
        cartTotalMrp,
        cartItemCount,
        activeOrder,
        quotesModalOrder,
        cartModalVisible,
        isLoadingAuth,
        login,
        logout,
        updateZone,
        addToCart,
        updateCartQty,
        clearCart,
        setActiveOrder,
        setQuotesModalOrder,
        setCartModalVisible
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error("useApp must be used within an AppProvider");
  return context;
};
