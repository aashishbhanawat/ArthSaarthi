import React, { createContext, useState, useContext, useEffect, useMemo, ReactNode } from 'react';

// Define the shape of the context state
interface PrivacyContextState {
  isPrivacyMode: boolean;
  togglePrivacyMode: () => void;
}

// Create the context with a default value
const PrivacyContext = createContext<PrivacyContextState | undefined>(undefined);

// Define the props for the provider
interface PrivacyProviderProps {
  children: ReactNode;
}

// Create the provider component
export const PrivacyProvider: React.FC<PrivacyProviderProps> = ({ children }) => {
  const [isPrivacyMode, setIsPrivacyMode] = useState<boolean>(() => {
    try {
      const item = window.localStorage.getItem('privacyMode');
      return item ? JSON.parse(item) : false;
    } catch (error) {
      console.error("Error reading from localStorage", error);
      return false;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem('privacyMode', JSON.stringify(isPrivacyMode));
    } catch (error) {
      console.error("Error writing to localStorage", error);
    }
  }, [isPrivacyMode]);

  const togglePrivacyMode = () => {
    setIsPrivacyMode(prevMode => !prevMode);
  };

  const contextValue = useMemo(() => ({
    isPrivacyMode,
    togglePrivacyMode,
  }), [isPrivacyMode]);

  return (
    <PrivacyContext.Provider value={contextValue}>
      {children}
    </PrivacyContext.Provider>
  );
};

// Create a custom hook to use the privacy context
// eslint-disable-next-line react-refresh/only-export-components
export const usePrivacy = (): PrivacyContextState => {
  const context = useContext(PrivacyContext);
  if (context === undefined) {
    throw new Error('usePrivacy must be used within a PrivacyProvider');
  }
  return context;
};
