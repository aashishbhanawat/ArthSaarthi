import React from 'react';
import { render, screen } from '@testing-library/react';
import AddAssetToWatchlistModal from '../../../components/modals/AddAssetToWatchlistModal';

describe('AddAssetToWatchlistModal', () => {
    it('renders the modal when it is open', () => {
        render(<AddAssetToWatchlistModal isOpen={true} onClose={() => {}} watchlistId="123" />);
        expect(screen.getByText('Add Asset to Watchlist')).toBeInTheDocument();
    });

    it('does not render the modal when it is closed', () => {
        render(<AddAssetToWatchlistModal isOpen={false} onClose={() => {}} watchlistId="123" />);
        expect(screen.queryByText('Add Asset to Watchlist')).not.toBeInTheDocument();
    });
});
