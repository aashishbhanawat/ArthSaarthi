import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.arthsaarthi.app',
  appName: 'ArthSaarthi',
  webDir: 'dist',
  // On Android, the React app loads from the local assets (file://)
  // and communicates with the Python backend on 127.0.0.1:<port>.
  // The actual port is provided dynamically by the native plugin.
  server: {
    // Allow mixed content (file:// loading assets that call http://127.0.0.1)
    androidScheme: 'http',
    // Allow navigation to the local backend
    allowNavigation: ['127.0.0.1'],
  },
  android: {
    // Allow cleartext traffic to localhost (for the embedded backend)
    allowMixedContent: true,
  },
  plugins: {
    // No default Capacitor plugins needed — we use a custom one
    // for the Python backend bridge.
  },
};

export default config;
