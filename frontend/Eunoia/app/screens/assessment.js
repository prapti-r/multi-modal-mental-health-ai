import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, SafeAreaView, Dimensions } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft, Info } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';

const { width } = Dimensions.get('window');

// Sample PHQ-9 Questions
const QUESTIONS = [
  "Little interest or pleasure in doing things",
  "Feeling down, depressed, or hopeless",
  "Trouble falling or staying asleep, or sleeping too much",
  "Feeling tired or having little energy",
  "Poor appetite or overeating"
];

const OPTIONS = [
  { label: "Not at all", score: 0 },
  { label: "Several days", score: 1 },
  { label: "More than half the days", score: 2 },
  { label: "Nearly every day", score: 3 }
];

export default function AssessmentScreen() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState({});

  const handleSelect = (score) => {
    setAnswers({ ...answers, [currentStep]: score });
    if (currentStep < QUESTIONS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const progress = ((currentStep + 1) / QUESTIONS.length) * 100;

  return (
    <SafeAreaView style={styles.container}>
      {/* Header with Progress Bar */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <ChevronLeft color={COLORS.text} size={28} />
        </TouchableOpacity>
        <View style={styles.progressWrapper}>
          <View style={[styles.progressBar, { width: `${progress}%` }]} />
        </View>
        <TouchableOpacity>
          <Info color={COLORS.text} size={22} opacity={0.5} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.typeTag}>PHQ-9 Assessment</Text>

        {/* Question Card */}
        <View style={styles.questionCard}>
          <Text style={styles.stepIndicator}>Question {currentStep + 1} of {QUESTIONS.length}</Text>
          <Text style={styles.questionText}>{QUESTIONS[currentStep]}</Text>
        </View>

        <Text style={styles.instructionText}>Over the last 2 weeks, how often have you been bothered by this?</Text>

        {/* Options List */}
        <View style={styles.optionsContainer}>
          {OPTIONS.map((option, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.optionButton,
                answers[currentStep] === option.score && styles.selectedOption
              ]}
              onPress={() => handleSelect(option.score)}
            >
              <Text style={[
                styles.optionText,
                answers[currentStep] === option.score && styles.selectedOptionText
              ]}>
                {option.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Navigation Buttons */}
        <View style={styles.navRow}>
          {currentStep > 0 && (
            <TouchableOpacity
              style={styles.backLink}
              onPress={() => setCurrentStep(currentStep - 1)}
            >
              <Text style={styles.backLinkText}>Previous Question</Text>
            </TouchableOpacity>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20
  },
  progressWrapper: {
    height: 8,
    backgroundColor: COLORS.gray,
    borderRadius: 4,
    width: width * 0.6,
    overflow: 'hidden'
  },
  progressBar: {
    height: '100%',
    backgroundColor: COLORS.primary,
  },
  content: { padding: 25 },
  typeTag: {
    backgroundColor: COLORS.secondary + '20',
    color: COLORS.secondary,
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 10,
    fontWeight: 'bold',
    fontSize: 12,
    marginBottom: 20
  },
  questionCard: {
    backgroundColor: COLORS.card,
    borderRadius: 30,
    padding: 30,
    elevation: 3,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 15,
    marginBottom: 30
  },
  stepIndicator: { fontSize: 14, color: COLORS.text, opacity: 0.5, marginBottom: 10 },
  questionText: { fontSize: 22, fontWeight: 'bold', color: COLORS.text, lineHeight: 30 },
  instructionText: { fontSize: 15, color: COLORS.text, opacity: 0.6, textAlign: 'center', marginBottom: 25 },
  optionsContainer: { gap: 12 },
  optionButton: {
    backgroundColor: COLORS.card,
    padding: 20,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: COLORS.gray,
    alignItems: 'center'
  },
  selectedOption: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  optionText: { fontSize: 16, color: COLORS.text, fontWeight: '500' },
  selectedOptionText: { color: COLORS.primary, fontWeight: 'bold' },
  navRow: { marginTop: 30, alignItems: 'center' },
  backLinkText: { color: COLORS.text, opacity: 0.5, textDecorationLine: 'underline' }
});