import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator
} from "react-native";
import { Medicine } from "../../types";
import { api } from "../../services/api";
import { useCart } from "../../context/CartContext";
import { MedicineCard } from "../../components/MedicineCard";
import { Colors } from "../../constants/Config";

export default function CustomerCatalogueScreen({ navigation }: any) {
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  const { addToCart, items, totalMRP, totalItemCount } = useCart();

  const loadData = async () => {
    try {
      setLoading(true);
      let query = "/medicines?";
      if (search) query += `search=${encodeURIComponent(search)}&`;
      if (selectedCategory) query += `category=${encodeURIComponent(selectedCategory)}&`;

      const [medRes, catRes] = await Promise.all([
        api.get<{ medicines: Medicine[] }>(query),
        api.get<{ categories: string[] }>("/medicines/categories")
      ]);

      setMedicines(medRes.medicines);
      setCategories(catRes.categories);
    } catch (err) {
      console.error("Failed to load catalogue:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadData();
    }, 250);
    return () => clearTimeout(timer);
  }, [search, selectedCategory]);

  const getInCartCount = (medId: number) => {
    const found = items.find((i) => i.medicine.id === medId);
    return found ? found.quantity : 0;
  };

  return (
    <View style={styles.container}>
      {/* Search Input */}
      <View style={styles.searchSection}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search medicines, salts, manufacturers..."
          placeholderTextColor="#94a3b8"
          value={search}
          onChangeText={setSearch}
        />
      </View>

      {/* Category Pills */}
      <View style={styles.categoryBar}>
        <TouchableOpacity
          style={[styles.categoryPill, !selectedCategory && styles.categoryPillActive]}
          onPress={() => setSelectedCategory("")}
        >
          <Text style={[styles.categoryText, !selectedCategory && styles.categoryTextActive]}>
            All
          </Text>
        </TouchableOpacity>
        {categories.map((cat) => (
          <TouchableOpacity
            key={cat}
            style={[styles.categoryPill, selectedCategory === cat && styles.categoryPillActive]}
            onPress={() => setSelectedCategory(cat === selectedCategory ? "" : cat)}
          >
            <Text style={[styles.categoryText, selectedCategory === cat && styles.categoryTextActive]}>
              {cat}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Medicine Feed */}
      {loading ? (
        <View style={styles.loader}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : medicines.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>No medicines found</Text>
          <Text style={styles.emptySubtitle}>Try adjusting your search terms or filter.</Text>
        </View>
      ) : (
        <FlatList
          data={medicines}
          keyExtractor={(item) => String(item.id)}
          renderItem={({ item }) => (
            <MedicineCard
              medicine={item}
              onAddToCart={(med, qty) => addToCart(med, qty)}
              inCartCount={getInCartCount(item.id)}
            />
          )}
          contentContainerStyle={{ paddingBottom: 100 }}
        />
      )}

      {/* Floating Cart Bar */}
      {totalItemCount > 0 && (
        <View style={styles.cartBar}>
          <View>
            <Text style={styles.cartCountText}>{totalItemCount} item(s) selected</Text>
            <Text style={styles.cartTotalText}>Estimated MRP: ${totalMRP.toFixed(2)}</Text>
          </View>
          <TouchableOpacity
            style={styles.viewCartBtn}
            onPress={() => navigation?.navigate?.("cart")}
          >
            <Text style={styles.viewCartBtnText}>Review Cart &rarr;</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background
  },
  searchSection: {
    padding: 12,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: Colors.border
  },
  searchInput: {
    backgroundColor: "#f1f5f9",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: Colors.text
  },
  categoryBar: {
    flexDirection: "row",
    paddingHorizontal: 12,
    paddingVertical: 8,
    gap: 8,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    flexWrap: "wrap"
  },
  categoryPill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: "#f1f5f9"
  },
  categoryPillActive: {
    backgroundColor: Colors.primary
  },
  categoryText: {
    fontSize: 12,
    fontWeight: "600",
    color: Colors.textSecondary
  },
  categoryTextActive: {
    color: "#ffffff"
  },
  loader: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center"
  },
  emptyState: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text
  },
  emptySubtitle: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 4
  },
  cartBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: Colors.text,
    paddingVertical: 14,
    paddingHorizontal: 20,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  cartCountText: {
    color: "#cbd5e1",
    fontSize: 12
  },
  cartTotalText: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "800"
  },
  viewCartBtn: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8
  },
  viewCartBtnText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 14
  }
});
