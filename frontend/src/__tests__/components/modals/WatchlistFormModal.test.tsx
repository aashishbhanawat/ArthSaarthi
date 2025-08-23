import React from 'react';
import { render, screen } from '@testing-library/react';
import WatchlistFormModal from '../../../components/modals/WatchlistFormModal';

describe('WatchlistFormModal', () => {
    it('renders the modal when it is open', () => {
        render(<WatchlistFormModal isOpen={true} onClose={() => {}} />);
        expect(screen.getByText('Watchlist Form')).toBeInTheDocument();
    });

    it('does not render the modal when it is closed', () => {
        render(<WatchlistFormModal isOpen={false} onClose={() => {}} />);
        expect(screen.queryByText('Watchlist Form')).not.toBeInTheDocument();
    });
});
