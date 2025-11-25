
import React, { useState, useRef, ReactNode } from 'react';

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
}

const Tooltip: React.FC<TooltipProps> = ({ content, children }) => {
  const [isVisible, setIsVisible] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          ref={tooltipRef}
          className="absolute z-10 w-64 p-2 -mt-1 text-sm text-white bg-gray-800 rounded-lg shadow-lg"
          style={{ bottom: '100%', left: '50%', transform: 'translateX(-50%)' }}
        >
          {content}
        </div>
      )}
    </div>
  );
};

export default Tooltip;
