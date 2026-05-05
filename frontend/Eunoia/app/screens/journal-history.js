// app/screens/journal-history.js
// Lists all past journal entries (paginated).
// Tap an entry → expands inline to read the full content.

import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  SafeAreaView, ActivityIndicator, Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft, BookOpen, ChevronDown, ChevronUp, PenLine } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';
import { getJournalHistory } from '../../src/api/tracking';

const SENTIMENT_COLOR = {
  positive: '#8BC34A',
  neutral:  COLORS.secondary,
  negative: '#F4A261',
  sadness:  '#8FAADC',
  anger:    '#E57373',
  fear:     '#CDB4DB',
  joy:      '#FFD166',
};

export default function JournalHistoryScreen() {
  const router = useRouter();

  const [entries,     setEntries]     = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page,        setPage]        = useState(1);
  const [hasMore,     setHasMore]     = useState(true);
  const [total,       setTotal]       = useState(0);
  const [expandedId,  setExpandedId]  = useState(null);

  const fetchEntries = useCallback(async (pageNum = 1, append = false) => {
    if (pageNum === 1) setLoading(true); else setLoadingMore(true);
    try {
      const { data } = await getJournalHistory(pageNum, 20);
      const newEntries = data.entries ?? [];
      setEntries((prev) => append ? [...prev, ...newEntries] : newEntries);
      setTotal(data.total ?? 0);
      setHasMore(newEntries.length === 20);
    } catch {
      Alert.alert('Error', 'Could not load journal history.');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => { fetchEntries(1); }, []);

  const loadMore = () => {
    if (!hasMore || loadingMore) return;
    const nextPage = page + 1;
    setPage(nextPage);
    fetchEntries(nextPage, true);
  };

  const formatDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', {
      weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
    });
  };

  const wordCount = (text = '') =>
    text.split(/\s+/).filter((w) => w).length;

  const sentimentColor = (label) =>
    SENTIMENT_COLOR[label?.toLowerCase()] ?? COLORS.text;

  const renderEntry = ({ item }) => {
    const isExpanded = expandedId === item.id;
    const color = sentimentColor(item.sentiment_label);

    return (
      <TouchableOpacity
        style={[styles.entryCard, isExpanded && styles.entryCardExpanded]}
        onPress={() => setExpandedId(isExpanded ? null : item.id)}
        activeOpacity={0.85}
      >
        {/* Card header */}
        <View style={styles.entryHeader}>
          <View style={styles.entryIconWrap}>
            <BookOpen color={COLORS.primary} size={18} />
          </View>
          <View style={styles.entryMeta}>
            <Text style={styles.entryDate}>{formatDate(item.created_at)}</Text>
            <Text style={styles.entryWordCount}>{wordCount(item.content)} words</Text>
          </View>
          {item.sentiment_label && (
            <View style={[styles.sentimentBadge, { backgroundColor: color + '20' }]}>
              <Text style={[styles.sentimentText, { color }]}>
                {item.sentiment_label}
              </Text>
            </View>
          )}
          {isExpanded
            ? <ChevronUp color={COLORS.text} size={18} opacity={0.3} />
            : <ChevronDown color={COLORS.text} size={18} opacity={0.3} />}
        </View>

        {/* Preview (always shown) */}
        {!isExpanded && (
          <Text style={styles.entryPreview} numberOfLines={2}>
            {item.content}
          </Text>
        )}

        {/* Full content (expanded) */}
        {isExpanded && (
          <Text style={styles.entryFull}>{item.content}</Text>
        )}
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <Header onBack={() => router.back()} />
        <View style={styles.center}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <Header onBack={() => router.back()} count={total} />
      <FlatList
        data={entries}
        keyExtractor={(item) => item.id}
        renderItem={renderEntry}
        contentContainerStyle={styles.list}
        onEndReached={loadMore}
        onEndReachedThreshold={0.3}
        ListFooterComponent={
          loadingMore
            ? <ActivityIndicator color={COLORS.primary} style={{ margin: 20 }} />
            : null
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <PenLine color={COLORS.text} size={48} opacity={0.2} />
            <Text style={styles.emptyText}>No journal entries yet</Text>
            <Text style={styles.emptySubtext}>Start writing from the Today tab</Text>
            <TouchableOpacity
              style={styles.writeBtn}
              onPress={() => router.push('/screens/journal')}
            >
              <Text style={styles.writeBtnText}>Write an entry →</Text>
            </TouchableOpacity>
          </View>
        }
        ItemSeparatorComponent={() => <View style={styles.separator} />}
      />
    </SafeAreaView>
  );
}

function Header({ onBack, count }) {
  return (
    <View style={styles.header}>
      <TouchableOpacity onPress={onBack} style={styles.backBtn}>
        <ChevronLeft color={COLORS.text} size={28} />
      </TouchableOpacity>
      <View>
        <Text style={styles.headerTitle}>Journal History</Text>
        {count != null && (
          <Text style={styles.headerSubtitle}>{count} entr{count !== 1 ? 'ies' : 'y'}</Text>
        )}
      </View>
      <View style={{ width: 40 }} />
    </View>
  );
}

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: COLORS.background },
  center:       { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
  },
  backBtn:      { padding: 4 },
  headerTitle:  { fontSize: 22, fontWeight: 'bold', color: COLORS.text, textAlign: 'center' },
  headerSubtitle: { fontSize: 13, color: COLORS.text, opacity: 0.45, textAlign: 'center' },
  list:         { paddingHorizontal: 20, paddingBottom: 40, paddingTop: 8 },
  entryCard: {
    backgroundColor: COLORS.card, borderRadius: 20, padding: 18,
    elevation: 2, shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 8,
  },
  entryCardExpanded: { borderLeftWidth: 4, borderLeftColor: COLORS.primary },
  entryHeader:  { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 10 },
  entryIconWrap: {
    width: 36, height: 36, borderRadius: 12,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center', alignItems: 'center',
  },
  entryMeta:    { flex: 1 },
  entryDate:    { fontSize: 14, fontWeight: '600', color: COLORS.text },
  entryWordCount: { fontSize: 11, color: COLORS.text, opacity: 0.4, marginTop: 1 },
  sentimentBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10, marginRight: 4 },
  sentimentText:  { fontSize: 11, fontWeight: '600' },
  entryPreview: { fontSize: 14, color: COLORS.text, opacity: 0.55, lineHeight: 20 },
  entryFull:    { fontSize: 16, color: COLORS.text, lineHeight: 26, marginTop: 4 },
  separator:    { height: 12 },
  empty:        { flex: 1, alignItems: 'center', paddingTop: 80, gap: 10 },
  emptyText:    { fontSize: 18, fontWeight: '600', color: COLORS.text, opacity: 0.4 },
  emptySubtext: { fontSize: 14, color: COLORS.text, opacity: 0.3 },
  writeBtn:     { marginTop: 12, backgroundColor: COLORS.primary, paddingHorizontal: 24, paddingVertical: 12, borderRadius: 16 },
  writeBtnText: { color: 'white', fontWeight: '600', fontSize: 15 },
});