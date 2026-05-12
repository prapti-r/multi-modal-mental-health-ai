import React, { useCallback, useRef, useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  FlatList, KeyboardAvoidingView, Platform, ActivityIndicator,
  Alert, SafeAreaView,
} from 'react-native';
import { Audio } from 'expo-av';
import * as ImagePicker from 'expo-image-picker';
import { Mic, Video, Send, History, AlertTriangle } from 'lucide-react-native';
import { useRouter } from 'expo-router';

import { COLORS } from '../../src/constants/Theme';
import { createSession, sendTextMessage, sendMediaMessage, getMessages } from '../../src/api/chat';
import { useCrisisGuard } from '../../src/hooks/useCrisisGuard';

export default function ChatbotScreen() {
  const router = useRouter();
  const { guard } = useCrisisGuard();

  // Refs
  const sessionIdRef = useRef(null);
  const sessionPromiseRef = useRef(null);
  const flatRef = useRef(null);
  const recordingRef = useRef(null);

  // States
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor, setNextCursor] = useState(null);
  const [isRecording, setIsRecording] = useState(false);

  // --- Session Management ---
  const ensureSession = useCallback(async () => {
    if (sessionIdRef.current) return sessionIdRef.current;
    if (sessionPromiseRef.current) return sessionPromiseRef.current;
    sessionPromiseRef.current = createSession().then(({ data }) => {
      sessionIdRef.current = data.id;
      sessionPromiseRef.current = null;
      return data.id;
    });
    return sessionPromiseRef.current;
  }, []);

  const appendPair = (pair) => {
    setMessages((prev) => [
      ...prev,
      { ...pair.user_message, used_fallback: pair.used_fallback },
      { ...pair.ai_message, used_fallback: pair.used_fallback },
    ]);
    setTimeout(() => flatRef.current?.scrollToEnd({ animated: true }), 100);
  };

  // --- Permissions ---
  const requestAudioPermission = async () => {
    const { status } = await Audio.requestPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Please allow microphone access to record audio.');
      return false;
    }
    return true;
  };

  const requestVideoPermission = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Please allow camera access to record video.');
      return false;
    }
    return true;
  };

  // --- Message Handlers ---
  const handleSendText = async () => {
    const text = message.trim();
    if (!text || sending) return;
    setMessage('');
    setSending(true);
    try {
      const sid = await ensureSession();
      const { data } = await sendTextMessage(sid, text);
      appendPair(data);
      guard(data);
    } catch {
      Alert.alert('Error', 'Failed to send message.');
      setMessage(text);
    } finally {
      setSending(false);
    }
  };

  //audio
  const startRecording = async () => {
    const hasPermission = await requestAudioPermission();
    if (!hasPermission) return;

    if (recordingRef.current) {
    try {
      await recordingRef.current.stopAndUnloadAsync();
      recordingRef.current = null;
    } catch (e) {
      // already unloaded
    }
  }

    try {
      setIsRecording(true);
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      recordingRef.current = recording;
    } catch (err) {
      console.error("Failed to start recording", err);
      setIsRecording(false);
      recordingRef.current = null;
    }
  };

  const stopAndSendAudio = async () => {

    if (!recordingRef.current) {
      setIsRecording(false);
      return;
    }

    try {
      setIsRecording(false);
      setSending(true);
      
      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI();
      
      const type = Platform.OS === 'ios' ? 'audio/x-m4a' : 'audio/3gp';

      const sid = await ensureSession();
      const { data } = await sendMediaMessage(sid, uri, type);
      appendPair(data);
      guard(data);
    } catch (err) {
      console.error("Audio upload error:", err);
      Alert.alert("Error", "Could not process audio.");
    } finally {
      setSending(false);
      recordingRef.current = null;
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
      });
    }
  };

  // Video 
  const handleVideoPress = async () => {
    await ImagePicker.requestCameraPermissionsAsync();
    await Audio.requestPermissionsAsync();
    const hasPermission = await requestVideoPermission();
    if (!hasPermission) return;

    try {
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Videos,
        videoMaxDuration: 10,
        quality: 0.1,
      });

      if (result.canceled) return;

      const asset = result.assets[0];
      console.log("VIDEO ASSET:", asset);

      setSending(true);

      const sid = await ensureSession();

      const mimeType =
      asset.mimeType ||
      (asset.uri.endsWith('.mov')
        ? 'video/quicktime'
        : 'video/mp4');

      const { data } = await sendMediaMessage(sid, asset.uri, mimeType);
      appendPair(data);
      guard(data);
    } catch (err) {
      Alert.alert('Error', 'Media upload failed.');
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
          keyExtractor={(item, index) => item.id || index.toString()}
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
            {/* Press and Hold Mic */}
            <TouchableOpacity 
              style={[styles.iconButton, isRecording && styles.activeMic]} 
              onPressIn={startRecording}
              onPressOut={stopAndSendAudio}
              disabled={sending}
            >
              <Mic color={isRecording ? 'white' : COLORS.secondary} size={24} />
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.iconButton} 
              onPress={handleVideoPress} 
              disabled={sending || isRecording}
            >
              <Video color={COLORS.secondary} size={24} />
            </TouchableOpacity>

            {isRecording && (
              <Text style={styles.recordingStatus}>Recording... Release to send</Text>
            )}
          </View>

          <View style={styles.textInputRow}>
            <TextInput
              style={styles.input}
              placeholder={isRecording ? "Listening..." : "Write down instead..."}
              placeholderTextColor="#999"
              value={message}
              onChangeText={setMessage}
              multiline
              editable={!sending && !isRecording}
            />
            <TouchableOpacity
              style={[styles.sendButton, { opacity: (message && !sending) ? 1 : 0.4 }]}
              onPress={handleSendText}
              disabled={!message || sending || isRecording}
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
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingTop: 10, paddingBottom: 6 },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: COLORS.text },
  historyBtn: { padding: 8 },
  messageList: { padding: 15, paddingBottom: 10, flexGrow: 1 },
  bubbleRow: { flexDirection: 'row', alignItems: 'flex-end', marginBottom: 12 },
  bubbleRowUser: { flexDirection: 'row-reverse' },
  aiDot: { width: 28, height: 28, borderRadius: 14, backgroundColor: COLORS.accent, marginRight: 8 },
  bubble: { maxWidth: '75%', padding: 14, borderRadius: 20, backgroundColor: COLORS.card, elevation: 1 },
  bubbleUser: { backgroundColor: COLORS.primary, borderBottomRightRadius: 4 },
  bubbleAi: { borderBottomLeftRadius: 4 },
  bubbleText: { fontSize: 16, color: COLORS.text, lineHeight: 22 },
  bubbleTextUser: { color: 'white' },
  fallbackBadge: { flexDirection: 'row', alignItems: 'center', marginTop: 6, gap: 4 },
  fallbackText: { fontSize: 10, color: COLORS.accent, opacity: 0.8 },
  emptyState: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 80 },
  orbShadow: { width: 180, height: 180, borderRadius: 90, backgroundColor: COLORS.accent + '30', justifyContent: 'center', alignItems: 'center', marginBottom: 30 },
  aiOrb: { width: 140, height: 140, borderRadius: 70, backgroundColor: COLORS.accent },
  aiTitle: { fontSize: 24, fontWeight: 'bold', color: COLORS.text, textAlign: 'center' },
  aiSubtext: { fontSize: 16, color: COLORS.text, opacity: 0.6, marginTop: 10 },
  inputWrapper: { padding: 20, backgroundColor: COLORS.card, borderTopLeftRadius: 30, borderTopRightRadius: 30, elevation: 10 },
  actionRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 15 },
  iconButton: { padding: 12, backgroundColor: COLORS.background, borderRadius: 15 },
  activeMic: { backgroundColor: COLORS.accent, transform: [{ scale: 1.1 }] },
  recordingStatus: { color: COLORS.accent, fontWeight: 'bold', fontSize: 14, marginLeft: 5 },
  textInputRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.background, borderRadius: 20, paddingHorizontal: 15, paddingVertical: Platform.OS === 'ios' ? 12 : 5 },
  input: { flex: 1, color: COLORS.text, fontSize: 16, maxHeight: 100 },
  sendButton: { backgroundColor: COLORS.primary, padding: 10, borderRadius: 12, marginLeft: 10 },
});