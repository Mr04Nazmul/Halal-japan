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
    extra: { buildVariant: withAds ? 'ads-test' : 'adfree' },
    // Native module is autolinked in both builds; a valid test App ID avoids startup crashes.
    // Ad-free variant never requests or displays ads.
    plugins: [['react-native-google-mobile-ads', { androidAppId: admobAppId }]]
  }
};
