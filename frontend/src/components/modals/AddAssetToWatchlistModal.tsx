import React from 'react';

interface Props {
    isOpen: boolean;
    onClose: () => void;
    watchlistId: string;
}

const AddAssetToWatchlistModal: React.FC<Props> = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center">
            <div className="bg-white p-4 rounded-lg">
                <h2 className="text-xl font-bold mb-4">Add Asset to Watchlist</h2>
                <p>Add asset to watchlist form is coming soon!</p>
                <button onClick={onClose} className="mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                    Close
                </button>
            </div>
        </div>
    );
};

export default AddAssetToWatchlistModal;
