// Two installable variants; ads SDK is intentionally not enabled without a valid
// Interstitial Ad Unit ID and matching AdMob App ID for this Android app.
const withAds = process.env.HALAL_VARIANT === 'ads';
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
    extra: { buildVariant: withAds ? 'ads-pending-integration' : 'adfree' },
    plugins: []
  }
};
