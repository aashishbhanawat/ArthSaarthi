export { };

declare global {
  interface Window {
    electronAPI?: {
      getApiConfig: () => Promise<{ host: string; port: number }>;
      openUserGuide: (sectionId?: string) => Promise<void>;
      // Update notification API
      checkForUpdates: () => Promise<{
        available: boolean;
        version?: string;
        url?: string;
        name?: string;
        error?: string;
      }>;
      openReleasePage: (url: string) => Promise<void>;
      getAppVersion: () => Promise<string>;
    };
  }
}
