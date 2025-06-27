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
import { Ionicons, FontAwesome } from '@expo/vector-icons';
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
  interpolate,
  Easing
} from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Leaf } from 'lucide-react-native';

const { width, height } = Dimensions.get('window');

const logo = require('../assets/images/converted-image.png');

export default function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({ username: '', password: '' });
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  const router = useRouter();

  // Animation values
  const fadeAnim = useSharedValue(0);
  const slideAnim = useSharedValue(50);
  const scaleAnim = useSharedValue(0.8);
  const logoRotation = useSharedValue(0);
  const pulseAnim = useSharedValue(1);

  useEffect(() => {
    // Initial animations
    fadeAnim.value = withTiming(1, { duration: 1000 });
    slideAnim.value = withTiming(0, { duration: 800, easing: Easing.out(Easing.quad) });
    scaleAnim.value = withTiming(1, { duration: 800, easing: Easing.out(Easing.back(1.2)) });
    
    // Logo rotation animation
    logoRotation.value = withRepeat(
      withTiming(360, { duration: 10000, easing: Easing.linear }),
      -1,
      false
    );

    // Pulse animation for login button
    pulseAnim.value = withRepeat(
      withSequence(
        withTiming(1.05, { duration: 1500 }),
        withTiming(1, { duration: 1500 })
      ),
      -1,
      true
    );

    // Keyboard listeners
    const keyboardDidShowListener = Keyboard.addListener('keyboardDidShow', () => {
      setKeyboardVisible(true);
    });
    const keyboardDidHideListener = Keyboard.addListener('keyboardDidHide', () => {
      setKeyboardVisible(false);
    });

    return () => {
      keyboardDidShowListener?.remove();
      keyboardDidHideListener?.remove();
    };
  }, []);

  const animatedContainerStyle = useAnimatedStyle(() => ({
    opacity: fadeAnim.value,
    transform: [
      { translateY: slideAnim.value },
      { scale: scaleAnim.value }
    ],
  }));

  const animatedLogoStyle = useAnimatedStyle(() => ({
    transform: [
      { rotate: `${logoRotation.value}deg` }
    ],
  }));

  const animatedButtonStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: pulseAnim.value }
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
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      await AsyncStorage.setItem('isLoggedIn', 'true');
      await AsyncStorage.setItem('username', username);
      
      // Success animation
      scaleAnim.value = withSequence(
        withTiming(1.1, { duration: 100 }),
        withTiming(1, { duration: 100 })
      );
      
      router.replace('/APIToken');
    } catch (error) {
      Alert.alert('Login Failed', 'Please check your credentials and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    Alert.alert('Coming Soon', 'Google login will be available in the next update!');
  };

  const handleRegister = () => {
    Alert.alert('Registration', 'Registration feature coming soon!');
  };

  const handleForgotPassword = () => {
    Alert.alert('Forgot Password', 'Password reset feature coming soon!');
  };

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={['#d4fc79', '#96e6a1']}
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
              <Animated.View style={[styles.logoBackground, animatedLogoStyle]}>
                <Leaf size={48} color="#ffffff" strokeWidth={2} />
              </Animated.View>
              <Text style={styles.appName}>CropFlow AI</Text>
              <Text style={styles.tagline}>Smart Agriculture Solutions</Text>
            </Animated.View>

            <Animated.View style={[animatedContainerStyle]}>
              <BlurView intensity={Platform.OS === 'ios' ? 25 : 80} style={styles.loginCard}>
                <Image source={logo} style={styles.logo} resizeMode="contain" />
                <Text style={styles.title}>Welcome to CFA</Text>
                <Text style={styles.subtitle}>AI-powered Tally Insights</Text>

                <View style={styles.inputContainer}>
                  <View style={styles.inputWrapper}>
                    <Ionicons name="person-outline" size={20} color="#388e3c" style={styles.inputIcon} />
                    <TextInput
                      style={[styles.input, errors.username ? styles.inputError : null]}
                      placeholder="Username"
                      placeholderTextColor="#388e3caa"
                      value={username}
                      onChangeText={(text) => {
                        setUsername(text);
                        if (errors.username) setErrors({...errors, username: ''});
                      }}
                      autoCapitalize="none"
                      autoCorrect={false}
                    />
                  </View>
                  {errors.username ? <Text style={styles.errorText}>{errors.username}</Text> : null}
                </View>

                <View style={styles.inputContainer}>
                  <View style={styles.inputWrapper}>
                    <Ionicons name="lock-closed-outline" size={20} color="#388e3c" style={styles.inputIcon} />
                    <TextInput
                      style={[styles.input, errors.password ? styles.inputError : null]}
                      placeholder="Password"
                      placeholderTextColor="#388e3caa"
                      value={password}
                      onChangeText={(text) => {
                        setPassword(text);
                        if (errors.password) setErrors({...errors, password: ''});
                      }}
                      secureTextEntry={!showPassword}
                    />
                    <TouchableOpacity 
                      onPress={() => setShowPassword(!showPassword)}
                      style={styles.eyeIcon}
                    >
                      {showPassword ? 
                        <Ionicons name="eye-off-outline" size={20} color="#388e3c" /> : 
                        <Ionicons name="eye-outline" size={20} color="#388e3c" />
                      }
                    </TouchableOpacity>
                  </View>
                  {errors.password ? <Text style={styles.errorText}>{errors.password}</Text> : null}
                </View>

                <TouchableOpacity onPress={handleForgotPassword} style={styles.forgotPassword}>
                  <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
                </TouchableOpacity>

                <Animated.View style={animatedButtonStyle}>
                  <TouchableOpacity 
                    style={[styles.loginBtn, isLoading && styles.loginBtnDisabled]} 
                    onPress={handleLogin}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <Text style={styles.loginBtnText}>Signing In...</Text>
                    ) : (
                      <>
                        <Ionicons name="log-in-outline" size={20} color="#fff" style={{ marginRight: 8 }} />
                        <Text style={styles.loginBtnText}>Login</Text>
                      </>
                    )}
                  </TouchableOpacity>
                </Animated.View>

                <View style={styles.divider}>
                  <View style={styles.dividerLine} />
                  <Text style={styles.dividerText}>or</Text>
                  <View style={styles.dividerLine} />
                </View>

                <TouchableOpacity style={styles.googleBtn} onPress={handleGoogleLogin}>
                  <View style={styles.googleIcon}>
                    <FontAwesome name="google" size={20} color="#fbc02d" style={{ marginRight: 10 }} />
                    <Text style={styles.googleBtnText}>Continue with Google</Text>
                  </View>
                </TouchableOpacity>

                <View style={styles.registerLink}>
                  <Text style={{ color: '#388e3c' }}>Don't have an account?{' '}
                    <Text style={styles.registerText} onPress={handleRegister}>Register here</Text>
                  </Text>
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
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  keyboardAvoid: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
    minHeight: height,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logoBackground: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  appName: {
    fontSize: 32,
    fontWeight: '800',
    color: '#ffffff',
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  tagline: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginTop: 4,
  },
  loginCard: {
    width: '92%',
    maxWidth: 410,
    backgroundColor: 'rgba(255,255,255,0.22)',
    borderRadius: 24,
    borderWidth: 1,
    borderColor: 'rgba(251,230,109,0.45)',
    padding: 36,
    alignItems: 'center',
    shadowColor: '#388e3c',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.18,
    shadowRadius: 32,
    elevation: 16,
    backdropFilter: Platform.OS === 'web' ? 'blur(16px)' : undefined,
  },
  logo: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: '#8bc34a',
    backgroundColor: '#fff',
    shadowColor: '#fbc02d',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.18,
    shadowRadius: 8,
    elevation: 8,
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#388e3c',
    marginBottom: 4,
    fontFamily: Platform.OS === 'ios' ? 'Poppins' : undefined,
    textAlign: 'center',
    letterSpacing: 1.1,
  },
  subtitle: {
    fontSize: 16,
    color: '#fbc02d',
    marginBottom: 18,
    textAlign: 'center',
    fontWeight: '600',
    letterSpacing: 0.8,
  },
  inputContainer: {
    marginBottom: 20,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(102, 126, 234, 0.3)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  inputIcon: {
    marginLeft: 16,
    marginRight: 12,
  },
  input: {
    flex: 1,
    paddingVertical: 16,
    paddingRight: 16,
    fontSize: 16,
    color: '#333',
    backgroundColor: 'rgba(251, 230, 109, 0.85)',
    borderRadius: 12,
    marginBottom: 18,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  inputError: {
    borderColor: '#ff4757',
    borderWidth: 1,
  },
  eyeIcon: {
    padding: 16,
  },
  errorText: {
    color: '#ff4757',
    fontSize: 12,
    marginTop: 4,
    marginLeft: 4,
  },
  forgotPassword: {
    alignSelf: 'flex-end',
    marginBottom: 24,
  },
  forgotPasswordText: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 14,
    textDecorationLine: 'underline',
  },
  loginBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#8bc34a',
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 28,
    width: '100%',
    marginTop: 4,
    marginBottom: 10,
    shadowColor: '#fbc02d',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.18,
    shadowRadius: 8,
    elevation: 6,
  },
  loginBtnDisabled: {
    opacity: 0.7,
  },
  loginBtnText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 17,
    letterSpacing: 0.5,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  dividerText: {
    color: 'rgba(255, 255, 255, 0.6)',
    paddingHorizontal: 16,
    fontSize: 14,
  },
  googleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fffde7',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#fbc02d',
    paddingVertical: 12,
    paddingHorizontal: 22,
    width: '100%',
    marginTop: 10,
    marginBottom: 10,
    shadowColor: '#fbc02d',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 6,
    elevation: 4,
  },
  googleIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#4285f4',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  googleBtnText: {
    color: '#444',
    fontWeight: '600',
    fontSize: 16,
    letterSpacing: 0.3,
  },
  registerLink: {
    marginTop: 20,
    fontSize: 15,
  },
  registerText: {
    fontWeight: 'bold',
    color: '#388e3c',
    textDecorationLine: 'underline',
  },
});