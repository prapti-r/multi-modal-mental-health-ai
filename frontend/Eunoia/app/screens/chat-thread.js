// app/screens/chat-thread.js
// Fix: Messages were displaying upside-down / in wrong order.
// Root cause: FlatList renders top-to-bottom but chat should show oldest at top,
// newest at bottom. The fix is to reverse the messages array so newest is at
// index 0, then use inverted={true} which flips the FlatList — newest appears
// at the bottom visually, oldest scrolls up. This is the standard chat pattern.

import React, { useEffect, useState, useRef } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  SafeAreaView, ActivityIndicator,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { ChevronLeft, AlertTriangle } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';
import { getMessages } from '../../src/api/chat';

export default function ChatThreadScreen() {
  const router = useRouter();
  const { sessionId, summary } = useLocalSearchParams();

  // Messages stored newest-first for inverted FlatList
  const [messages,    setMessages]    = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor,  setNextCursor]  = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await getMessages(sessionId, 40, null);
        const msgs = data.messages ?? [];
        // Reverse so newest is at index 0 (required for inverted FlatList)
        setMessages([...msgs].reverse());
        setNextCursor(data.next_cursor ?? null);
      } catch {
        // show empty state
      } finally {
        setLoading(false);
      }
    })();
  }, [sessionId]);

  // Load older messages — prepend to end of array (which is visual top in inverted list)
  const loadOlder = async () => {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    try {
      const { data } = await getMessages(sessionId, 40, nextCursor);
      const older = data.messages ?? [];
      // Older messages go to the END of the array (visual top in inverted FlatList)
      setMessages((prev) => [...prev, ...older.reverse()]);
      setNextCursor(data.next_cursor ?? null);
    } catch {}
    finally { setLoadingMore(false); }
  };

  const renderMessage = ({ item }) => {
    const isUser = item.sender_type === 'user';
    return (
      <View style={[styles.bubbleRow, isUser && styles.bubbleRowUser]}>
        {!isUser && <View style={styles.aiDot} />}
        <View style={[styles.bubble, isUser ? styles.bubbleUser : styles.bubbleAi]}>
          <Text style={[styles.bubbleText, isUser && styles.bubbleTextUser]}>
            {item.content}
          </Text>
          {item.input_mode && item.input_mode !== 'text' && (
            <Text style={styles.inputModeBadge}>
              {item.input_mode === 'voice' ? '🎤 Voice' : '🎥 Video'}
            </Text>
          )}
          {item.used_fallback && !isUser && (
            <View style={styles.fallbackBadge}>
              <AlertTriangle size={10} color={COLORS.accent} />
              <Text style={styles.fallbackText}>Template mode</Text>
            </View>
          )}
          <Text style={styles.timestamp}>
            {item.created_at
              ? new Date(item.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
              : ''}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <ChevronLeft color={COLORS.text} size={28} />
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>
          {summary || 'Conversation'}
        </Text>
        <View style={{ width: 40 }} />
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : (
        <FlatList
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessage}
          contentContainerStyle={styles.messageList}
          // ✅ FIX: inverted flips the list so newest messages appear at the bottom
          // Combined with reversing the array, this gives correct chat order
          inverted
          onEndReached={loadOlder}
          onEndReachedThreshold={0.3}
          ListFooterComponent={
            loadingMore
              ? <ActivityIndicator color={COLORS.primary} style={{ margin: 10 }} />
              : null
          }
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={styles.emptyText}>No messages in this session</Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container:     { flex: 1, backgroundColor: COLORS.background },
  center:        { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: COLORS.gray,
  },
  backBtn:       { padding: 4 },
  headerTitle:   { flex: 1, fontSize: 17, fontWeight: '600', color: COLORS.text, textAlign: 'center', marginHorizontal: 8 },
  messageList:   { padding: 16, paddingBottom: 20 },
  bubbleRow:     { flexDirection: 'row', alignItems: 'flex-end', marginBottom: 12 },
  bubbleRowUser: { flexDirection: 'row-reverse' },
  aiDot:         { width: 28, height: 28, borderRadius: 14, backgroundColor: COLORS.accent, marginRight: 8 },
  bubble:        { maxWidth: '75%', padding: 14, borderRadius: 20, backgroundColor: COLORS.card, elevation: 1 },
  bubbleUser:    { backgroundColor: COLORS.primary, borderBottomRightRadius: 4 },
  bubbleAi:      { borderBottomLeftRadius: 4 },
  bubbleText:    { fontSize: 15, color: COLORS.text, lineHeight: 21 },
  bubbleTextUser:{ color: 'white' },
  inputModeBadge:{ fontSize: 11, opacity: 0.6, marginTop: 4 },
  fallbackBadge: { flexDirection: 'row', alignItems: 'center', marginTop: 4, gap: 4 },
  fallbackText:  { fontSize: 10, color: COLORS.accent, opacity: 0.8 },
  timestamp:     { fontSize: 10, opacity: 0.35, marginTop: 4, textAlign: 'right' },
  empty:         { flex: 1, alignItems: 'center', paddingTop: 60 },
  emptyText:     { fontSize: 16, color: COLORS.text, opacity: 0.4 },
});