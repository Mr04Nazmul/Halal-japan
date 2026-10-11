// Two installable variants; ads SDK is intentionally not enabled without a valid
// Interstitial Ad Unit ID and matching AdMob App ID for this Android app.
const withAds = process.env.HALAL_VARIANT === 'ads';
const admobAppId = process.env.HALAL_ADMOB_APP_ID || 'ca-app-pub-3940256099942544~3347511713'; // Google test app ID
module.exports = {
  expo: {
    name: withAds ? 'Japan Halal Checker Ads' : 'Japan Halal Checker',
    slug: 'japan-halal-checker',
    version: '1.0.0',
    orientation: 'portrait',
    userInterfaceStyle: 'light',
    android: {
      package: withAds ? 'com.nazmul.japanhalalchecker.ads' : 'com.nazmul.japanhalalchecker',
      permissions: ['CAMERA'],
      versionCode: 1
    },
    extra: { productApiBaseUrl: process.env.HALAL_PRODUCT_API_BASE_URL || 'https://vjygltfnrmyghlwyjtwu.supabase.co/functions/v1/halal-product-lookup', backendAnonKey: process.env.HALAL_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqeWdsdGZucm15Z2hsd3lqdHd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTEyNDI1NDEsImV4cCI6MjEwNjgxODU0MX0.nwq8t1ybnwBFIYNmc1h8tbIbCGUE9FZMQErPLD3ECdQ', buildVariant: withAds ? 'ads-test' : 'adfree', eas: { projectId: 'cdaa84da-4b3b-456e-958b-baa4bc58c5f7' } },
    owner: 'money-wallet',
    // Native module is autolinked in both builds; a valid test App ID avoids startup crashes.
    // Ad-free variant never requests or displays ads.
    plugins: [['react-native-google-mobile-ads', { androidAppId: admobAppId }]]
  }
};
