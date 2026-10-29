import React from "react";
import {
  ScrollView,
  TouchableOpacity,
  View,
  Text,
  StyleSheet
} from "react-native";
import { MaterialCommunityIcons, FontAwesome5, Ionicons } from "@expo/vector-icons";

const CATEGORIES = [
  { id: "", name: "Pharmacy", icon: "pill", type: "MaterialCommunityIcons" },
  { id: "Antidiabetic", name: "Diabetic care", icon: "water-outline", type: "Ionicons" },
  { id: "Analgesic", name: "Self care", icon: "heart-outline", type: "Ionicons" },
  { id: "Ayurveda", name: "Ayurveda", icon: "leaf", type: "Ionicons" },
  { id: "Antibiotic", name: "Antibiotics", icon: "shield-outline", type: "Ionicons" },
  { id: "Cardiovascular", name: "Heart Care", icon: "heartbeat", type: "FontAwesome5" }
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
            style={[styles.item, isSelected && styles.itemActive]}
            activeOpacity={0.75}
            onPress={() => onSelect(cat.id)}
          >
            <View style={[styles.iconWrap, isSelected && styles.iconWrapActive]}>
              {cat.type === "MaterialCommunityIcons" && (
                <MaterialCommunityIcons
                  name={cat.icon}
                  size={20}
                  color={isSelected ? "#16a34a" : "#475569"}
                />
              )}
              {cat.type === "Ionicons" && (
                <Ionicons
                  name={cat.icon}
                  size={19}
                  color={isSelected ? "#16a34a" : "#475569"}
                />
              )}
              {cat.type === "FontAwesome5" && (
                <FontAwesome5
                  name={cat.icon}
                  size={17}
                  color={isSelected ? "#16a34a" : "#475569"}
                />
              )}
            </View>
            <Text
              style={[styles.title, isSelected && styles.titleActive]}
              numberOfLines={1}
            >
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
    gap: 12,
    alignItems: "center"
  },
  item: {
    alignItems: "center",
    justifyContent: "center",
    width: 68
  },
  itemActive: {},
  iconWrap: {
    width: 48,
    height: 48,
    borderRadius: 14,
    backgroundColor: "#ffffff",
    borderWidth: 1.5,
    borderColor: "#e2e8f0",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
    marginBottom: 5
  },
  iconWrapActive: {
    backgroundColor: "#ecfdf5",
    borderColor: "#16a34a",
    borderWidth: 2
  },
  title: {
    fontSize: 11,
    fontWeight: "700",
    color: "#475569",
    textAlign: "center"
  },
  titleActive: {
    color: "#166534",
    fontWeight: "800"
  }
});
