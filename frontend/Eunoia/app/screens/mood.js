import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, SafeAreaView, Dimensions } from 'react-native';
import { useRouter } from 'expo-router';
import { X, Check, Mic } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';

const { width } = Dimensions.get('window');

const MOODS = [
  { id: 'happy', label: 'Happy', color: '#FFD1DC', icon: 'ᐡ›ﻌ‹ᐡ' },
  { id: 'peaceful', label: 'Peaceful', color: '#B8E1DD', icon: 'ᐡᵕᐡ' },
  { id: 'normal', label: 'Normal', color: '#D3E5EF', icon: '• ᵕ •' }, // Soft Blue-Grey
  { id: 'anxiety', label: 'Anxiety', color: '#D2B7E5', icon: '•︠ ﻌ •︡' },
  { id: 'stress', label: 'Stress', color: '#FFC971', icon: '◎_◎' },
  { id: 'sad', label: 'Sad', color: '#A9C9FF', icon: '╥﹏╥' },
  { id: 'tired', label: 'Tired', color: '#C8D6AF', icon: 'ᵕ_ᵕ' }, // Muted Olive
  { id: 'angry', label: 'Angry', color: '#F8B1B1', icon: 'ᐡ`^´ᐡ' },
];

export default function MoodScreen() {
  const router = useRouter();
  const [selectedIndex, setSelectedIndex] = useState(2);
  const [note, setNote] = useState('');

  const currentMood = MOODS[selectedIndex];

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentMood.color + '10' }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <X color={COLORS.text} size={28} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Mood Check</Text>
        <View style={{ width: 28 }} />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        <Text style={styles.question}>How Do You Feel{"\n"}Today?</Text>

        {/* Dynamic Visual Centerpiece */}
        <View style={styles.visualContainer}>
          <View style={[styles.outerCircle, { backgroundColor: currentMood.color + '40' }]}>
            <View style={[styles.innerCircle, { backgroundColor: currentMood.color }]}>
              <Text style={styles.bigIcon}>{currentMood.icon}</Text>
            </View>
          </View>
          <Text style={styles.moodLabel}>{currentMood.label}</Text>
        </View>

        {/* Circular Mood Grid */}
        <View style={styles.grid}>
          {MOODS.map((mood, index) => (
            <View key={mood.id} style={styles.moodItemWrapper}>
              <TouchableOpacity
                onPress={() => setSelectedIndex(index)}
                style={[
                  styles.moodCircle,
                  { backgroundColor: mood.color + '30' },
                  selectedIndex === index && { borderWidth: 3, borderColor: mood.color, backgroundColor: mood.color }
                ]}
              >
                <Text style={[styles.blobIcon, selectedIndex === index && { color: '#FFF' }]}>
                  {mood.icon}
                </Text>
              </TouchableOpacity>
              <Text style={styles.blobLabel}>{mood.label}</Text>
            </View>
          ))}
        </View>

        {/* Note Section with Voice Option */}
        <View style={styles.noteWrapper}>
          <View style={styles.noteHeader}>
            <Text style={styles.noteLabel}>Add a note</Text>
            <TouchableOpacity style={styles.voiceButton}>
              <Mic color={COLORS.primary} size={20} />
            </TouchableOpacity>
          </View>
          <TextInput
            style={styles.input}
            placeholder="What's making you feel this way?"
            placeholderTextColor="#999"
            multiline
            value={note}
            onChangeText={setNote}
          />
        </View>

        {/* Steady Sage Green Button */}
        <TouchableOpacity
          style={styles.submitButton}
          onPress={() => router.back()}
        >
          <Text style={styles.submitText}>Save Reflection</Text>
          <Check color="white" size={20} />
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 20 },
  headerTitle: { fontSize: 18, fontWeight: '600', color: COLORS.text },
  content: { paddingHorizontal: 25, alignItems: 'center', paddingBottom: 40 },
  question: { fontSize: 28, fontWeight: 'bold', color: COLORS.text, textAlign: 'center', marginTop: 10 },

  visualContainer: { marginVertical: 30, alignItems: 'center' },
  outerCircle: { width: 160, height: 160, borderRadius: 80, justifyContent: 'center', alignItems: 'center' },
  innerCircle: { width: 110, height: 110, borderRadius: 55, justifyContent: 'center', alignItems: 'center', elevation: 4 },
  bigIcon: { fontSize: 28, fontWeight: 'bold', color: 'white' },
  moodLabel: { fontSize: 22, fontWeight: 'bold', marginTop: 15, color: COLORS.text },

  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', width: '100%', marginBottom: 20 },
  moodItemWrapper: { width: '23%', alignItems: 'center', marginBottom: 20 },
  moodCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8
  },
  blobIcon: { fontSize: 14, color: COLORS.text },
  blobLabel: { fontSize: 11, color: COLORS.text, fontWeight: '600', opacity: 0.7 },

  noteWrapper: { width: '100%', marginBottom: 25 },
  noteHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  noteLabel: { fontSize: 14, fontWeight: 'bold', color: COLORS.text, opacity: 0.6 },
  voiceButton: { padding: 5 },
  input: { backgroundColor: 'white', borderRadius: 20, padding: 15, height: 80, textAlignVertical: 'top', elevation: 1 },

  submitButton: {
    backgroundColor: COLORS.primary, // Fixed to Sage Green
    flexDirection: 'row',
    width: '100%',
    padding: 20,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 3
  },
  submitText: { color: 'white', fontSize: 18, fontWeight: 'bold', marginRight: 10 }
});