/* eslint-disable testing-library/no-node-access */
import { render, screen, act } from '@testing-library/react';
import { PrivacyProvider, usePrivacy } from '../../context/PrivacyContext';
import React from 'react';

const TestComponent = () => {
  const { isPrivacyMode, togglePrivacyMode } = usePrivacy();
  return (
    <div>
      <span data-testid="privacy-mode">{isPrivacyMode.toString()}</span>
      <button onClick={togglePrivacyMode}>Toggle</button>
    </div>
  );
};

describe('PrivacyContext', () => {
  afterEach(() => {
    localStorage.clear();
  });

  it('should initialize with privacy mode off by default', () => {
    render(
      <PrivacyProvider>
        <TestComponent />
      </PrivacyProvider>
    );
    expect(screen.getByTestId('privacy-mode')).toHaveTextContent(/^false$/);
  });

  it('should initialize with the value from localStorage if present', () => {
    localStorage.setItem('privacyMode', 'true');
    render(
      <PrivacyProvider>
        <TestComponent />
      </PrivacyProvider>
    );
    expect(screen.getByTestId('privacy-mode')).toHaveTextContent(/^true$/);
  });

  it('should toggle privacy mode and update localStorage', () => {
    render(
      <PrivacyProvider>
        <TestComponent />
      </PrivacyProvider>
    );

    const toggleButton = screen.getByText('Toggle');

    // Initial state
    expect(screen.getByTestId('privacy-mode')).toHaveTextContent(/^false$/);
    expect(localStorage.getItem('privacyMode')).toBe('false');

    // Toggle on
    act(() => {
      toggleButton.click();
    });
    expect(screen.getByTestId('privacy-mode')).toHaveTextContent(/^true$/);
    expect(localStorage.getItem('privacyMode')).toBe('true');

    // Toggle off
    act(() => {
      toggleButton.click();
    });
    expect(screen.getByTestId('privacy-mode')).toHaveTextContent(/^false$/);
    expect(localStorage.getItem('privacyMode')).toBe('false');
  });
});
