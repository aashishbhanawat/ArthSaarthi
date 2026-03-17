import React, { ButtonHTMLAttributes } from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

interface LoadingButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading: boolean;
  loadingText?: string;
  children: React.ReactNode;
}

const LoadingButton: React.FC<LoadingButtonProps> = ({
  isLoading,
  loadingText,
  children,
  className = '',
  disabled,
  ...props
}) => {
  return (
    <button
      className={`flex items-center justify-center gap-2 ${className}`}
      disabled={isLoading || disabled}
      {...props}
    >
      {isLoading && <ArrowPathIcon className="h-4 w-4 animate-spin" />}
      {isLoading && loadingText ? loadingText : children}
    </button>
  );
};

export default LoadingButton;