import React, { useCallback, useRef, useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  FlatList, KeyboardAvoidingView, Platform, ActivityIndicator,
  Alert, SafeAreaView,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Mic, Video, Send, History, AlertTriangle } from 'lucide-react-native';
import { useRouter } from 'expo-router';
import { COLORS } from '../../src/constants/Theme';
import { createSession, sendTextMessage, sendMediaMessage, getMessages } from '../../src/api/chat';
import { useCrisisGuard } from '../../src/hooks/useCrisisGuard';

export default function ChatbotScreen() {
  const router    = useRouter();
  const { guard } = useCrisisGuard();

  const sessionIdRef      = useRef(null);
  const sessionPromiseRef = useRef(null);

  const [messages,    setMessages]    = useState([]);
  const [message,     setMessage]     = useState('');
  const [sending,     setSending]     = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor,  setNextCursor]  = useState(null);
  const flatRef = useRef(null);

  const ensureSession = useCallback(async () => {
    if (sessionIdRef.current) return sessionIdRef.current;
    if (sessionPromiseRef.current) return sessionPromiseRef.current;
    sessionPromiseRef.current = createSession().then(({ data }) => {
      sessionIdRef.current      = data.id;
      sessionPromiseRef.current = null;
      return data.id;
    });
    return sessionPromiseRef.current;
  }, []);

  const appendPair = (pair) => {
    setMessages((prev) => [
      ...prev,
      { ...pair.user_message, used_fallback: pair.used_fallback },
      { ...pair.ai_message,   used_fallback: pair.used_fallback },
    ]);
    setTimeout(() => flatRef.current?.scrollToEnd({ animated: true }), 100);
  };

  const handleSend = async () => {
    const text = message.trim();
    if (!text || sending) return;
    setMessage('');
    setSending(true);
    try {
      const sid      = await ensureSession();
      const { data } = await sendTextMessage(sid, text);
      appendPair(data);
      guard(data);
    } catch {
      Alert.alert('Error', 'Failed to send message. Please try again.');
      setMessage(text);
    } finally {
      setSending(false);
    }
  };

  // FIX: Only request camera permission — it covers audio recording too.
  // requestMicrophonePermissionsAsync does not exist on this Expo version.
  const requestPermissions = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Please enable Camera access in your device settings.');
      return false;
    }
    return true;
  };

  const handleMedia = async (type) => {
    const ok = await requestPermissions();
    if (!ok) return;

    if (type === 'audio') {
      Alert.alert(
        'Voice Check-in',
        'Record a short video with your voice (up to 60 seconds).',
        [
          { text: 'Record', onPress: launchCamera },
          { text: 'Cancel', style: 'cancel' },
        ]
      );
    } else {
      launchCamera();
    }
  };

  const launchCamera = async () => {
    try {
      // ✅ FIX: MediaTypeOptions.Videos — correct API for this Expo version
      // Do NOT use ImagePicker.MediaType.Videos (that's SDK 52+ only)
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Videos,
        videoMaxDuration: 60,
        quality: 0.5,
      });

      if (result.canceled) return;

      const asset = result.assets[0];
      setSending(true);
      const sid      = await ensureSession();
      const { data } = await sendMediaMessage(sid, asset.uri, 'video/mp4');
      appendPair(data);
      guard(data);
    } catch (err) {
      console.error('Media error:', err);
      Alert.alert('Error', 'Media upload failed. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const loadOlder = async () => {
    if (!sessionIdRef.current || !nextCursor || loadingMore) return;
    setLoadingMore(true);
    try {
      const { data } = await getMessages(sessionIdRef.current, 20, nextCursor);
      setMessages((prev) => [...(data.messages ?? []), ...prev]);
      setNextCursor(data.next_cursor ?? null);
    } catch { /* silent */ }
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
          {item.used_fallback && !isUser && (
            <View style={styles.fallbackBadge}>
              <AlertTriangle size={10} color={COLORS.accent} />
              <Text style={styles.fallbackText}>Template mode</Text>
            </View>
          )}
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>AI Chat</Text>
        <TouchableOpacity style={styles.historyBtn} onPress={() => router.push('/screens/chat-history')}>
          <History color={COLORS.text} size={22} />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
        keyboardVerticalOffset={90}
      >
        <FlatList
          ref={flatRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessage}
          contentContainerStyle={styles.messageList}
          onScrollBeginDrag={({ nativeEvent }) => {
            if (nativeEvent.contentOffset.y < 20) loadOlder();
          }}
          ListHeaderComponent={loadingMore ? <ActivityIndicator color={COLORS.primary} style={{ margin: 10 }} /> : null}
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <View style={styles.orbShadow}><View style={styles.aiOrb} /></View>
              <Text style={styles.aiTitle}>Speak your thoughts</Text>
              <Text style={styles.aiSubtext}>I'm listening and here to help.</Text>
            </View>
          }
        />

        <View style={styles.inputWrapper}>
          <View style={styles.actionRow}>
            <TouchableOpacity style={styles.iconButton} onPress={() => handleMedia('audio')} disabled={sending}>
              <Mic color={COLORS.secondary} size={24} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.iconButton} onPress={() => handleMedia('video')} disabled={sending}>
              <Video color={COLORS.secondary} size={24} />
            </TouchableOpacity>
          </View>
          <View style={styles.textInputRow}>
            <TextInput
              style={styles.input}
              placeholder="Write down instead..."
              placeholderTextColor="#999"
              value={message}
              onChangeText={setMessage}
              multiline
              editable={!sending}
            />
            <TouchableOpacity
              style={[styles.sendButton, { opacity: (message && !sending) ? 1 : 0.4 }]}
              onPress={handleSend}
              disabled={!message || sending}
            >
              {sending ? <ActivityIndicator color="white" size="small" /> : <Send color="white" size={20} />}
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container:     { flex: 1, backgroundColor: COLORS.background },
  header:        { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingTop: 10, paddingBottom: 6 },
  headerTitle:   { fontSize: 20, fontWeight: 'bold', color: COLORS.text },
  historyBtn:    { padding: 8 },
  messageList:   { padding: 15, paddingBottom: 10, flexGrow: 1 },
  bubbleRow:     { flexDirection: 'row', alignItems: 'flex-end', marginBottom: 12 },
  bubbleRowUser: { flexDirection: 'row-reverse' },
  aiDot:         { width: 28, height: 28, borderRadius: 14, backgroundColor: COLORS.accent, marginRight: 8 },
  bubble:        { maxWidth: '75%', padding: 14, borderRadius: 20, backgroundColor: COLORS.card, elevation: 1 },
  bubbleUser:    { backgroundColor: COLORS.primary, borderBottomRightRadius: 4 },
  bubbleAi:      { borderBottomLeftRadius: 4 },
  bubbleText:    { fontSize: 16, color: COLORS.text, lineHeight: 22 },
  bubbleTextUser:{ color: 'white' },
  fallbackBadge: { flexDirection: 'row', alignItems: 'center', marginTop: 6, gap: 4 },
  fallbackText:  { fontSize: 10, color: COLORS.accent, opacity: 0.8 },
  emptyState:    { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 80 },
  orbShadow:     { width: 180, height: 180, borderRadius: 90, backgroundColor: COLORS.accent + '30', justifyContent: 'center', alignItems: 'center', marginBottom: 30 },
  aiOrb:         { width: 140, height: 140, borderRadius: 70, backgroundColor: COLORS.accent },
  aiTitle:       { fontSize: 24, fontWeight: 'bold', color: COLORS.text, textAlign: 'center' },
  aiSubtext:     { fontSize: 16, color: COLORS.text, opacity: 0.6, marginTop: 10 },
  inputWrapper:  { padding: 20, backgroundColor: COLORS.card, borderTopLeftRadius: 30, borderTopRightRadius: 30, elevation: 10 },
  actionRow:     { flexDirection: 'row', gap: 12, marginBottom: 15 },
  iconButton:    { padding: 12, backgroundColor: COLORS.background, borderRadius: 15 },
  textInputRow:  { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.background, borderRadius: 20, paddingHorizontal: 15, paddingVertical: Platform.OS === 'ios' ? 12 : 5 },
  input:         { flex: 1, color: COLORS.text, fontSize: 16, maxHeight: 100 },
  sendButton:    { backgroundColor: COLORS.primary, padding: 10, borderRadius: 12, marginLeft: 10 },
});