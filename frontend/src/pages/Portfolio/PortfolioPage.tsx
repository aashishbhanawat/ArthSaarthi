import React, { useState } from 'react';
import { usePortfolios } from '../../hooks/usePortfolios';
import PortfolioList from '../../components/Portfolio/PortfolioList';
import CreatePortfolioModal from '../../components/Portfolio/CreatePortfolioModal';

const PortfolioPage: React.FC = () => {
  const { data: portfolios, isLoading, isError, error } = usePortfolios();
  const [isModalOpen, setModalOpen] = useState(false);

  if (isLoading) return <div className="text-center p-8">Loading portfolios...</div>;
  if (isError) return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Portfolios</h1>
        <button onClick={() => setModalOpen(true)} className="btn btn-primary">
          Create New Portfolio
        </button>
      </div>

      <PortfolioList portfolios={portfolios || []} />

      <CreatePortfolioModal
        isOpen={isModalOpen}
        onClose={() => setModalOpen(false)}
      />
    </div>
  );
};

export default PortfolioPage;