import { useState, useEffect, useCallback } from 'react';

const useIdleTimer = (timeout: number, onIdle: () => void, enabled: boolean = true) => {
  const [isIdle, setIsIdle] = useState(false);

  const handleIdle = useCallback(() => {
    setIsIdle(true);
    onIdle();
  }, [onIdle]);

  const resetTimer = useCallback(() => {
    setIsIdle(false);
  }, []);

  useEffect(() => {
    if (!enabled) {
      setIsIdle(false);
      return;
    }

    let timer: NodeJS.Timeout;

    const handleUserActivity = () => {
      resetTimer();
      clearTimeout(timer);
      timer = setTimeout(handleIdle, timeout);
    };

    window.addEventListener('mousemove', handleUserActivity);
    window.addEventListener('keydown', handleUserActivity);
    window.addEventListener('click', handleUserActivity);

    timer = setTimeout(handleIdle, timeout);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('mousemove', handleUserActivity);
      window.removeEventListener('keydown', handleUserActivity);
      window.removeEventListener('click', handleUserActivity);
    };
  }, [timeout, handleIdle, resetTimer, enabled]);

  return isIdle;
};

export default useIdleTimer;
