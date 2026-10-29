import React, { useState, useEffect, useRef } from "react";
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
  const searchInputRef = useRef(null);

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

  const renderHeader = () => (
    <View>
      {/* Category Horizontal Row */}
      <CategoryBar
        selected={category}
        onSelect={(catId) => setCategory(catId)}
      />

      {/* Zepto Style Promotional Banner */}
      <View style={styles.promoBanner}>
        <Text style={styles.promoTag}>LOWEST PRICE GUARANTEE</Text>
        <Text style={styles.promoMain}>— FLAT 25% OFF —</Text>
        <Text style={styles.promoSub}>NO MINIMUM ORDER</Text>
        <View style={styles.promoStripWrap}>
          <Text style={styles.promoStrip}>⚡ FREE 15-MIN EXPRESS DELIVERY 🛵</Text>
        </View>

        {/* Trust Pills */}
        <View style={styles.trustRow}>
          <View style={styles.trustPill}>
            <Ionicons name="medkit" size={12} color="#475569" />
            <Text style={styles.trustText}>35,000+ Meds</Text>
          </View>
          <View style={styles.trustPill}>
            <Ionicons name="time" size={12} color="#475569" />
            <Text style={styles.trustText}>In Minutes</Text>
          </View>
          <View style={styles.trustPill}>
            <Ionicons name="shield-checkmark" size={12} color="#475569" />
            <Text style={styles.trustText}>Licensed Shops</Text>
          </View>
        </View>
      </View>

      {/* HERO QUICK ACTION CARD (CREATE ORDER - OPTION A) */}
      <View style={styles.heroCard}>
        <View style={styles.heroTitleRow}>
          <View style={styles.heroTitleLeft}>
            <Ionicons name="flash" size={18} color="#2e1065" />
            <Text style={styles.heroTitleText}>Create New Order</Text>
          </View>
          <View style={styles.heroQuoteBadge}>
            <Text style={styles.heroQuoteText}>Real-Time Quotes</Text>
          </View>
        </View>

        <View style={styles.heroActionsRow}>
          {/* Action 1: Upload Prescription */}
          <TouchableOpacity
            style={styles.heroActionRx}
            activeOpacity={0.85}
            onPress={() => {
              Alert.alert(
                "Upload Prescription",
                "Take a photo or upload doctor prescription. Licensed pharmacies in " + zone + " will read and quote best prices!",
                [
                  { text: "Cancel", style: "cancel" },
                  { text: "Proceed to Cart", onPress: () => setCartModalVisible(true) }
                ]
              );
            }}
          >
            <View style={styles.heroActionHead}>
              <Ionicons name="camera" size={18} color="#be185d" />
              <Text style={styles.heroActionRxTitle}>Upload Rx</Text>
            </View>
            <Text style={styles.heroActionDesc}>
              Let pharmacies scan & quote prices.
            </Text>
          </TouchableOpacity>

          {/* Action 2: Search & Add from Catalog */}
          <TouchableOpacity
            style={styles.heroActionCat}
            activeOpacity={0.85}
            onPress={() => searchInputRef.current?.focus()}
          >
            <View style={styles.heroActionHead}>
              <Ionicons name="search" size={18} color="#059669" />
              <Text style={styles.heroActionCatTitle}>Search Meds</Text>
            </View>
            <Text style={styles.heroActionDesc}>
              Browse 2,750+ medicines & select qty.
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Catalogue Section Header */}
      <View style={styles.catalogHeadingRow}>
        <Text style={styles.catalogTitle}>
          {category ? `${category} Medicines` : "Popular Medicines in " + zone}
        </Text>
        <Text style={styles.catalogSub}>
          {medicines.length} {medicines.length === 1 ? "medicine" : "medicines"} available
        </Text>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Top Search Bar */}
      <View style={styles.searchSection}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={17} color="#64748b" />
          <TextInput
            ref={searchInputRef}
            style={styles.searchInput}
            placeholder='Search "dolo 650", "cough syrup" or brand...'
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

      {/* Medicines List with Integrated Header */}
      {isLoading && medicines.length === 0 ? (
        <View style={styles.centerLoading}>
          <ActivityIndicator size="large" color="#16a34a" />
          <Text style={styles.loadingText}>Loading catalogue in {zone}...</Text>
        </View>
      ) : (
        <FlatList
          data={medicines}
          keyExtractor={(item) => String(item.id)}
          renderItem={({ item }) => <MedicineCard medicine={item} />}
          ListHeaderComponent={renderHeader}
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
    paddingBottom: 4,
    backgroundColor: "#ffffff"
  },
  searchBar: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ffffff",
    borderWidth: 1.5,
    borderColor: "#e2e8f0",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 9,
    gap: 8,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2
  },
  searchInput: {
    flex: 1,
    fontSize: 13,
    color: "#0f172a"
  },
  promoBanner: {
    backgroundColor: "#ffffff",
    borderWidth: 1.5,
    borderColor: "#e2e8f0",
    borderRadius: 16,
    paddingVertical: 14,
    paddingHorizontal: 16,
    alignItems: "center",
    marginHorizontal: 14,
    marginTop: 6,
    marginBottom: 12,
    shadowColor: "#000",
    shadowOpacity: 0.03,
    shadowRadius: 6,
    elevation: 1
  },
  promoTag: {
    fontSize: 10,
    fontWeight: "900",
    color: "#059669",
    letterSpacing: 1,
    marginBottom: 2
  },
  promoMain: {
    fontSize: 20,
    fontWeight: "900",
    color: "#2e1065",
    letterSpacing: -0.5,
    marginVertical: 2
  },
  promoSub: {
    fontSize: 11,
    fontWeight: "800",
    color: "#64748b",
    letterSpacing: 0.5,
    marginBottom: 8
  },
  promoStripWrap: {
    backgroundColor: "#ecfdf5",
    borderWidth: 1,
    borderColor: "#a7f3d0",
    borderRadius: 20,
    paddingVertical: 4,
    paddingHorizontal: 12,
    marginBottom: 10
  },
  promoStrip: {
    fontSize: 10.5,
    fontWeight: "800",
    color: "#065f46"
  },
  trustRow: {
    flexDirection: "row",
    gap: 6
  },
  trustPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#f8fafc",
    borderWidth: 1,
    borderColor: "#e2e8f0",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12
  },
  trustText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#475569"
  },
  heroCard: {
    backgroundColor: "#ffffff",
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: "#e2e8f0",
    padding: 14,
    marginHorizontal: 14,
    marginBottom: 14,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2
  },
  heroTitleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12
  },
  heroTitleLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6
  },
  heroTitleText: {
    fontSize: 15,
    fontWeight: "900",
    color: "#1e1b4b"
  },
  heroQuoteBadge: {
    backgroundColor: "#ecfdf5",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12
  },
  heroQuoteText: {
    fontSize: 10,
    fontWeight: "800",
    color: "#059669"
  },
  heroActionsRow: {
    flexDirection: "row",
    gap: 10
  },
  heroActionRx: {
    flex: 1,
    backgroundColor: "#fdf2f8",
    borderWidth: 1.5,
    borderColor: "#fbcfe8",
    borderRadius: 12,
    padding: 12
  },
  heroActionCat: {
    flex: 1,
    backgroundColor: "#ecfdf5",
    borderWidth: 1.5,
    borderColor: "#a7f3d0",
    borderRadius: 12,
    padding: 12
  },
  heroActionHead: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 4
  },
  heroActionRxTitle: {
    fontSize: 13,
    fontWeight: "900",
    color: "#9d174d"
  },
  heroActionCatTitle: {
    fontSize: 13,
    fontWeight: "900",
    color: "#065f46"
  },
  heroActionDesc: {
    fontSize: 10.5,
    color: "#64748b",
    lineHeight: 14
  },
  catalogHeadingRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "baseline",
    paddingHorizontal: 14,
    marginBottom: 8
  },
  catalogTitle: {
    fontSize: 14,
    fontWeight: "900",
    color: "#0f172a"
  },
  catalogSub: {
    fontSize: 11,
    color: "#64748b"
  },
  listContent: {
    paddingBottom: 110
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
