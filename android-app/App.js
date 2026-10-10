import React, { useState } from 'react';
import { SafeAreaView, View, Text, Pressable, ActivityIndicator, StyleSheet, StatusBar, BackHandler } from 'react-native';
import { WebView } from 'react-native-webview';

// The website owns the scanner and ingredient-checking logic.
// This shell does not independently certify products or guarantee camera access.
const APP_URL = 'https://mr04nazmul.github.io/Halal-japan/';
export default function App() {
  const [failed, setFailed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [retryKey, setRetryKey] = useState(0);
  return <SafeAreaView style={s.root}>
    <StatusBar backgroundColor="#0c382b" barStyle="light-content" />
    {failed ? <View style={s.center}>
      <Text style={s.title}>Connection unavailable</Text>
      <Text style={s.message}>Check your internet connection and try again.</Text>
      <Pressable accessibilityRole="button" style={s.button} onPress={() => { setFailed(false); setLoading(true); setRetryKey(k => k + 1); }}>
        <Text style={s.buttonText}>Retry</Text>
      </Pressable>
    </View> : <WebView
      key={retryKey}
      source={{ uri: APP_URL }}
      originWhitelist={['https://*']}
      javaScriptEnabled
      domStorageEnabled
      mediaPlaybackRequiresUserAction
      allowsInlineMediaPlayback
      onError={() => { setFailed(true); setLoading(false); }}
      onHttpError={e => { if (e.nativeEvent.statusCode >= 500) setFailed(true); }}
      onLoadEnd={() => setLoading(false)}
      onLoadStart={() => setLoading(true)}
      style={s.web}
    />}
    {loading && !failed && <View style={s.loader}><ActivityIndicator color="#0c382b" size="large" /></View>}
  </SafeAreaView>;
}
const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#f4f8f3' },
  web: { flex: 1 },
  loader: { position: 'absolute', top: 0, bottom: 0, left: 0, right: 0, alignItems: 'center', justifyContent: 'center', backgroundColor: '#f4f8f3' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 30 },
  title: { fontSize: 22, fontWeight: '700', color: '#0c382b' },
  message: { textAlign: 'center', marginTop: 12, color: '#52645a' },
  button: { backgroundColor: '#0c382b', borderRadius: 12, paddingVertical: 13, paddingHorizontal: 25, marginTop: 20 },
  buttonText: { color: 'white', fontWeight: '700' }
});