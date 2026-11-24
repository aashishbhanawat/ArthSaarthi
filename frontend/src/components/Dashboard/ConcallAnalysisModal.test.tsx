import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { ConcallAnalysisModal } from './ConcallAnalysisModal';
import * as newsApi from '../../services/newsApi';
import { ConcallAnalysis, MarketNewsArticle } from '../../types/marketNews';

jest.mock('../../services/newsApi');
const mockedNewsApi = newsApi as jest.Mocked<typeof newsApi>;

const mockArticle: MarketNewsArticle = {
  id: 'concall-123',
  title: 'Exide Industries Results Earnings Call for Q2FY27',
  summary: 'Earnings call transcript.',
  url: 'https://example.com/exide',
  source: 'Trendlyne Concalls',
  category: 'CONCALL',
  published_at: '2026-11-20T10:00:00Z',
  symbols: ['EXIDEIND'],
  sentiment: 'NEUTRAL',
  created_at: '2026-11-20T10:00:00Z',
  metadata_json: {
    quarter: 'Q2FY27',
    audio_url: 'https://example.com/exide.mp3',
  },
};

const mockAnalysisResult: ConcallAnalysis = {
  article_id: 'concall-123',
  title: 'Exide Industries Results Earnings Call for Q2FY27',
  quarter: 'Q2FY27',
  management_tone: {
    positive_pct: 75.0,
    neutral_pct: 20.0,
    negative_pct: 5.0,
    overall: 'BULLISH',
    sample_size: 10,
  },
  qa_tone: {
    positive_pct: 50.0,
    neutral_pct: 30.0,
    negative_pct: 20.0,
    overall: 'BALANCED',
    sample_size: 8,
  },
  guidance_metrics: [
    { category: 'Capex', text: 'Planned capex of ₹1,200 crore for gigafactory' },
    { category: 'Margin Outlook', text: 'EBITDA margins improved to 12.8%' },
  ],
  top_takeaways: [
    'Commercial production from the new facility is expected in Q4.',
    'Replacement battery demand grew 14% YoY across markets.',
  ],
  key_themes: ['Lithium Cells', 'OEM Demand', 'Capex'],
  transcription_source: 'TRANSCRIPT',
};

describe('ConcallAnalysisModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders initial state and triggers analysis on button click', async () => {
    mockedNewsApi.analyzeConcall.mockResolvedValue(mockAnalysisResult);

    render(
      <ConcallAnalysisModal
        article={mockArticle}
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    expect(screen.getByText(/Concall Intelligence/i)).toBeInTheDocument();
    expect(screen.getByText('Exide Industries Results Earnings Call for Q2FY27')).toBeInTheDocument();
    expect(screen.getByText('No Concall Analysis Generated Yet')).toBeInTheDocument();

    const analyzeBtn = screen.getByRole('button', { name: /Analyze with Edge Engine/i });
    fireEvent.click(analyzeBtn);

    await waitFor(() => {
      expect(screen.getByText('Management Discussion Tone')).toBeInTheDocument();
      expect(screen.getByText(/75% Pos/i)).toBeInTheDocument();
      expect(screen.getByText('Analyst Q&A Tone')).toBeInTheDocument();
      expect(screen.getByText('Key Guidance & Financial Targets')).toBeInTheDocument();
      expect(screen.getByText(/Planned capex of ₹1,200 crore/i)).toBeInTheDocument();
      expect(screen.getByText('Top Key Takeaways (Extracted Sentences)')).toBeInTheDocument();
      expect(screen.getByText(/Commercial production from the new facility/i)).toBeInTheDocument();
      expect(screen.getByText('#Lithium Cells')).toBeInTheDocument();
    });
  });

  test('renders pre-cached analysis directly', () => {
    const articleWithAnalysis: MarketNewsArticle = {
      ...mockArticle,
      metadata_json: {
        ...mockArticle.metadata_json,
        concall_analysis: mockAnalysisResult,
      },
    };

    render(
      <ConcallAnalysisModal
        article={articleWithAnalysis}
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    expect(screen.getByText('Management Discussion Tone')).toBeInTheDocument();
    expect(screen.getByText(/75% Pos/i)).toBeInTheDocument();
  });
});
