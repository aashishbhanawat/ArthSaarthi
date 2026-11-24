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
    transcript_url: 'https://example.com/exide-transcript.pdf',
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
    average_tone_score: 0.65,
    sample_size: 10,
  },
  qa_tone: {
    positive_pct: 50.0,
    neutral_pct: 30.0,
    negative_pct: 20.0,
    overall: 'BALANCED',
    average_tone_score: 0.25,
    sample_size: 8,
  },
  tone_gap_alert: 0.40,
  tone_divergence_summary: 'Tone Gap Alert (+0.40): Management tone turned defensive under analyst questioning.',
  hedge_rate_per_100w: 1.25,
  topic_sentiment: {
    demand_revenue: 0.55,
    margins_costs: -0.20,
    guidance_outlook: 0.35,
    capex_debt: 0.45,
  },
  red_flags: [
    { text: 'Raw material volatility impacted automotive margins slightly.', score: -0.35 },
  ],
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
      expect(screen.getAllByText(/Tone Gap Alert/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/Uncertainty \/ Hedging: 1.25 \/ 100 words/i)).toBeInTheDocument();
      expect(screen.getByText('Aspect Financial Sentiment Scorecard')).toBeInTheDocument();
      expect(screen.getByText('Demand & Revenue')).toBeInTheDocument();
      expect(screen.getByText('Cautionary Remarks & Risk Flags')).toBeInTheDocument();
      expect(screen.getByText(/"Raw material volatility impacted automotive margins slightly."/i)).toBeInTheDocument();
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

  test('renders transcribe and analyze audio button when concall has audio podcast', async () => {
    mockedNewsApi.analyzeConcall.mockResolvedValue({
      ...mockAnalysisResult,
      transcription_source: 'WHISPER_AUDIO',
    });

    const audioOnlyArticle: MarketNewsArticle = {
      ...mockArticle,
      metadata_json: {
        quarter: 'Q2FY27',
        audio_url: 'https://example.com/podcast.mp3',
      },
    };

    render(
      <ConcallAnalysisModal
        article={audioOnlyArticle}
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    expect(screen.getByText(/On-Device Audio Intelligence/i)).toBeInTheDocument();
    const transcribeBtn = screen.getByRole('button', { name: /Transcribe & Analyze Audio/i });
    expect(transcribeBtn).toBeEnabled();

    fireEvent.click(transcribeBtn);

    await waitFor(() => {
      expect(mockedNewsApi.analyzeConcall).toHaveBeenCalledWith(audioOnlyArticle.id, undefined);
      expect(screen.getByText('Management Discussion Tone')).toBeInTheDocument();
      expect(screen.getByText(/Source: WHISPER_AUDIO/i)).toBeInTheDocument();
    });
  });

  test('displays background processing banner when request times out', async () => {
    mockedNewsApi.analyzeConcall.mockRejectedValue({
      response: { status: 504, data: { detail: 'Gateway Timeout / Proxy Read Timeout' } },
      message: 'timeout of 300000ms exceeded',
    });

    const audioArticle: MarketNewsArticle = {
      ...mockArticle,
      metadata_json: {
        quarter: 'Q2FY27',
        audio_url: 'https://example.com/podcast.mp3',
      },
    };

    render(
      <ConcallAnalysisModal
        article={audioArticle}
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    const transcribeBtn = screen.getByRole('button', { name: /Transcribe & Analyze Audio/i });
    fireEvent.click(transcribeBtn);

    await waitFor(() => {
      expect(screen.getByText(/Transcription In Progress \(Background Processing\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Refresh & Check Results/i)).toBeInTheDocument();
    });
  });
});
