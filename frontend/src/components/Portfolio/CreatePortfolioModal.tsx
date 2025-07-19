import React, { useState, useEffect } from 'react';
import { useCreatePortfolio } from '../../hooks/usePortfolios';

interface CreatePortfolioModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const CreatePortfolioModal: React.FC<CreatePortfolioModalProps> = ({ isOpen, onClose }) => {
    const [name, setName] = useState('');
    const createPortfolioMutation = useCreatePortfolio();

    useEffect(() => {
        if (createPortfolioMutation.isSuccess) {
            onClose();
            createPortfolioMutation.reset();
            setName('');
        }
    }, [createPortfolioMutation.isSuccess, onClose, createPortfolioMutation]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (name.trim()) {
            createPortfolioMutation.mutate({ name });
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-content max-w-md">
                <div className="modal-header">
                    <h2 className="text-2xl font-bold">Create New Portfolio</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
                </div>
                <div className="p-6">
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label htmlFor="portfolio-name" className="form-label">
                                Portfolio Name
                            </label>
                            <input
                                id="portfolio-name"
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="form-input"
                                required
                            />
                        </div>
                        {createPortfolioMutation.isError && (
                            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                                <span className="block sm:inline">Error: An unexpected error occurred.</span>
                            </div>
                        )}
                        <div className="flex items-center justify-end pt-4">
                            <button type="button" onClick={onClose} className="btn btn-secondary mr-2" disabled={createPortfolioMutation.isPending} >
                                Cancel
                            </button>
                            <button type="submit" className="btn btn-primary" disabled={createPortfolioMutation.isPending} >
                                {createPortfolioMutation.isPending ? 'Creating...' : 'Create'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default CreatePortfolioModal;
