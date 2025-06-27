import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Platform, Alert } from 'react-native';
import { Ionicons, FontAwesome } from '@expo/vector-icons';
import AnimatedGradient from './components/AnimatedGradient';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();

  const handleLogin = async () => {
    // Simple demo: accept any non-empty username/password
    if (username.trim() && password.trim()) {
      await AsyncStorage.setItem('isLoggedIn', 'true');
      router.replace('/APIToken'); // After API token, go to Main
    } else {
      Alert.alert('Login Failed', 'Please enter both username and password.');
    }
  };

  const handleGoogleLogin = () => {
    // TODO: Implement Google login logic
    Alert.alert('Google login pressed!');
  };

  const handleRegister = () => {
    // TODO: Navigate to register screen
    Alert.alert('Register link pressed!');
  };

  return (
    <View style={styles.container}>
      <AnimatedGradient />
      <View style={styles.loginCard}>
        <Text style={styles.title}><FontAwesome name="leaf" size={28} color="#2e7d32" /> CFA Login</Text>
        <TextInput
          style={styles.input}
          placeholder="Username"
          placeholderTextColor="#2e7d32aa"
          value={username}
          onChangeText={setUsername}
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor="#2e7d32aa"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        <TouchableOpacity style={styles.loginBtn} onPress={handleLogin}>
          <Ionicons name="log-in-outline" size={20} color="#fff" style={{ marginRight: 8 }} />
          <Text style={styles.loginBtnText}>Login</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.googleBtn} onPress={handleGoogleLogin}>
          <FontAwesome name="google" size={20} color="#ea4335" style={{ marginRight: 10 }} />
          <Text style={styles.googleBtnText}>Continue with Google</Text>
        </TouchableOpacity>
        <View style={styles.registerLink}>
          <Text style={{ color: '#2e7d32' }}>Don't have an account?{' '}
            <Text style={styles.registerText} onPress={handleRegister}>Register here</Text>
          </Text>
        </View>
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
  loginCard: {
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
    fontSize: 26,
    fontWeight: 'bold',
    color: '#2e7d32',
    marginBottom: 24,
    fontFamily: Platform.OS === 'ios' ? 'Poppins' : undefined,
    textAlign: 'center',
  },
  input: {
    width: '100%',
    backgroundColor: 'rgba(255,255,255,0.8)',
    borderRadius: 10,
    padding: 14,
    marginBottom: 16,
    fontSize: 16,
    color: '#2e7d32',
    borderWidth: 0,
  },
  loginBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#8bc34a',
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 24,
    width: '100%',
    justifyContent: 'center',
    marginTop: 4,
    marginBottom: 8,
  },
  loginBtnText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  googleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    paddingVertical: 10,
    paddingHorizontal: 18,
    width: '100%',
    justifyContent: 'center',
    marginTop: 10,
    marginBottom: 8,
  },
  googleBtnText: {
    color: '#444',
    fontWeight: '500',
    fontSize: 15,
  },
  registerLink: {
    marginTop: 18,
    fontSize: 14,
  },
  registerText: {
    fontWeight: 'bold',
    color: '#2e7d32',
    textDecorationLine: 'underline',
  },
});
