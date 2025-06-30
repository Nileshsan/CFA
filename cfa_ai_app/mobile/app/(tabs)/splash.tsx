import React, { useEffect, useRef } from 'react';
import { View, Image, StyleSheet, Animated, Easing } from 'react-native';
import { useRouter } from 'expo-router';

// Use the PNG PBS logo for compatibility (corrected path)
const logo = require('../../assets/images/converted-image.png');

export default function SplashScreen() {
  const router = useRouter();
  const scaleAnim = useRef(new Animated.Value(0.7)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 1200,
        useNativeDriver: true,
        easing: Easing.out(Easing.exp),
      }),
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 1200,
        useNativeDriver: true,
        easing: Easing.out(Easing.exp),
      }),
    ]).start();
    const timer = setTimeout(() => {
      router.replace('/(tabs)/login');
    }, 5000); // Show splash for 5 seconds
    return () => clearTimeout(timer);
  }, []);

  const rotate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <View style={styles.container}>
      <Animated.View
        style={{
          transform: [
            { scale: scaleAnim },
            { rotate },
          ],
          shadowColor: '#0a2a66',
          shadowOffset: { width: 0, height: 8 },
          shadowOpacity: 0.3,
          shadowRadius: 16,
          elevation: 16,
          backgroundColor: 'rgba(210, 236, 248, 0.8)',
          borderRadius: 120,
          padding: 16,
        }}
      >
        <Image source={logo} style={styles.logo} resizeMode="cover" />
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'rgba(210, 248, 212, 0.8)', // Soft PBS blue background
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    width: 200,
    height: 200,
    borderRadius: 100, // Makes the logo circular
    borderWidth: 4,
    borderColor: '#0a2a66', // PBS blue border
    backgroundColor: '#fff',
    shadowColor: '#0a2a66',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 16,
  },
});
