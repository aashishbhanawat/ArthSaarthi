import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { ResearchIntelligenceFeed } from './ResearchIntelligenceFeed';
import * as newsApi from '../../services/newsApi';
import { ResearchFeedResponse, ResearchFeedSummary } from '../../types/marketNews';

jest.mock('../../services/newsApi');
const mockedApi = newsApi as jest.Mocked<typeof newsApi>;

const mockFeedResponse: ResearchFeedResponse = {
  total: 3,
  symbols: ['RECLTD', 'TCS'],
  items: [
    {
      id: 'news-1',
      title: 'REC Limited signs major power financing pact',
      summary: 'REC has signed an MoU to finance green energy projects.',
      url: 'https://example.com/rec-mou',
      source: 'Moneycontrol',
      category: 'NEWS',
      published_at: new Date(Date.now() - 3600000).toISOString(),
      symbols: ['RECLTD'],
      sentiment: 'POSITIVE',
      created_at: new Date().toISOString(),
    },
    {
      id: 'broker-1',
      title: 'Buy REC; target of Rs 600: Motilal Oswal',
      summary: 'Brokerage house recommends Buy.',
      url: 'https://example.com/rec-broker',
      source: 'Moneycontrol Research',
      category: 'BROKER_REPORT',
      published_at: new Date(Date.now() - 7200000).toISOString(),
      symbols: ['RECLTD'],
      sentiment: 'POSITIVE',
      metadata_json: {
        broker: 'Motilal Oswal',
        target_price: 600,
        recommendation: 'BUY',
      },
      created_at: new Date().toISOString(),
    },
    {
      id: 'concall-1',
      title: 'TCS Q2 FY25 Earnings Call Podcast',
      summary: 'Concall transcript and audio highlights.',
      url: 'https://example.com/tcs-concall',
      source: 'Trendlyne Concalls',
      category: 'CONCALL',
      published_at: new Date(Date.now() - 14400000).toISOString(),
      symbols: ['TCS'],
      sentiment: 'NEUTRAL',
      metadata_json: {
        quarter: 'Q2 FY25',
        audio_url: 'https://example.com/audio.mp3',
      },
      created_at: new Date().toISOString(),
    },
  ],
};

const mockSummaryResponse: ResearchFeedSummary = {
  news_count: 1,
  broker_reports_count: 1,
  concalls_count: 1,
  results_count: 0,
  latest_items: mockFeedResponse.items,
};

describe('ResearchIntelligenceFeed', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApi.getResearchFeed.mockResolvedValue(mockFeedResponse);
    mockedApi.getResearchSummary.mockResolvedValue(mockSummaryResponse);
  });

  test('renders header, tabs, and loaded articles', async () => {
    render(<ResearchIntelligenceFeed />);

    expect(screen.getByText('Holding Intelligence & Research')).toBeInTheDocument();
    expect(screen.getByText('News & Pulse')).toBeInTheDocument();
    expect(screen.getByText('Broker Targets')).toBeInTheDocument();
    expect(screen.getByText('Earnings Concalls')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('REC Limited signs major power financing pact')).toBeInTheDocument();
      expect(screen.getByText('Buy REC; target of Rs 600: Motilal Oswal')).toBeInTheDocument();
      expect(screen.getByText('Target: ₹600.00')).toBeInTheDocument();
      expect(screen.getByText('Q2 FY25')).toBeInTheDocument();
    });
  });

  test('filters by tab click', async () => {
    render(<ResearchIntelligenceFeed />);

    await waitFor(() => {
      expect(screen.getByText('Broker Targets')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Broker Targets'));

    await waitFor(() => {
      expect(mockedApi.getResearchFeed).toHaveBeenCalledWith(
        expect.objectContaining({ category: 'BROKER_REPORT' })
      );
    });
  });

  test('calls sync on Sync Now click', async () => {
    mockedApi.refreshMarketNews.mockResolvedValue({
      message: 'Feed synchronization complete: 10 fetched, 5 saved/updated.',
      articles_fetched: 10,
      articles_inserted: 5,
      status: 'success',
    });

    render(<ResearchIntelligenceFeed />);

    await waitFor(() => {
      expect(screen.getByText('Sync Now')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Sync Now'));

    await waitFor(() => {
      expect(mockedApi.refreshMarketNews).toHaveBeenCalledTimes(1);
    });
  });

  test('displays empty state when no items exist', async () => {
    mockedApi.getResearchFeed.mockResolvedValue({
      total: 0,
      symbols: [],
      items: [],
    });

    render(<ResearchIntelligenceFeed />);

    await waitFor(() => {
      expect(screen.getByText('No intelligence updates found')).toBeInTheDocument();
    });
  });
});
