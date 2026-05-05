// app/screens/assessment.js
// Full PHQ-9 (9 questions) and GAD-7 (7 questions) assessment screen.
// Features:
//   • Test selector — choose PHQ-9 or GAD-7 before starting
//   • Progress bar showing question X of N
//   • Auto-advances on answer selection
//   • Calculates total score + severity label on completion
//   • Calls POST /assessments/submit with the result
//   • Shows results card with severity colour and follow-up action
//   • Hard-triggers crisis screen if score is in "Severe" range

import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, SafeAreaView,
  ScrollView, ActivityIndicator, Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft, Info, CheckCircle } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';
import { submitAssessment } from '../../src/api/tracking';

// ─── Question banks ────────────────────────────────────────────────────────────

const OPTIONS = [
  { label: 'Not at all',            score: 0 },
  { label: 'Several days',          score: 1 },
  { label: 'More than half the days', score: 2 },
  { label: 'Nearly every day',      score: 3 },
];

const PHQ9_QUESTIONS = [
  'Little interest or pleasure in doing things',
  'Feeling down, depressed, or hopeless',
  'Trouble falling or staying asleep, or sleeping too much',
  'Feeling tired or having little energy',
  'Poor appetite or overeating',
  'Feeling bad about yourself — or that you are a failure or have let yourself or your family down',
  'Trouble concentrating on things, such as reading the newspaper or watching television',
  'Moving or speaking so slowly that other people could have noticed — or the opposite, being so fidgety or restless that you have been moving around a lot more than usual',
  'Thoughts that you would be better off dead, or of hurting yourself in some way',
];

const GAD7_QUESTIONS = [
  'Feeling nervous, anxious, or on edge',
  'Not being able to stop or control worrying',
  'Worrying too much about different things',
  'Trouble relaxing',
  'Being so restless that it is hard to sit still',
  'Becoming easily annoyed or irritable',
  'Feeling afraid, as if something awful might happen',
];

// ─── Scoring ──────────────────────────────────────────────────────────────────

function getSeverity(testType, score) {
  if (testType === 'PHQ-9') {
    if (score <= 4)  return { label: 'Minimal',  color: COLORS.primary,   action: null };
    if (score <= 9)  return { label: 'Mild',      color: '#8BC34A',        action: 'Consider self-care strategies and monitor your mood.' };
    if (score <= 14) return { label: 'Moderate',  color: '#FFC107',        action: 'Speaking with a counsellor or therapist may help.' };
    if (score <= 19) return { label: 'Moderately Severe', color: '#FF9800', action: 'We strongly recommend speaking with a mental health professional.' };
    return           { label: 'Severe',    color: COLORS.crisis,   action: 'Please reach out to a professional or crisis line right away.' };
  } else {
    // GAD-7
    if (score <= 4)  return { label: 'Minimal',  color: COLORS.primary,   action: null };
    if (score <= 9)  return { label: 'Mild',      color: '#8BC34A',        action: 'Relaxation techniques and self-care may help manage your anxiety.' };
    if (score <= 14) return { label: 'Moderate',  color: '#FFC107',        action: 'Consider talking to a counsellor about your anxiety.' };
    return           { label: 'Severe',    color: COLORS.crisis,   action: 'Please reach out to a mental health professional or crisis line right away.' };
  }
}

// ─── Screens ──────────────────────────────────────────────────────────────────

const SCREEN = {
  SELECT:   'SELECT',
  QUIZ:     'QUIZ',
  RESULT:   'RESULT',
};

export default function AssessmentScreen() {
  const router = useRouter();

  const [screen,      setScreen]      = useState(SCREEN.SELECT);
  const [testType,    setTestType]    = useState(null);       // 'PHQ-9' | 'GAD-7'
  const [answers,     setAnswers]     = useState([]);         // array of scores (0-3)
  const [currentQ,    setCurrentQ]    = useState(0);
  const [result,      setResult]      = useState(null);       // { score, severity }
  const [submitting,  setSubmitting]  = useState(false);

  const questions = testType === 'PHQ-9' ? PHQ9_QUESTIONS : GAD7_QUESTIONS;
  const progress  = questions.length > 0 ? (currentQ / questions.length) : 0;

  // ── Start a test ────────────────────────────────────────────────────────────
  const startTest = (type) => {
    setTestType(type);
    setAnswers([]);
    setCurrentQ(0);
    setResult(null);
    setScreen(SCREEN.QUIZ);
  };

  // ── Handle answer selection — auto-advances ──────────────────────────────────
  const handleAnswer = async (score) => {
    const newAnswers = [...answers, score];
    setAnswers(newAnswers);

    if (currentQ < questions.length - 1) {
      // Short delay so user sees the selection before advancing
      setTimeout(() => setCurrentQ((q) => q + 1), 300);
    } else {
      // Last question — calculate and submit
      const total = newAnswers.reduce((sum, s) => sum + s, 0);
      const severity = getSeverity(testType, total);
      setSubmitting(true);
      try {
        await submitAssessment({ test_type: testType, answers: newAnswers, total_score: total });
      } catch {
        // Still show results even if submission fails
      } finally {
        setSubmitting(false);
      }
      setResult({ score: total, severity });
      setScreen(SCREEN.RESULT);

      // Hard trigger for severe
      if (severity.label === 'Severe' || severity.label === 'Moderately Severe') {
        setTimeout(() => router.push('/screens/crisis'), 2500);
      }
    }
  };

  // ── Go back one question ─────────────────────────────────────────────────────
  const handleBack = () => {
    if (currentQ === 0) {
      setScreen(SCREEN.SELECT);
    } else {
      setCurrentQ((q) => q - 1);
      setAnswers((prev) => prev.slice(0, -1));
    }
  };

  // ─── SELECT screen ──────────────────────────────────────────────────────────
  if (screen === SCREEN.SELECT) {
    return (
      <SafeAreaView style={styles.container}>
        <TouchableOpacity style={styles.closeBtn} onPress={() => router.back()}>
          <ChevronLeft color={COLORS.text} size={28} />
        </TouchableOpacity>

        <ScrollView contentContainerStyle={styles.selectContent}>
          <Text style={styles.selectTitle}>Clinical Assessment</Text>
          <Text style={styles.selectSubtitle}>
            These are standardised questionnaires used worldwide to screen for depression and anxiety.
            Select one to begin.
          </Text>

          <View style={styles.disclaimer}>
            <Info color={COLORS.secondary} size={16} />
            <Text style={styles.disclaimerText}>
              Not a medical diagnosis. Results are for self-awareness only — always consult a professional.
            </Text>
          </View>

          {/* PHQ-9 card */}
          <TouchableOpacity style={styles.testCard} onPress={() => startTest('PHQ-9')}>
            <View style={[styles.testBadge, { backgroundColor: COLORS.primary + '20' }]}>
              <Text style={[styles.testBadgeText, { color: COLORS.primary }]}>PHQ-9</Text>
            </View>
            <Text style={styles.testCardTitle}>Depression Screening</Text>
            <Text style={styles.testCardDesc}>
              The Patient Health Questionnaire assesses the severity of depression symptoms over the last 2 weeks.
            </Text>
            <View style={styles.testMeta}>
              <Text style={styles.testMetaText}>9 questions · ~2 min</Text>
              <Text style={styles.testMetaText}>Max score: 27</Text>
            </View>
            <View style={styles.severityRow}>
              {['Minimal', 'Mild', 'Moderate', 'Severe'].map((s, i) => (
                <View key={s} style={[styles.severityChip, { backgroundColor: ['#9DBF9E', '#8BC34A', '#FFC107', '#E57373'][i] + '25' }]}>
                  <Text style={[styles.severityChipText, { color: ['#9DBF9E', '#6A9A3D', '#B8860B', '#E57373'][i] }]}>{s}</Text>
                </View>
              ))}
            </View>
            <View style={styles.startRow}>
              <Text style={[styles.startText, { color: COLORS.primary }]}>Start PHQ-9 →</Text>
            </View>
          </TouchableOpacity>

          {/* GAD-7 card */}
          <TouchableOpacity style={styles.testCard} onPress={() => startTest('GAD-7')}>
            <View style={[styles.testBadge, { backgroundColor: COLORS.secondary + '20' }]}>
              <Text style={[styles.testBadgeText, { color: COLORS.secondary }]}>GAD-7</Text>
            </View>
            <Text style={styles.testCardTitle}>Anxiety Screening</Text>
            <Text style={styles.testCardDesc}>
              The Generalised Anxiety Disorder scale measures how often you've been bothered by anxiety symptoms.
            </Text>
            <View style={styles.testMeta}>
              <Text style={styles.testMetaText}>7 questions · ~1 min</Text>
              <Text style={styles.testMetaText}>Max score: 21</Text>
            </View>
            <View style={styles.severityRow}>
              {['Minimal', 'Mild', 'Moderate', 'Severe'].map((s, i) => (
                <View key={s} style={[styles.severityChip, { backgroundColor: ['#9DBF9E', '#8BC34A', '#FFC107', '#E57373'][i] + '25' }]}>
                  <Text style={[styles.severityChipText, { color: ['#9DBF9E', '#6A9A3D', '#B8860B', '#E57373'][i] }]}>{s}</Text>
                </View>
              ))}
            </View>
            <View style={styles.startRow}>
              <Text style={[styles.startText, { color: COLORS.secondary }]}>Start GAD-7 →</Text>
            </View>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // ─── QUIZ screen ────────────────────────────────────────────────────────────
  if (screen === SCREEN.QUIZ) {
    const accentColor = testType === 'PHQ-9' ? COLORS.primary : COLORS.secondary;

    return (
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.quizHeader}>
          <TouchableOpacity onPress={handleBack} style={styles.backBtn}>
            <ChevronLeft color={COLORS.text} size={26} />
          </TouchableOpacity>
          {/* Progress bar */}
          <View style={styles.progressTrack}>
            <View style={[styles.progressFill, { width: `${progress * 100}%`, backgroundColor: accentColor }]} />
          </View>
          <View style={[styles.testPill, { backgroundColor: accentColor + '20' }]}>
            <Text style={[styles.testPillText, { color: accentColor }]}>{testType}</Text>
          </View>
        </View>

        <ScrollView contentContainerStyle={styles.quizContent}>
          <Text style={styles.questionCounter}>
            Question {currentQ + 1} of {questions.length}
          </Text>

          <View style={styles.questionCard}>
            <Text style={styles.questionInstruction}>
              Over the last 2 weeks, how often have you been bothered by the following?
            </Text>
            <Text style={styles.questionText}>{questions[currentQ]}</Text>
          </View>

          <View style={styles.optionsList}>
            {OPTIONS.map((opt) => (
              <TouchableOpacity
                key={opt.score}
                style={[
                  styles.optionBtn,
                  answers[currentQ] === opt.score && {
                    backgroundColor: accentColor + '20',
                    borderColor: accentColor,
                  },
                ]}
                onPress={() => handleAnswer(opt.score)}
                disabled={submitting}
              >
                <Text style={[
                  styles.optionText,
                  answers[currentQ] === opt.score && { color: accentColor, fontWeight: '600' },
                ]}>
                  {opt.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {submitting && (
            <View style={styles.submittingRow}>
              <ActivityIndicator color={accentColor} />
              <Text style={styles.submittingText}>Saving your results…</Text>
            </View>
          )}
        </ScrollView>
      </SafeAreaView>
    );
  }

  // ─── RESULT screen ──────────────────────────────────────────────────────────
  if (screen === SCREEN.RESULT && result) {
    const { score, severity } = result;
    const maxScore = testType === 'PHQ-9' ? 27 : 21;
    const isSevere = severity.label === 'Severe' || severity.label === 'Moderately Severe';

    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.resultContent}>
          {/* Score display */}
          <View style={[styles.scoreCircle, { borderColor: severity.color }]}>
            <Text style={[styles.scoreNumber, { color: severity.color }]}>{score}</Text>
            <Text style={styles.scoreMax}>/ {maxScore}</Text>
          </View>

          <Text style={[styles.severityLabel, { color: severity.color }]}>{severity.label}</Text>
          <Text style={styles.testLabel}>{testType} Score</Text>

          {/* Score bar */}
          <View style={styles.scoreBarTrack}>
            <View style={[styles.scoreBarFill, {
              width: `${(score / maxScore) * 100}%`,
              backgroundColor: severity.color,
            }]} />
          </View>

          {/* Action card */}
          {severity.action && (
            <View style={[styles.actionCard, { borderLeftColor: severity.color }]}>
              <Text style={styles.actionCardText}>{severity.action}</Text>
            </View>
          )}

          {!isSevere && (
            <View style={styles.successRow}>
              <CheckCircle color={COLORS.primary} size={18} />
              <Text style={styles.successText}>Assessment saved to your history</Text>
            </View>
          )}

          {isSevere && (
            <View style={[styles.crisisBanner, { backgroundColor: COLORS.crisis + '15', borderColor: COLORS.crisis + '40' }]}>
              <Text style={[styles.crisisBannerText, { color: COLORS.crisis }]}>
                Redirecting to crisis resources…
              </Text>
            </View>
          )}

          <View style={styles.resultActions}>
            <TouchableOpacity
              style={[styles.retakeBtn, { borderColor: severity.color }]}
              onPress={() => startTest(testType)}
            >
              <Text style={[styles.retakeText, { color: severity.color }]}>Retake {testType}</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.otherBtn, { backgroundColor: testType === 'PHQ-9' ? COLORS.secondary : COLORS.primary }]}
              onPress={() => startTest(testType === 'PHQ-9' ? 'GAD-7' : 'PHQ-9')}
            >
              <Text style={styles.otherBtnText}>
                Take {testType === 'PHQ-9' ? 'GAD-7' : 'PHQ-9'} →
              </Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity style={styles.doneBtn} onPress={() => router.back()}>
            <Text style={styles.doneBtnText}>Done</Text>
          </TouchableOpacity>

          <Text style={styles.resultDisclaimer}>
            These results are not a clinical diagnosis. Please consult a qualified mental health professional for advice.
          </Text>
        </ScrollView>
      </SafeAreaView>
    );
  }

  return null;
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container:       { flex: 1, backgroundColor: COLORS.background },

  // SELECT
  closeBtn:        { padding: 20, alignSelf: 'flex-start' },
  selectContent:   { paddingHorizontal: 24, paddingBottom: 40 },
  selectTitle:     { fontSize: 28, fontWeight: 'bold', color: COLORS.text, marginBottom: 10 },
  selectSubtitle:  { fontSize: 15, color: COLORS.text, opacity: 0.6, lineHeight: 22, marginBottom: 18 },
  disclaimer: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 10,
    backgroundColor: COLORS.secondary + '15', borderRadius: 14,
    padding: 14, marginBottom: 24,
  },
  disclaimerText:  { flex: 1, fontSize: 13, color: COLORS.text, opacity: 0.7, lineHeight: 18 },
  testCard: {
    backgroundColor: COLORS.card, borderRadius: 24, padding: 22,
    marginBottom: 18, elevation: 2,
    shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 10,
  },
  testBadge:       { alignSelf: 'flex-start', paddingHorizontal: 12, paddingVertical: 5, borderRadius: 10, marginBottom: 12 },
  testBadgeText:   { fontSize: 13, fontWeight: 'bold', letterSpacing: 0.5 },
  testCardTitle:   { fontSize: 20, fontWeight: 'bold', color: COLORS.text, marginBottom: 8 },
  testCardDesc:    { fontSize: 14, color: COLORS.text, opacity: 0.6, lineHeight: 20, marginBottom: 14 },
  testMeta:        { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 14 },
  testMetaText:    { fontSize: 12, color: COLORS.text, opacity: 0.45 },
  severityRow:     { flexDirection: 'row', gap: 6, marginBottom: 16, flexWrap: 'wrap' },
  severityChip:    { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  severityChipText:{ fontSize: 11, fontWeight: '600' },
  startRow:        { alignItems: 'flex-end' },
  startText:       { fontSize: 15, fontWeight: 'bold' },

  // QUIZ
  quizHeader: {
    flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16,
    paddingTop: 8, paddingBottom: 12, gap: 10,
  },
  backBtn:         { padding: 4 },
  progressTrack: {
    flex: 1, height: 6, backgroundColor: COLORS.gray,
    borderRadius: 3, overflow: 'hidden',
  },
  progressFill:    { height: '100%', borderRadius: 3 },
  testPill:        { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10 },
  testPillText:    { fontSize: 12, fontWeight: 'bold' },
  quizContent:     { paddingHorizontal: 24, paddingBottom: 40 },
  questionCounter: { fontSize: 13, color: COLORS.text, opacity: 0.45, marginBottom: 16, marginTop: 8 },
  questionCard: {
    backgroundColor: COLORS.card, borderRadius: 24, padding: 22,
    marginBottom: 24, elevation: 2,
    shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 8,
  },
  questionInstruction: {
    fontSize: 13, color: COLORS.text, opacity: 0.5,
    marginBottom: 12, fontStyle: 'italic',
  },
  questionText:    { fontSize: 20, fontWeight: 'bold', color: COLORS.text, lineHeight: 28 },
  optionsList:     { gap: 12 },
  optionBtn: {
    backgroundColor: COLORS.card, borderRadius: 18,
    paddingVertical: 18, paddingHorizontal: 22,
    borderWidth: 1.5, borderColor: COLORS.gray,
    elevation: 1,
  },
  optionText:      { fontSize: 16, color: COLORS.text, textAlign: 'center' },
  submittingRow:   { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, marginTop: 24 },
  submittingText:  { fontSize: 14, color: COLORS.text, opacity: 0.5 },

  // RESULT
  resultContent:   { paddingHorizontal: 28, paddingBottom: 40, alignItems: 'center', paddingTop: 30 },
  scoreCircle: {
    width: 130, height: 130, borderRadius: 65,
    borderWidth: 4, justifyContent: 'center', alignItems: 'center',
    marginBottom: 18,
  },
  scoreNumber:     { fontSize: 44, fontWeight: 'bold' },
  scoreMax:        { fontSize: 16, color: COLORS.text, opacity: 0.4 },
  severityLabel:   { fontSize: 28, fontWeight: 'bold', marginBottom: 4 },
  testLabel:       { fontSize: 14, color: COLORS.text, opacity: 0.5, marginBottom: 20 },
  scoreBarTrack: {
    width: '100%', height: 8, backgroundColor: COLORS.gray,
    borderRadius: 4, overflow: 'hidden', marginBottom: 24,
  },
  scoreBarFill:    { height: '100%', borderRadius: 4 },
  actionCard: {
    width: '100%', backgroundColor: COLORS.card, borderRadius: 20,
    padding: 18, borderLeftWidth: 4, marginBottom: 20,
  },
  actionCardText:  { fontSize: 15, color: COLORS.text, lineHeight: 22 },
  successRow:      { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 24 },
  successText:     { fontSize: 14, color: COLORS.primary },
  crisisBanner: {
    width: '100%', padding: 16, borderRadius: 16,
    borderWidth: 1, marginBottom: 20, alignItems: 'center',
  },
  crisisBannerText:{ fontSize: 15, fontWeight: '600' },
  resultActions:   { flexDirection: 'row', gap: 12, width: '100%', marginBottom: 14 },
  retakeBtn: {
    flex: 1, paddingVertical: 15, borderRadius: 18,
    borderWidth: 1.5, alignItems: 'center',
  },
  retakeText:      { fontSize: 15, fontWeight: '600' },
  otherBtn:        { flex: 1, paddingVertical: 15, borderRadius: 18, alignItems: 'center' },
  otherBtnText:    { color: 'white', fontSize: 15, fontWeight: '600' },
  doneBtn: {
    width: '100%', backgroundColor: COLORS.card, paddingVertical: 16,
    borderRadius: 18, alignItems: 'center', marginBottom: 20,
    borderWidth: 1, borderColor: COLORS.gray,
  },
  doneBtnText:     { fontSize: 16, color: COLORS.text, opacity: 0.6 },
  resultDisclaimer:{ fontSize: 11, color: COLORS.text, opacity: 0.3, textAlign: 'center', lineHeight: 16 },
});