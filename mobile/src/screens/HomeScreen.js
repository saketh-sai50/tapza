import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  Alert
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { medicinesApi } from "../services/api";
import { CategoryBar } from "../components/CategoryBar";
import { MedicineCard } from "../components/MedicineCard";
import { useApp } from "../context/AppContext";

export const HomeScreen = ({ onOpenAuth }) => {
  const { zone, token, setCartModalVisible } = useApp();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [medicines, setMedicines] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchMedicines = async (q = "", cat = "") => {
    setIsLoading(true);
    try {
      const d = await medicinesApi.search(q, cat, 60);
      setMedicines(d.medicines || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMedicines(query, category);
  }, [category]);

  const handleSearchSubmit = () => {
    fetchMedicines(query, category);
  };

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchSection}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={17} color="#64748b" />
          <TextInput
            style={styles.searchInput}
            placeholder="Search medicines, salts, syrups, healthcare..."
            placeholderTextColor="#94a3b8"
            value={query}
            onChangeText={setQuery}
            onSubmitEditing={handleSearchSubmit}
            returnKeyType="search"
          />
          {query.length > 0 && (
            <TouchableOpacity onPress={() => { setQuery(""); fetchMedicines("", category); }}>
              <Ionicons name="close-circle" size={16} color="#94a3b8" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Category Pills Bar */}
      <CategoryBar
        selected={category}
        onSelect={(catId) => {
          setCategory(catId);
        }}
      />

      {/* Prescription Upload Quick Banner */}
      <View style={styles.rxBannerWrap}>
        <TouchableOpacity
          style={styles.rxBanner}
          activeOpacity={0.85}
          onPress={() => {
            Alert.alert(
              "Prescription Order",
              "You can upload a physical prescription and licensed pharmacies in " + zone + " will digitize and bid on it!",
              [
                { text: "Cancel", style: "cancel" },
                { text: "Proceed to Cart", onPress: () => setCartModalVisible(true) }
              ]
            );
          }}
        >
          <View style={styles.rxIconCircle}>
            <Ionicons name="camera" size={18} color="#059669" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.rxTitle}>Have a Doctor's Prescription?</Text>
            <Text style={styles.rxSub}>
              Upload doctor prescription & get direct competitive quotes
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={16} color="#059669" />
        </TouchableOpacity>
      </View>

      {/* Medicines List */}
      {isLoading ? (
        <View style={styles.centerLoading}>
          <ActivityIndicator size="large" color="#16a34a" />
          <Text style={styles.loadingText}>Loading catalogue in {zone}...</Text>
        </View>
      ) : (
        <FlatList
          data={medicines}
          keyExtractor={(item) => String(item.id)}
          renderItem={({ item }) => <MedicineCard medicine={item} />}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <View style={styles.emptyWrap}>
              <Ionicons name="medkit-outline" size={40} color="#94a3b8" />
              <Text style={styles.emptyTitle}>No Medicines Found</Text>
              <Text style={styles.emptySub}>
                Try searching for generic names like Dolo, Azithral, Pan, or Paracetamol.
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc"
  },
  searchSection: {
    paddingHorizontal: 14,
    paddingTop: 10,
    paddingBottom: 4
  },
  searchBar: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    gap: 8,
    shadowColor: "#000",
    shadowOpacity: 0.03,
    shadowRadius: 4,
    elevation: 1
  },
  searchInput: {
    flex: 1,
    fontSize: 12.5,
    color: "#0f172a"
  },
  rxBannerWrap: {
    paddingHorizontal: 14,
    marginBottom: 6
  },
  rxBanner: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ecfdf5",
    borderWidth: 1,
    borderColor: "#a7f3d0",
    padding: 10,
    borderRadius: 12,
    gap: 10
  },
  rxIconCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#ffffff",
    alignItems: "center",
    justifyContent: "center"
  },
  rxTitle: {
    fontSize: 12.5,
    fontWeight: "800",
    color: "#065f46"
  },
  rxSub: {
    fontSize: 10.5,
    color: "#047857",
    marginTop: 1
  },
  listContent: {
    paddingHorizontal: 14,
    paddingBottom: 110,
    paddingTop: 4
  },
  centerLoading: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center"
  },
  loadingText: {
    fontSize: 12,
    color: "#64748b",
    marginTop: 8
  },
  emptyWrap: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 50
  },
  emptyTitle: {
    fontSize: 14,
    fontWeight: "800",
    color: "#0f172a",
    marginTop: 8
  },
  emptySub: {
    fontSize: 11.5,
    color: "#64748b",
    textAlign: "center",
    marginTop: 4,
    paddingHorizontal: 20
  }
});
