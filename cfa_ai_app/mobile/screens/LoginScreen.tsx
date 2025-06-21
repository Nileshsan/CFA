import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet } from 'react-native';
import api from '../utils/api';

import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Login: undefined;
  Dashboard: undefined;
};

type LoginScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Login'>;

interface Props {
  navigation: LoginScreenNavigationProp;
}

export default function LoginScreen({ navigation }: Props) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const login = async () => {
    try {
      const res = await api.post('token/', { username, password });
      const token = res.data.access;
      console.log('Token:', token);
      navigation.navigate('Dashboard');
    } catch (error) {
      alert('Login failed');
    }
  };

  return (
    <View style={styles.container}>
      <Text>Username</Text>
      <TextInput value={username} onChangeText={setUsername} style={styles.input} />
      <Text>Password</Text>
      <TextInput value={password} onChangeText={setPassword} secureTextEntry style={styles.input} />
      <Button title="Login" onPress={login} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20 },
  input: { borderWidth: 1, marginVertical: 10, padding: 8, borderRadius: 5 },
});
