import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as dashboardApi from '../../services/dashboardApi';
import {
    useDashboardSummary,
    useDashboardHistory,
    useDashboardAllocation,
} from '../../hooks/useDashboard';
import {
    DashboardSummary,
    PortfolioHistoryResponse,
    AssetAllocationResponse,
} from '../../types/dashboard';

// Mock the API module
jest.mock('../../services/dashboardApi');

const mockedDashboardApi = dashboardApi as jest.Mocked<typeof dashboardApi>;

const createTestQueryClient = () =>
    new QueryClient({
        defaultOptions: {
            queries: {
                retry: false, // Turn off retries for testing
            },
        },
    });

const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={createTestQueryClient()}>{children}</QueryClientProvider>
);

describe('Dashboard Hooks', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('useDashboardSummary', () => {
        it('should return dashboard summary data on success', async () => {
            const mockSummary: DashboardSummary = {
                total_value: 10000,
                total_unrealized_pnl: 500,
                total_realized_pnl: 200,
                top_movers: [],
                asset_allocation: [],
            };
            mockedDashboardApi.getDashboardSummary.mockResolvedValue(mockSummary);

            const { result } = renderHook(() => useDashboardSummary(), { wrapper });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));
            expect(result.current.data).toEqual(mockSummary);
        });
    });

    describe('useDashboardHistory', () => {
        it('should return portfolio history data on success', async () => {
            const mockHistory: PortfolioHistoryResponse = {
                history: [{ date: '2023-01-01', value: 1000 }],
            };
            mockedDashboardApi.getDashboardHistory.mockResolvedValue(mockHistory);

            const { result } = renderHook(() => useDashboardHistory('7d'), { wrapper });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));
            expect(result.current.data).toEqual(mockHistory);
            expect(mockedDashboardApi.getDashboardHistory).toHaveBeenCalledWith('7d');
        });

        it('should return an error when the history API call fails', async () => {
            const errorMessage = 'Failed to fetch history';
            mockedDashboardApi.getDashboardHistory.mockRejectedValue(new Error(errorMessage));

            const { result } = renderHook(() => useDashboardHistory('30d'), { wrapper });

            await waitFor(() => expect(result.current.isError).toBe(true));
            expect((result.current.error as Error).message).toBe(errorMessage);
        });
    });

    describe('useDashboardAllocation', () => {
        it('should return asset allocation data on success', async () => {
            const mockAllocation: AssetAllocationResponse = {
                allocation: [{ ticker: 'AAPL', value: 5000 }],
            };
            mockedDashboardApi.getDashboardAllocation.mockResolvedValue(mockAllocation);

            const { result } = renderHook(() => useDashboardAllocation(), { wrapper });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));
            expect(result.current.data).toEqual(mockAllocation);
            expect(mockedDashboardApi.getDashboardAllocation).toHaveBeenCalledTimes(1);
        });
    });
});

