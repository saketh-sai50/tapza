import React, { createContext, useContext, useState, useMemo } from "react";
import { Medicine, CartItem } from "../types";

interface CartContextType {
  items: CartItem[];
  addToCart: (medicine: Medicine, quantity?: number) => void;
  removeFromCart: (medicineId: number) => void;
  updateQuantity: (medicineId: number, quantity: number) => void;
  clearCart: () => void;
  totalMRP: number;
  totalItemCount: number;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [items, setItems] = useState<CartItem[]>([]);

  const addToCart = (medicine: Medicine, quantity = 1) => {
    setItems((prev) => {
      const existingIndex = prev.findIndex((i) => i.medicine.id === medicine.id);
      if (existingIndex > -1) {
        const next = [...prev];
        const newQty = next[existingIndex].quantity + quantity;
        next[existingIndex] = {
          ...next[existingIndex],
          quantity: newQty,
          subtotal_mrp: Number((newQty * medicine.mrp).toFixed(2))
        };
        return next;
      }
      return [
        ...prev,
        {
          medicine,
          quantity,
          subtotal_mrp: Number((quantity * medicine.mrp).toFixed(2))
        }
      ];
    });
  };

  const removeFromCart = (medicineId: number) => {
    setItems((prev) => prev.filter((i) => i.medicine.id !== medicineId));
  };

  const updateQuantity = (medicineId: number, quantity: number) => {
    if (quantity <= 0) {
      removeFromCart(medicineId);
      return;
    }
    setItems((prev) =>
      prev.map((item) => {
        if (item.medicine.id === medicineId) {
          return {
            ...item,
            quantity,
            subtotal_mrp: Number((quantity * item.medicine.mrp).toFixed(2))
          };
        }
        return item;
      })
    );
  };

  const clearCart = () => {
    setItems([]);
  };

  const totalMRP = useMemo(() => {
    return Number(items.reduce((sum, item) => sum + item.subtotal_mrp, 0).toFixed(2));
  }, [items]);

  const totalItemCount = useMemo(() => {
    return items.reduce((sum, item) => sum + item.quantity, 0);
  }, [items]);

  return (
    <CartContext.Provider
      value={{
        items,
        addToCart,
        removeFromCart,
        updateQuantity,
        clearCart,
        totalMRP,
        totalItemCount
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const ctx = useContext(CartContext);
  if (!ctx) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return ctx;
};
