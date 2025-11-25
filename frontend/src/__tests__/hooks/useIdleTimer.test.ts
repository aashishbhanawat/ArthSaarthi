import { renderHook, act } from '@testing-library/react';
import useIdleTimer from '../../hooks/useIdleTimer';

describe('useIdleTimer', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should call onIdle after the specified timeout', () => {
    const onIdle = jest.fn();
    const timeout = 1000;

    renderHook(() => useIdleTimer(timeout, onIdle));

    expect(onIdle).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(timeout);
    });

    expect(onIdle).toHaveBeenCalledTimes(1);
  });

  it('should reset the timer on user activity', () => {
    const onIdle = jest.fn();
    const timeout = 1000;

    renderHook(() => useIdleTimer(timeout, onIdle));

    act(() => {
      jest.advanceTimersByTime(timeout / 2);
    });

    expect(onIdle).not.toHaveBeenCalled();

    act(() => {
      window.dispatchEvent(new MouseEvent('mousemove'));
    });

    act(() => {
      jest.advanceTimersByTime(timeout / 2);
    });

    expect(onIdle).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(timeout / 2);
    });

    expect(onIdle).toHaveBeenCalledTimes(1);
  });

  it('should not call onIdle if disabled', () => {
    const onIdle = jest.fn();
    const timeout = 1000;

    renderHook(() => useIdleTimer(timeout, onIdle, false));

    act(() => {
      jest.advanceTimersByTime(timeout + 100);
    });

    expect(onIdle).not.toHaveBeenCalled();
  });

  it('should stop timer when disabled dynamically', () => {
    const onIdle = jest.fn();
    const timeout = 1000;

    const { rerender } = renderHook(({ enabled }) => useIdleTimer(timeout, onIdle, enabled), {
      initialProps: { enabled: true },
    });

    // Advance halfway
    act(() => {
      jest.advanceTimersByTime(timeout / 2);
    });

    // Disable it
    rerender({ enabled: false });

    // Advance remaining time plus some buffer
    act(() => {
      jest.advanceTimersByTime(timeout);
    });

    expect(onIdle).not.toHaveBeenCalled();
  });
});
