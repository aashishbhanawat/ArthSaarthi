import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AssetLinkModal from '../../../components/modals/AssetLinkModal';
import { Goal } from '../../../types/goal';
import * as usePortfoliosHooks from '../../../hooks/usePortfolios';
import * as useAssetsHooks from '../../../hooks/useAssets';
import { Portfolio } from '../../../types/portfolio';
import { Asset } from '../../../types/asset';

jest.mock('../../../hooks/usePortfolios');
jest.mock('../../../hooks/useAssets');

const mockUsePortfolios = usePortfoliosHooks.usePortfolios as jest.Mock;
const mockUseAssetSearch = useAssetsHooks.useAssetSearch as jest.Mock;

const queryClient = new QueryClient();

const renderWithClient = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

const mockGoal: Goal = { id: '1', name: 'Buy a car', target_amount: 25000, target_date: '2025-12-31', user_id: 'user1', links: [] };
const mockPortfolios: Portfolio[] = [{ id: 'p1', name: 'My Portfolio', user_id: 'user1', description: '', transactions: [] }];
const mockAssets: Asset[] = [{ id: 'a1', name: 'Apple Inc.', ticker_symbol: 'AAPL', asset_type: 'STOCK', currency: 'USD', exchange: 'NASDAQ' }];

describe('AssetLinkModal', () => {
    const onLink = jest.fn();
    const onClose = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
        mockUsePortfolios.mockReturnValue({ data: mockPortfolios, isLoading: false, error: null });
        mockUseAssetSearch.mockReturnValue({ data: mockAssets, isLoading: false, error: null });
    });

    it('renders correctly and shows portfolios by default', () => {
        renderWithClient(<AssetLinkModal isOpen={true} onClose={onClose} onLink={onLink} goal={mockGoal} />);
        expect(screen.getByText('Link Item to "Buy a car"')).toBeInTheDocument();
        expect(screen.getByText('My Portfolio')).toBeInTheDocument();
    });

    it('searches for assets when search term is entered', async () => {
        renderWithClient(<AssetLinkModal isOpen={true} onClose={onClose} onLink={onLink} goal={mockGoal} />);
        fireEvent.change(screen.getByPlaceholderText('Type to search for assets...'), { target: { value: 'AAPL' } });
        await waitFor(() => {
            expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
        });
    });

    it('calls onLink with portfolio_id when a portfolio is linked', () => {
        renderWithClient(<AssetLinkModal isOpen={true} onClose={onClose} onLink={onLink} goal={mockGoal} />);
        fireEvent.click(screen.getAllByRole('button', { name: 'Link' })[0]); // Use getAllByRole since text is generic
        expect(onLink).toHaveBeenCalledWith({ portfolio_id: 'p1' });
        expect(onClose).toHaveBeenCalled();
    });

    it('calls onLink with asset_id when an asset is linked', async () => {
        renderWithClient(<AssetLinkModal isOpen={true} onClose={onClose} onLink={onLink} goal={mockGoal} />);
        fireEvent.change(screen.getByPlaceholderText('Type to search for assets...'), { target: { value: 'AAPL' } });
        await waitFor(() => {
            expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
        });
        fireEvent.click(screen.getByRole('button', { name: 'Link' }));
        expect(onLink).toHaveBeenCalledWith({ asset_id: 'a1' });
        expect(onClose).toHaveBeenCalled();
    });
});
