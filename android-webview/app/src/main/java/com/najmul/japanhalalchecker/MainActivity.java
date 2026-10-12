package com.najmul.japanhalalchecker;

import android.Manifest;
import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;
import android.webkit.PermissionRequest;
import android.webkit.GeolocationPermissions;
import android.webkit.ValueCallback;
import android.webkit.WebSettings;
import android.net.Uri;
import android.view.View;
import android.widget.TextView;
import android.widget.LinearLayout;
import android.widget.Button;
import android.graphics.Color;
import android.os.Build;

public class MainActivity extends Activity {
  private static final String HOME = "https://japan-halal-checker-najmul.floot.app/";
  private static final String TRUSTED = "japan-halal-checker-najmul.floot.app";
  private static final int FILE_PICK = 15;
  private static final int PERMISSION_REQUEST = 16;
  private WebView web;
  private ValueCallback<Uri[]> selectedFiles;
  private PermissionRequest cameraRequest;
  private GeolocationPermissions.Callback locationCallback;
  private String locationOrigin;

  @Override public void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    web = new WebView(this);
    web.setBackgroundColor(Color.rgb(8, 22, 18));
    setContentView(web);
    WebSettings settings = web.getSettings();
    settings.setJavaScriptEnabled(true);
    settings.setDomStorageEnabled(true);
    settings.setMediaPlaybackRequiresUserGesture(false);
    settings.setAllowFileAccess(false);
    settings.setAllowContentAccess(true);
    settings.setGeolocationEnabled(true);
    web.setWebViewClient(new WebViewClient() {
      @Override public boolean shouldOverrideUrlLoading(WebView view, android.webkit.WebResourceRequest request) {
        Uri uri = request.getUrl();
        if ("https".equals(uri.getScheme()) && TRUSTED.equals(uri.getHost())) return false;
        try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); } catch (Exception ignored) {}
        return true;
      }
      @Override public void onReceivedError(WebView view, android.webkit.WebResourceRequest request, android.webkit.WebResourceError error) {
        if (request.isForMainFrame()) showOffline();
      }
    });
    web.setWebChromeClient(new WebChromeClient() {
      @Override public void onPermissionRequest(PermissionRequest req) {
        runOnUiThread(() -> {
          Uri origin = Uri.parse(req.getOrigin().toString());
          if (!TRUSTED.equals(origin.getHost()) || !"https".equals(origin.getScheme())) { req.deny(); return; }
          boolean video = false;
          for (String r : req.getResources()) if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(r)) video = true;
          if (!video) { req.deny(); return; }
          if (checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            req.grant(new String[]{ PermissionRequest.RESOURCE_VIDEO_CAPTURE });
          } else {
            cameraRequest = req;
            requestPermissions(new String[]{Manifest.permission.CAMERA}, PERMISSION_REQUEST);
          }
        });
      }
      @Override public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
        Uri uri = Uri.parse(origin);
        if (!"https".equals(uri.getScheme()) || !TRUSTED.equals(uri.getHost())) {callback.invoke(origin,false,false);return;}
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
            checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
          callback.invoke(origin,true,false);
        } else {
          locationCallback = callback;
          locationOrigin = origin;
          requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION}, PERMISSION_REQUEST);
        }
      }
      @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
        if (selectedFiles != null) selectedFiles.onReceiveValue(null);
        selectedFiles = callback;
        try {
          Intent intent = params.createIntent();
          startActivityForResult(intent, FILE_PICK);
          return true;
        } catch (Exception e) { selectedFiles = null; return false; }
      }
    });
    web.loadUrl(HOME);
  }
  private void showOffline() {
    LinearLayout layout = new LinearLayout(this);
    layout.setOrientation(LinearLayout.VERTICAL);
    layout.setPadding(36, 80, 36, 36);
    layout.setBackgroundColor(Color.rgb(9, 34, 26));
    TextView message = new TextView(this);
    message.setText("Japan Halal Checker\\n\\nInternet connection is required.");
    message.setTextColor(Color.WHITE);
    message.setTextSize(20);
    Button retry = new Button(this);
    retry.setText("Retry");
    retry.setOnClickListener(v -> { setContentView(web); web.loadUrl(HOME); });
    layout.addView(message);
    layout.addView(retry);
    setContentView(layout);
  }
  @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grants) {
    super.onRequestPermissionsResult(requestCode, permissions, grants);
    if (requestCode != PERMISSION_REQUEST) return;
    if (cameraRequest != null) {
      PermissionRequest req=cameraRequest; cameraRequest=null;
      if (checkSelfPermission(Manifest.permission.CAMERA)==PackageManager.PERMISSION_GRANTED) req.grant(new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE});
      else req.deny();
    }
    if (locationCallback != null) {
      boolean allowed=checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED;
      locationCallback.invoke(locationOrigin,allowed,false);
      locationCallback=null; locationOrigin=null;
    }
  }
  @Override protected void onActivityResult(int requestCode,int resultCode,Intent data) {
    super.onActivityResult(requestCode,resultCode,data);
    if(requestCode==FILE_PICK && selectedFiles!=null){
      selectedFiles.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(resultCode,data));
      selectedFiles=null;
    }
  }
  @Override public void onBackPressed() {
    if(web.canGoBack()) web.goBack(); else super.onBackPressed();
  }
  @Override protected void onDestroy() {
    if(cameraRequest!=null){cameraRequest.deny();cameraRequest=null;}
    if(selectedFiles!=null){selectedFiles.onReceiveValue(null);selectedFiles=null;}
    web.destroy();super.onDestroy();
  }
}
