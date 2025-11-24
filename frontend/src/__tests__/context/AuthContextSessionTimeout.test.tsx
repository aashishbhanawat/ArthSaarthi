import { render, screen, act } from '@testing-library/react';
import { AuthProvider } from '../../context/AuthContext';

// Mock api
jest.mock('../../services/api', () => ({
  defaults: { headers: { common: {} } },
  interceptors: { response: { use: jest.fn(), eject: jest.fn() } },
  get: jest.fn(),
}));

describe('Issue 122 Fix Verification: Session Timeout Modal on Login Page', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    localStorage.clear();
    sessionStorage.clear();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('does NOT show the session timeout modal when not logged in', () => {
    // Default timeout in AuthContext is 30 minutes if env var is not set
    const THIRTY_MINUTES = 30 * 60 * 1000;

    render(
      <AuthProvider>
        <div>Login Page Content</div>
      </AuthProvider>
    );

    // Initial state: Modal should not be visible
    expect(screen.queryByText(/Session Timeout/i)).not.toBeInTheDocument();

    // Fast-forward time past the timeout
    act(() => {
      jest.advanceTimersByTime(THIRTY_MINUTES + 1000);
    });

    // Verification: Modal should still NOT be visible
    expect(screen.queryByText(/Session Timeout/i)).not.toBeInTheDocument();
  });
});
