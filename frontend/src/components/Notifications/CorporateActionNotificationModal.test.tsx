import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { CorporateActionNotificationModal } from './CorporateActionNotificationModal';
import * as corporateActionsApi from '../../services/corporateActionsApi';
import { CorporateActionEventListResponse } from '../../types/corporateActions';

jest.mock('../../services/corporateActionsApi');
const mockedApi = corporateActionsApi as jest.Mocked<typeof corporateActionsApi>;

const mockResponse: CorporateActionEventListResponse = {
  total: 2,
  unread_count: 2,
  items: [
    {
      id: 'event-1',
      user_id: 'user-1',
      portfolio_id: 'port-1',
      asset_id: 'asset-1',
      transaction_id: 'tx-1',
      event_type: 'BOND_COUPON',
      event_date: '2026-11-08',
      units: 20,
      amount: 1500,
      status: 'NEW',
      details: { bond_name: '7.5% Sovereign Bond 2026' },
      created_at: '2026-11-08T00:15:00Z',
      bond_name: '7.5% Sovereign Bond 2026',
      isin: 'IN0020200001',
    },
    {
      id: 'event-2',
      user_id: 'user-1',
      portfolio_id: 'port-1',
      asset_id: 'asset-2',
      transaction_id: 'tx-2',
      event_type: 'BOND_MATURITY',
      event_date: '2026-11-08',
      units: 10,
      amount: 10000,
      status: 'NEW',
      details: { bond_name: 'NHAI 8.2% Tax Free Bond' },
      created_at: '2026-11-08T00:15:00Z',
      bond_name: 'NHAI 8.2% Tax Free Bond',
      isin: 'IN0030300002',
    },
  ],
};

describe('CorporateActionNotificationModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading and then event receipts when open', async () => {
    mockedApi.getCorporateActionEvents.mockResolvedValue(mockResponse);

    render(
      <CorporateActionNotificationModal
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    expect(await screen.findByText('Automated Activity')).toBeInTheDocument();
    expect(screen.getByText('7.5% Sovereign Bond 2026')).toBeInTheDocument();
    expect(screen.getByText('NHAI 8.2% Tax Free Bond')).toBeInTheDocument();
    expect(screen.getByText('Coupon Payout')).toBeInTheDocument();
    expect(screen.getByText('Maturity Redemption')).toBeInTheDocument();
  });

  it('renders empty state when there are no receipts', async () => {
    mockedApi.getCorporateActionEvents.mockResolvedValue({
      total: 0,
      unread_count: 0,
      items: [],
    });

    render(
      <CorporateActionNotificationModal
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    expect(await screen.findByText('No automated receipts recorded')).toBeInTheDocument();
  });

  it('dismisses single event on clicking dismiss', async () => {
    mockedApi.getCorporateActionEvents.mockResolvedValue(mockResponse);
    mockedApi.dismissCorporateActionEvent.mockResolvedValue({
      ...mockResponse.items[0],
      status: 'DISMISSED',
    });

    const onCountChange = jest.fn();
    render(
      <CorporateActionNotificationModal
        isOpen={true}
        onClose={jest.fn()}
        onCountChange={onCountChange}
      />
    );

    const dismissButtons = await screen.findAllByText('Dismiss');
    fireEvent.click(dismissButtons[0]);

    await waitFor(() => {
      expect(mockedApi.dismissCorporateActionEvent).toHaveBeenCalledWith('event-1');
    });
    expect(onCountChange).toHaveBeenCalledWith(1);
  });

  it('dismisses all events on clicking Dismiss All', async () => {
    mockedApi.getCorporateActionEvents.mockResolvedValue(mockResponse);
    mockedApi.dismissAllCorporateActionEvents.mockResolvedValue({
      message: 'Dismissed 2',
      dismissed_count: 2,
    });

    const onCountChange = jest.fn();
    render(
      <CorporateActionNotificationModal
        isOpen={true}
        onClose={jest.fn()}
        onCountChange={onCountChange}
      />
    );

    const dismissAllBtn = await screen.findByText('Dismiss All');
    fireEvent.click(dismissAllBtn);

    await waitFor(() => {
      expect(mockedApi.dismissAllCorporateActionEvents).toHaveBeenCalled();
    });
    expect(onCountChange).toHaveBeenCalledWith(0);
  });
});
