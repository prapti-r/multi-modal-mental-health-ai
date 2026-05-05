// app/screens/chat-history.js
// Lists all past chat sessions (paginated).
// Tap a session → view its full message thread.

import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  SafeAreaView, ActivityIndicator, Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft, MessageCircle, ChevronRight, Inbox } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';
import { listSessions, getMessages } from '../../src/api/chat';

// ─── Session list screen ───────────────────────────────────────────────────────
export default function ChatHistoryScreen() {
  const router = useRouter();

  const [sessions,    setSessions]    = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page,        setPage]        = useState(1);
  const [hasMore,     setHasMore]     = useState(true);
  const [total,       setTotal]       = useState(0);

  const fetchSessions = useCallback(async (pageNum = 1, append = false) => {
    if (pageNum === 1) setLoading(true); else setLoadingMore(true);
    try {
      const { data } = await listSessions(pageNum, 20);
      const newSessions = data.sessions ?? [];
      setSessions((prev) => append ? [...prev, ...newSessions] : newSessions);
      setTotal(data.total ?? 0);
      setHasMore(newSessions.length === 20);
    } catch {
      Alert.alert('Error', 'Could not load chat history.');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => { fetchSessions(1); }, []);

  const loadMore = () => {
    if (!hasMore || loadingMore) return;
    const nextPage = page + 1;
    setPage(nextPage);
    fetchSessions(nextPage, true);
  };

  const formatDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    const now = new Date();
    const diffDays = Math.floor((now - d) / 86400000);
    if (diffDays === 0) return 'Today · ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    if (diffDays === 1) return 'Yesterday · ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const renderSession = ({ item }) => (
    <TouchableOpacity
      style={styles.sessionCard}
      onPress={() => router.push({ pathname: '/screens/chat-thread', params: { sessionId: item.id, summary: item.session_summary } })}
    >
      <View style={styles.sessionIcon}>
        <MessageCircle color={COLORS.secondary} size={22} />
      </View>
      <View style={styles.sessionBody}>
        <Text style={styles.sessionSummary} numberOfLines={1}>
          {item.session_summary || 'Conversation'}
        </Text>
        <Text style={styles.sessionDate}>{formatDate(item.started_at)}</Text>
      </View>
      <ChevronRight color={COLORS.text} size={18} opacity={0.3} />
    </TouchableOpacity>
  );

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
        data={sessions}
        keyExtractor={(item) => item.id}
        renderItem={renderSession}
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
            <Inbox color={COLORS.text} size={48} opacity={0.2} />
            <Text style={styles.emptyText}>No chat sessions yet</Text>
            <Text style={styles.emptySubtext}>Start a conversation from the AI Chat tab</Text>
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
        <Text style={styles.headerTitle}>Chat History</Text>
        {count != null && <Text style={styles.headerSubtitle}>{count} session{count !== 1 ? 's' : ''}</Text>}
      </View>
      <View style={{ width: 40 }} />
    </View>
  );
}

const styles = StyleSheet.create({
  container:       { flex: 1, backgroundColor: COLORS.background },
  center:          { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
  },
  backBtn:         { padding: 4 },
  headerTitle:     { fontSize: 22, fontWeight: 'bold', color: COLORS.text, textAlign: 'center' },
  headerSubtitle:  { fontSize: 13, color: COLORS.text, opacity: 0.45, textAlign: 'center' },
  list:            { paddingHorizontal: 20, paddingBottom: 40, paddingTop: 8 },
  sessionCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: COLORS.card, borderRadius: 18,
    padding: 16, gap: 14,
  },
  sessionIcon: {
    width: 44, height: 44, borderRadius: 14,
    backgroundColor: COLORS.secondary + '15',
    justifyContent: 'center', alignItems: 'center',
  },
  sessionBody:    { flex: 1 },
  sessionSummary: { fontSize: 15, fontWeight: '600', color: COLORS.text, marginBottom: 3 },
  sessionDate:    { fontSize: 12, color: COLORS.text, opacity: 0.45 },
  separator:      { height: 10 },
  empty:          { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 80, gap: 10 },
  emptyText:      { fontSize: 18, fontWeight: '600', color: COLORS.text, opacity: 0.4 },
  emptySubtext:   { fontSize: 14, color: COLORS.text, opacity: 0.3 },
});