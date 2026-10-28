export const Config = {
  API_URL: process.env.EXPO_PUBLIC_API_URL || "http://127.0.0.1:5000/api",
  BROADCAST_WINDOW_SECONDS: 240,
  DEFAULT_ZONE: "Warangal",
  AVAILABLE_ZONES: ["Warangal", "Hanamkonda", "Kazipet"]
};

export const Colors = {
  primary: "#0ea5e9", // Clean medical cyan/blue
  primaryDark: "#0284c7",
  secondary: "#10b981", // Emerald green
  background: "#f8fafc",
  card: "#ffffff",
  text: "#0f172a",
  textSecondary: "#64748b",
  border: "#e2e8f0",
  danger: "#ef4444",
  warning: "#f59e0b",
  success: "#10b981",
  disabled: "#cbd5e1",
  accent: "#8b5cf6"
};
