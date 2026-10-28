import React, { useState, useEffect } from "react";
import { View, Text, StyleSheet } from "react-native";
import { Colors } from "../constants/Config";

interface CountdownTimerProps {
  initialSeconds: number;
  onExpire?: () => void;
}

export const CountdownTimer: React.FC<CountdownTimerProps> = ({ initialSeconds, onExpire }) => {
  const [secondsLeft, setSecondsLeft] = useState<number>(Math.max(0, initialSeconds));

  useEffect(() => {
    setSecondsLeft(Math.max(0, initialSeconds));
  }, [initialSeconds]);

  useEffect(() => {
    if (secondsLeft <= 0) {
      if (onExpire) onExpire();
      return;
    }

    const interval = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          if (onExpire) onExpire();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [secondsLeft, onExpire]);

  const mins = Math.floor(secondsLeft / 60);
  const secs = secondsLeft % 60;
  const formattedTime = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;

  const isUrgent = secondsLeft > 0 && secondsLeft <= 60;
  const isCritical = secondsLeft > 0 && secondsLeft <= 20;
  const isExpired = secondsLeft === 0;

  const timerColor = isExpired
    ? Colors.disabled
    : isCritical
    ? Colors.danger
    : isUrgent
    ? Colors.warning
    : Colors.primary;

  return (
    <View style={[styles.container, { borderColor: timerColor }]}>
      <Text style={styles.label}>
        {isExpired ? "BROADCAST EXPIRED" : "BROADCAST WINDOW (4 MIN MAX)"}
      </Text>
      <Text style={[styles.timer, { color: timerColor }]}>
        {isExpired ? "00:00" : formattedTime}
      </Text>
      {!isExpired && (
        <Text style={styles.subtext}>
          Pharmacies are reviewing and submitting quotes...
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 14,
    borderRadius: 12,
    borderWidth: 2,
    backgroundColor: "#ffffff",
    alignItems: "center",
    marginVertical: 10
  },
  label: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.8,
    color: Colors.textSecondary,
    marginBottom: 4
  },
  timer: {
    fontSize: 32,
    fontWeight: "800",
    fontVariant: ["tabular-nums"]
  },
  subtext: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 4
  }
});
