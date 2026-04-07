import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import { Mic, Image as ImageIcon, Video, Send, Paperclip } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';

export default function ChatbotScreen() {
  const [message, setMessage] = useState('');

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      {/* AI Visual Area (The "Cozy" Orb) */}
      <View style={styles.aiContainer}>
        <View style={styles.orbShadow}>
           <View style={styles.aiOrb}>
             {/* This is where your AI animation will eventually go */}
           </View>
        </View>
        <Text style={styles.aiTitle}>Speak your thoughts</Text>
        <Text style={styles.aiSubtext}>I'm listening and here to help.</Text>
      </View>

      {/* Input Area */}
      <View style={styles.inputWrapper}>
        <View style={styles.actionRow}>
          <TouchableOpacity style={styles.iconButton}>
            <ImageIcon color={COLORS.secondary} size={24} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.iconButton}>
            <Video color={COLORS.secondary} size={24} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.iconButton}>
            <Mic color={COLORS.secondary} size={24} />
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
          />
          <TouchableOpacity style={[styles.sendButton, { opacity: message ? 1 : 0.5 }]}>
            <Send color="white" size={20} />
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  aiContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40
  },
  orbShadow: {
    width: 180,
    height: 180,
    borderRadius: 90,
    backgroundColor: COLORS.accent + '30', // Soft lavender glow
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 30,
  },
  aiOrb: {
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: COLORS.accent,
    // Add a slight gradient-like feel using shadows
    shadowColor: COLORS.secondary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 20,
    elevation: 10,
  },
  aiTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.text,
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Georgia' : 'serif' // Give it a more "cozy" serif look
  },
  aiSubtext: { fontSize: 16, color: COLORS.text, opacity: 0.6, marginTop: 10 },

  inputWrapper: {
    padding: 20,
    backgroundColor: COLORS.card,
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    elevation: 10,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 10,
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 15
  },
  iconButton: {
    padding: 12,
    backgroundColor: COLORS.background,
    borderRadius: 15,
  },
  textInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: Platform.OS === 'ios' ? 12 : 5,
  },
  input: {
    flex: 1,
    color: COLORS.text,
    fontSize: 16,
    maxHeight: 100,
  },
  sendButton: {
    backgroundColor: COLORS.primary,
    padding: 10,
    borderRadius: 12,
    marginLeft: 10,
  }
});