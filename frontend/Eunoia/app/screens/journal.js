// app/screens/journal.js
// Changes from original:
//   • Save button calls POST /journal/entry
//   • Shows returned sentiment_label as a subtle badge after save
//   • Loading + error states

import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  SafeAreaView, KeyboardAvoidingView, Platform, ActivityIndicator, Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft, Save , History} from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';
import { createJournal } from '../../src/api/tracking';

export default function JournalScreen() {
  const router  = useRouter();
  const [entry,   setEntry]   = useState('');
  const [loading, setLoading] = useState(false);
  const [sentiment, setSentiment] = useState(null);   // shown after save

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  });

  const handleSave = async () => {
    if (!entry.trim()) return;
    setLoading(true);
    try {
      const { data } = await createJournal({ content: entry });
      setSentiment(data.sentiment_label);   // e.g. "neutral", "positive", "sadness"
      // Brief pause so user sees the sentiment badge, then go back
      setTimeout(() => router.back(), 1200);
    } catch (err) {
      Alert.alert('Error', 'Could not save your entry. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <ChevronLeft color={COLORS.text} size={28} />
          </TouchableOpacity>
          <View>
            <Text style={styles.dateText}>{today}</Text>
            <Text style={styles.titleText}>Daily Reflection</Text>
          </View>
          <TouchableOpacity
            style={[styles.saveButton, { opacity: entry && !loading ? 1 : 0.5 }]}
            onPress={handleSave}
            disabled={!entry || loading}
          >
            {loading
              ? <ActivityIndicator color="white" size="small" />
              : <Save color="white" size={20} />}
          </TouchableOpacity>
          <TouchableOpacity
          style={styles.historyBtn}
          onPress={() => router.push('/screens/journal-history')}
        >
          <History color={COLORS.text} size={22} />
        </TouchableOpacity>
        </View>

        {/* Sentiment badge — appears after save */}
        {sentiment && (
          <View style={styles.sentimentBadge}>
            <Text style={styles.sentimentText}>
              Mood detected: <Text style={{ fontWeight: 'bold' }}>{sentiment}</Text>
            </Text>
          </View>
        )}

        <View style={styles.journalArea}>
          <TextInput
            style={styles.input}
            placeholder="Write your thoughts here..."
            placeholderTextColor="#AAA"
            multiline
            autoFocus
            value={entry}
            onChangeText={setEntry}
            selectionColor={COLORS.primary}
          />
        </View>

        <View style={styles.footer}>
          <Text style={styles.wordCount}>
            {entry.split(/\s+/).filter((w) => w).length} words
          </Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container:  { flex: 1, backgroundColor: COLORS.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    padding: 20, backgroundColor: COLORS.background,
  },
  backButton:   { padding: 5 },
  dateText:     { fontSize: 14, color: COLORS.text, opacity: 0.5, textAlign: 'center' },
  titleText:    { fontSize: 20, fontWeight: 'bold', color: COLORS.text, textAlign: 'center' },
  saveButton:   { backgroundColor: COLORS.primary, padding: 10, borderRadius: 12, elevation: 2 },
  sentimentBadge: {
    marginHorizontal: 20, marginBottom: 8,
    backgroundColor: COLORS.primary + '15', borderRadius: 12,
    paddingHorizontal: 14, paddingVertical: 6, alignSelf: 'flex-start',
  },
  sentimentText:{ fontSize: 13, color: COLORS.primary },
  journalArea: {
    flex: 1, marginHorizontal: 20, marginTop: 10,
    backgroundColor: COLORS.card, borderRadius: 30, padding: 25,
    elevation: 2, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 10,
  },
  input:  { fontSize: 18, color: COLORS.text, lineHeight: 28, textAlignVertical: 'top', height: '100%' },
  footer: { padding: 20, alignItems: 'center' },
  wordCount: { fontSize: 14, color: COLORS.text, opacity: 0.4, fontStyle: 'italic' },
});