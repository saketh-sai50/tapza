import React from "react";
import {
  ScrollView,
  TouchableOpacity,
  Text,
  StyleSheet
} from "react-native";
import { MaterialCommunityIcons, FontAwesome5, Ionicons } from "@expo/vector-icons";

const CATEGORIES = [
  { id: "", name: "All Meds", icon: "pill", type: "MaterialCommunityIcons" },
  { id: "Pharmacy", name: "Pharmacy", icon: "medical-bag", type: "MaterialCommunityIcons" },
  { id: "Diabetic Care", name: "Diabetic Care", icon: "water-outline", type: "Ionicons" },
  { id: "Cardiac Care", name: "Cardiac Care", icon: "heartbeat", type: "FontAwesome5" },
  { id: "Pain Relief", name: "Pain Relief", icon: "flash-outline", type: "Ionicons" },
  { id: "Vitamins & Supplements", name: "Vitamins", icon: "fruit-cherries", type: "MaterialCommunityIcons" },
  { id: "Digestive Health", name: "Digestive", icon: "stomach", type: "MaterialCommunityIcons" }
];

export const CategoryBar = ({ selected, onSelect }) => {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.container}
    >
      {CATEGORIES.map((cat) => {
        const isSelected = selected === cat.id;
        return (
          <TouchableOpacity
            key={cat.id}
            style={[styles.pill, isSelected && styles.pillActive]}
            activeOpacity={0.7}
            onPress={() => onSelect(cat.id)}
          >
            {cat.type === "MaterialCommunityIcons" && (
              <MaterialCommunityIcons
                name={cat.icon}
                size={14}
                color={isSelected ? "#ffffff" : "#475569"}
              />
            )}
            {cat.type === "Ionicons" && (
              <Ionicons
                name={cat.icon}
                size={14}
                color={isSelected ? "#ffffff" : "#475569"}
              />
            )}
            {cat.type === "FontAwesome5" && (
              <FontAwesome5
                name={cat.icon}
                size={12}
                color={isSelected ? "#ffffff" : "#475569"}
              />
            )}
            <Text style={[styles.pillText, isSelected && styles.pillTextActive]}>
              {cat.name}
            </Text>
          </TouchableOpacity>
        );
      })}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    gap: 8,
    alignItems: "center"
  },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e2e8f0",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20,
    gap: 6
  },
  pillActive: {
    backgroundColor: "#16a34a",
    borderColor: "#16a34a"
  },
  pillText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#475569"
  },
  pillTextActive: {
    color: "#ffffff"
  }
});
