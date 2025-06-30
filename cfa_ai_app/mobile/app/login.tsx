import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Platform,
  Alert,
  Keyboard,
  KeyboardAvoidingView,
  ScrollView,
  Dimensions,
  Image
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withRepeat,
  withSequence,
  Easing,
} from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LogIn, Mail, Lock, Eye, EyeOff } from 'lucide-react-native';
import LogoImage from '../assets/images/converted-image.png';

const { width, height } = Dimensions.get('window');

export default function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({ username: '', password: '' });
  const router = useRouter();

  // Animations
  const fadeAnim = useSharedValue(0);
  const slideAnim = useSharedValue(50);
  const scaleAnim = useSharedValue(0.95);

  useEffect(() => {
    fadeAnim.value = withTiming(1, { duration: 900 });
    slideAnim.value = withTiming(0, { duration: 700, easing: Easing.out(Easing.quad) });
    scaleAnim.value = withTiming(1, { duration: 700, easing: Easing.out(Easing.back(1.2)) });
  }, []);

  const animatedContainerStyle = useAnimatedStyle(() => ({
    opacity: fadeAnim.value,
    transform: [
      { translateY: slideAnim.value },
      { scale: scaleAnim.value },
    ],
  }));

  const validateForm = () => {
    const newErrors = { username: '', password: '' };
    let isValid = true;

    if (!username.trim()) {
      newErrors.username = 'Username is required';
      isValid = false;
    } else if (username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
      isValid = false;
    }

    if (!password.trim()) {
      newErrors.password = 'Password is required';
      isValid = false;
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleLogin = async () => {
    if (!validateForm()) return;
    setIsLoading(true);

    try {
      await new Promise(resolve => setTimeout(resolve, 1200));
      await AsyncStorage.setItem('isLoggedIn', 'true');
      await AsyncStorage.setItem('username', username);
      router.replace('/APIToken');
    } catch (error) {
      Alert.alert('Login Failed', 'Please check your credentials and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={['#fff', '#b7e4c7', '#f5f5dc']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradient}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardAvoid}
        >
          <ScrollView
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            <Animated.View style={[styles.logoContainer, animatedContainerStyle]}>
              <View style={styles.logoBackground}>
                <Image
                  source={LogoImage}
                  style={styles.logoImage}
                  resizeMode="contain"
                />
              </View>
              <Text style={styles.appName}>CFA Login</Text>
              <Text style={styles.tagline}>AI-powered Financial Insights</Text>
            </Animated.View>

            <Animated.View style={animatedContainerStyle}>
              <BlurView intensity={Platform.OS === 'ios' ? 25 : 80} style={styles.loginCard}>
                <Text style={styles.title}>Sign in to your account</Text>

                <View style={styles.inputContainer}>
                  <View style={styles.inputWrapper}>
                    <Mail size={20} color="#a8e063" style={styles.inputIcon} />
                    <TextInput
                      style={[styles.input, errors.username ? styles.inputError : null]}
                      placeholder="Username"
                      placeholderTextColor="#a8e063aa"
                      value={username}
                      onChangeText={text => {
                        setUsername(text);
                        if (errors.username) setErrors({ ...errors, username: '' });
                      }}
                      autoCapitalize="none"
                      autoCorrect={false}
                    />
                  </View>
                  {errors.username ? <Text style={styles.errorText}>{errors.username}</Text> : null}
                </View>

                <View style={styles.inputContainer}>
                  <View style={styles.inputWrapper}>
                    <Lock size={20} color="#a8e063" style={styles.inputIcon} />
                    <TextInput
                      style={[styles.input, errors.password ? styles.inputError : null]}
                      placeholder="Password"
                      placeholderTextColor="#a8e063aa"
                      value={password}
                      onChangeText={text => {
                        setPassword(text);
                        if (errors.password) setErrors({ ...errors, password: '' });
                      }}
                      secureTextEntry={!showPassword}
                    />
                    <TouchableOpacity
                      onPress={() => setShowPassword(!showPassword)}
                      style={styles.eyeIcon}
                    >
                      {showPassword ? (
                        <EyeOff size={20} color="#a8e063" />
                      ) : (
                        <Eye size={20} color="#a8e063" />
                      )}
                    </TouchableOpacity>
                  </View>
                  {errors.password ? <Text style={styles.errorText}>{errors.password}</Text> : null}
                </View>

                <TouchableOpacity style={styles.loginBtn} onPress={handleLogin} disabled={isLoading}>
                  {isLoading ? (
                    <Text style={styles.loginBtnText}>Signing In...</Text>
                  ) : (
                    <>
                      <LogIn size={20} color="#fff" style={styles.buttonIcon} />
                      <Text style={styles.loginBtnText}>Login</Text>
                    </>
                  )}
                </TouchableOpacity>

                <TouchableOpacity style={styles.forgotPassword}>
                  <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
                </TouchableOpacity>

                <View style={styles.divider}>
                  <View style={styles.dividerLine} />
                  <Text style={styles.dividerText}>or</Text>
                  <View style={styles.dividerLine} />
                </View>

                <TouchableOpacity style={styles.googleBtn} onPress={() => Alert.alert('Coming Soon', 'Google login will be available soon!')}>
                  <View style={styles.googleIcon}>
                    <Text style={styles.googleIconText}>G</Text>
                  </View>
                  <Text style={styles.googleBtnText}>Continue with Google</Text>
                </TouchableOpacity>

                <View style={styles.registerLink}>
                  <Text style={styles.registerPrompt}>Don't have an account? </Text>
                  <TouchableOpacity onPress={() => Alert.alert('Registration', 'Registration coming soon!')}>
                    <Text style={styles.registerText}>Register here</Text>
                  </TouchableOpacity>
                </View>
              </BlurView>
            </Animated.View>
          </ScrollView>
        </KeyboardAvoidingView>
      </LinearGradient>
    </SafeAreaView>
  );
}



const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  keyboardAvoid: { flex: 1 },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
    minHeight: height,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logoBackground: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(183,228,199,0.18)', // very light green glass
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 14,
    shadowColor: '#b7e4c7',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.13,
    shadowRadius: 10,
    elevation: 8,
  },
  logoImage: {
    width: 56,
    height: 56,
    borderRadius: 16,
  },
  appName: {
    fontSize: 30,
    fontWeight: '800',
    color: '#5b8c5a', // softer green
    textAlign: 'center',
    letterSpacing: 1.1,
  },
  tagline: {
    fontSize: 15,
    color: '#b2b200', // soft yellow-green
    textAlign: 'center',
    marginTop: 2,
    marginBottom: 2,
  },
  loginCard: {
    width: '96%',
    maxWidth: 410,
    backgroundColor: 'rgba(255,255,255,0.22)',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.25)',
    padding: 32,
    alignItems: 'center',
    shadowColor: '#e6ee9c',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.12,
    shadowRadius: 32,
    elevation: 12,
    marginBottom: 20,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#5b8c5a',
    marginBottom: 22,
    textAlign: 'center',
    letterSpacing: 1.1,
  },
  input: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.97)',
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    color: '#5b8c5a',
    borderWidth: 0,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  inputError: {
    borderWidth: 1.5,
    borderColor: '#ff6f61',
  },
  inputContainer: {
    marginBottom: 16,
    width: '100%',
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(245, 255, 250, 0.95)', // very light green
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(200,230,201,0.18)',
    shadowColor: '#b2dfdb',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
    paddingRight: 8,
  },
  inputIcon: {
    marginLeft: 12,
    marginRight: 8,
  },
  loginBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#b2df76', // lighter green-yellow
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 28,
    width: '100%',
    justifyContent: 'center',
    marginTop: 4,
    marginBottom: 10,
    shadowColor: '#f9fbe7',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.13,
    shadowRadius: 8,
    elevation: 6,
  },
  
  loginBtnText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 17,
    letterSpacing: 0.5,
  },
  buttonIcon: {
    marginRight: 8,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 18,
    marginTop: 8,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(200,230,201,0.3)',
  },
  dividerText: {
    color: '#b2b200',
    paddingHorizontal: 12,
    fontSize: 14,
  },
  googleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fffde7',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#f9e79f',
    paddingVertical: 12,
    paddingHorizontal: 22,
    width: '100%',
    justifyContent: 'center',
    marginTop: 4,
    marginBottom: 8,
    shadowColor: '#f9e79f',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 4,
  },
  googleIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#b2b200',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  googleIconText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 14,
  },
  googleBtnText: {
    color: '#444',
    fontWeight: '600',
    fontSize: 16,
    letterSpacing: 0.3,
  },
  registerLink: {
    marginTop: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  registerPrompt: {
    color: '#b2b200',
    fontSize: 14,
  },
  registerText: {
    fontWeight: 'bold',
    color: '#5b8c5a',
    textDecorationLine: 'underline',
    fontSize: 14,
  },
  errorText: {
    color: '#ff6f61',
    fontSize: 12,
    marginTop: 2,
    marginLeft: 4,
  },
  forgotPassword: {
    alignSelf: 'flex-end',
    marginBottom: 8,
  },
  forgotPasswordText: {
    color: '#b2b200',
    fontSize: 14,
    textDecorationLine: 'underline',
  },
  eyeIcon: {
    position: 'absolute',
    right: 12,
    padding: 4,
    zIndex: 1,
  },
});