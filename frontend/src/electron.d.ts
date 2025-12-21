export { };

declare global {
  interface Window {
    electronAPI?: {
      getApiConfig: () => Promise<{ host: string; port: number }>;
      openUserGuide: (sectionId?: string) => Promise<void>;
    };
  }
}
