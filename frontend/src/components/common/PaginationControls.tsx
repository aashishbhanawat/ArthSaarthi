import React from 'react';

interface PaginationControlsProps {
  currentPage: number;
  pageCount: number;
  onPageChange: (newPage: number) => void;
}

const PaginationControls: React.FC<PaginationControlsProps> = ({
  currentPage,
  pageCount,
  onPageChange,
}) => {
  if (pageCount <= 1) {
    return null; // Don't render pagination if there's only one page
  }

  const handlePrevious = () => {
    onPageChange(Math.max(0, currentPage - 1));
  };

  const handleNext = () => {
    onPageChange(Math.min(pageCount - 1, currentPage + 1));
  };

  return (
    <div className="flex justify-end items-center space-x-4 mt-4">
      <span className="text-sm text-gray-600">
        Page {currentPage + 1} of {pageCount}
      </span>
      <button onClick={handlePrevious} disabled={currentPage === 0} className="btn btn-secondary btn-sm disabled:opacity-50 disabled:cursor-not-allowed">Previous</button>
      <button onClick={handleNext} disabled={currentPage >= pageCount - 1} className="btn btn-secondary btn-sm disabled:opacity-50 disabled:cursor-not-allowed">Next</button>
    </div>
  );
};

export default PaginationControls;