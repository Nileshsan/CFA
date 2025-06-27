import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform, Alert } from 'react-native';
import AnimatedGradient from './components/AnimatedGradient';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import QRCode from 'react-native-qrcode-svg';
import { useRouter } from 'expo-router';

// Simulate API token generation (in real app, fetch from backend)
const generateToken = () => {
  return 'CFA-' + Math.random().toString(36).substr(2, 16).toUpperCase();
};

export default function APITokenScreen() {
  const [apiToken] = useState(generateToken());
  const router = useRouter();

  const handleCopy = () => {
    Clipboard.setStringAsync(apiToken);
    Alert.alert('Copied!', 'API token copied to clipboard.');
  };

  const handleNext = () => {
    // Go to the next state, e.g., model training or main app
    router.replace('/Main');
  };

  return (
    <View style={styles.container}>
      <AnimatedGradient />
      <View style={styles.card}>
        <Text style={styles.title}>Your API Token</Text>
        <View style={styles.qrContainer}>
          <QRCode value={apiToken} size={180} backgroundColor="transparent" />
        </View>
        <View style={styles.tokenRow}>
          <Text style={styles.token}>{apiToken}</Text>
          <TouchableOpacity onPress={handleCopy} style={styles.copyBtn}>
            <Ionicons name="copy-outline" size={22} color="#2e7d32" />
          </TouchableOpacity>
        </View>
        <Text style={styles.info}>
          Use this token in your desktop sync agent to securely link your Tally data with your account.
        </Text>
        <TouchableOpacity style={styles.nextBtn} onPress={handleNext}>
          <Text style={styles.nextBtnText}>Proceed with Authentication</Text>
          <Ionicons name="arrow-forward-circle" size={22} color="#fff" style={{ marginLeft: 8 }} />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'transparent',
  },
  card: {
    width: '90%',
    maxWidth: 400,
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)',
    padding: 32,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 24,
    elevation: 12,
    backdropFilter: Platform.OS === 'web' ? 'blur(12px)' : undefined,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2e7d32',
    marginBottom: 18,
    textAlign: 'center',
  },
  qrContainer: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 12,
    marginBottom: 18,
    shadowColor: '#0a2a66',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 6,
  },
  tokenRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  token: {
    fontSize: 18,
    color: '#2e7d32',
    fontWeight: 'bold',
    letterSpacing: 1.2,
    backgroundColor: 'rgba(255,255,255,0.8)',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  copyBtn: {
    marginLeft: 10,
    padding: 6,
    borderRadius: 8,
    backgroundColor: 'rgba(210,236,248,0.5)',
  },
  info: {
    marginTop: 16,
    color: '#2e7d32',
    fontSize: 14,
    textAlign: 'center',
  },
  nextBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2e7d32',
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 24,
    width: '100%',
    justifyContent: 'center',
    marginTop: 18,
  },
  nextBtnText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
});
