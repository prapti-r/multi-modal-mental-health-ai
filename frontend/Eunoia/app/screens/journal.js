import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, SafeAreaView, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft, Save } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';

export default function JournalScreen() {
  const router = useRouter();
  const [entry, setEntry] = useState('');
  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric'
  });

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <ChevronLeft color={COLORS.text} size={28} />
          </TouchableOpacity>
          <View>
            <Text style={styles.dateText}>{today}</Text>
            <Text style={styles.titleText}>Daily Reflection</Text>
          </View>
          <TouchableOpacity
            style={[styles.saveButton, { opacity: entry ? 1 : 0.5 }]}
            onPress={() => router.back()}
            disabled={!entry}
          >
            <Save color="white" size={20} />
          </TouchableOpacity>
        </View>

        {/* Paper Area */}
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

        {/* Aesthetic footer detail */}
        <View style={styles.footer}>
           <Text style={styles.wordCount}>{entry.split(/\s+/).filter(w => w).length} words</Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
    backgroundColor: COLORS.background
  },
  backButton: { padding: 5 },
  dateText: { fontSize: 14, color: COLORS.text, opacity: 0.5, textAlign: 'center' },
  titleText: { fontSize: 20, fontWeight: 'bold', color: COLORS.text, textAlign: 'center' },
  saveButton: {
    backgroundColor: COLORS.primary,
    padding: 10,
    borderRadius: 12,
    elevation: 2
  },
  journalArea: {
    flex: 1,
    marginHorizontal: 20,
    marginTop: 10,
    backgroundColor: COLORS.card,
    borderRadius: 30,
    padding: 25,
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 10,
  },
  input: {
    fontSize: 18,
    color: COLORS.text,
    lineHeight: 28,
    textAlignVertical: 'top',
    height: '100%',
  },
  footer: {
    padding: 20,
    alignItems: 'center'
  },
  wordCount: {
    fontSize: 14,
    color: COLORS.text,
    opacity: 0.4,
    fontStyle: 'italic'
  }
});