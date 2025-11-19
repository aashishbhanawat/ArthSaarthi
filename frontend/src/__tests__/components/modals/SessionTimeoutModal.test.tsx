import { render, fireEvent, act, screen } from '@testing-library/react';
import SessionTimeoutModal from '../../../components/modals/SessionTimeoutModal';

describe('SessionTimeoutModal', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should not render when isOpen is false', () => {
    render(
      <SessionTimeoutModal isOpen={false} onClose={jest.fn()} onLogout={jest.fn()} />
    );
    expect(screen.queryByText('Session Timeout')).not.toBeInTheDocument();
  });

  it('should render when isOpen is true', () => {
    render(
      <SessionTimeoutModal isOpen={true} onClose={jest.fn()} onLogout={jest.fn()} />
    );
    expect(screen.getByText('Session Timeout')).toBeInTheDocument();
  });

  it('should display a countdown timer', () => {
    render(
      <SessionTimeoutModal isOpen={true} onClose={jest.fn()} onLogout={jest.fn()} />
    );
    expect(screen.getByText('You will be logged out in 120 seconds due to inactivity.')).toBeInTheDocument();

    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(screen.getByText('You will be logged out in 119 seconds due to inactivity.')).toBeInTheDocument();
  });

  it('should call onLogout when the countdown timer reaches zero', () => {
    const onLogout = jest.fn();
    render(<SessionTimeoutModal isOpen={true} onClose={jest.fn()} onLogout={onLogout} />);

    act(() => {
      jest.advanceTimersByTime(120000);
    });

    expect(onLogout).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when the "Stay Logged In" button is clicked', () => {
    const onClose = jest.fn();
    render(
      <SessionTimeoutModal isOpen={true} onClose={onClose} onLogout={jest.fn()} />
    );

    fireEvent.click(screen.getByText('Stay Logged In'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('should call onLogout when the "Logout" button is clicked', () => {
    const onLogout = jest.fn();
    render(
      <SessionTimeoutModal isOpen={true} onClose={jest.fn()} onLogout={onLogout} />
    );

    fireEvent.click(screen.getByText('Logout'));
    expect(onLogout).toHaveBeenCalledTimes(1);
  });
});
