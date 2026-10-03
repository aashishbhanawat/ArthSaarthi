import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { BrokerApiSyncCard } from '../../../components/import/BrokerApiSyncCard';
import * as brokerApi from '../../../services/brokerApi';

jest.mock('../../../services/brokerApi');

const mockGetBrokerCredentials = brokerApi.getBrokerCredentials as jest.Mock;

describe('BrokerApiSyncCard', () => {
  const portfolios = [
    { id: 'p1', name: 'Retirement Portfolio' },
    { id: 'p2', name: 'Trading Portfolio' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders card title, provider options, and unconfigured state', async () => {
    mockGetBrokerCredentials.mockResolvedValue([]);

    render(
      <MemoryRouter>
        <BrokerApiSyncCard portfolios={portfolios} isLoadingPortfolios={false} />
      </MemoryRouter>
    );

    expect(screen.getByText('Direct Broker API Sync (NFR12)')).toBeInTheDocument();
    expect(screen.getByText('Zerodha Kite API')).toBeInTheDocument();
    expect(screen.getByText('ICICI Breeze API')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Not Configured')).toBeInTheDocument();
    });
  });

  it('renders connected state when active authenticated credentials exist', async () => {
    mockGetBrokerCredentials.mockResolvedValue([
      {
        id: 'c1',
        provider_name: 'zerodha_kite',
        api_key: 'key1',
        is_active: true,
        is_authenticated: true,
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      },
    ]);

    render(
      <MemoryRouter>
        <BrokerApiSyncCard portfolios={portfolios} isLoadingPortfolios={false} />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });
});
