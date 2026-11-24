import React, { useState } from 'react';
import {
  XMarkIcon,
  SparklesIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  ChatBubbleLeftRightIcon,
  TagIcon,
  CurrencyRupeeIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  DocumentTextIcon,
  SpeakerWaveIcon,
} from '@heroicons/react/24/outline';
import { ConcallAnalysis, MarketNewsArticle } from '../../types/marketNews';
import { analyzeConcall } from '../../services/newsApi';

interface ConcallAnalysisModalProps {
  article: MarketNewsArticle;
  isOpen: boolean;
  onClose: () => void;
  onAnalysisUpdated?: (updated: ConcallAnalysis) => void;
}

export const ConcallAnalysisModal: React.FC<ConcallAnalysisModalProps> = ({
  article,
  isOpen,
  onClose,
  onAnalysisUpdated,
}) => {
  const initialAnalysis = article.metadata_json?.concall_analysis;
  const [analysis, setAnalysis] = useState<ConcallAnalysis | null>(initialAnalysis || null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showPasteTab, setShowPasteTab] = useState<boolean>(false);
  const [customText, setCustomText] = useState<string>('');

  const isAudioOnly = Boolean(
    article.metadata_json?.audio_url &&
    !article.metadata_json?.transcript_url &&
    !article.metadata_json?.transcript_text &&
    !article.url?.toLowerCase().endsWith('.pdf')
  );

  if (!isOpen) return null;

  const handleRunAnalysis = async (textOverride?: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await analyzeConcall(article.id, textOverride || undefined);
      setAnalysis(res);
      if (onAnalysisUpdated) {
        onAnalysisUpdated(res);
      }
      setShowPasteTab(false);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Failed to analyze concall. Please ensure transcript text or audio model is available.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const getToneBadge = (tone: string) => {
    switch (tone) {
      case 'BULLISH':
        return (
          <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700">
            🟢 Bullish
          </span>
        );
      case 'BEARISH':
        return (
          <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border border-rose-300 dark:border-rose-700">
            🔴 Bearish
          </span>
        );
      case 'BALANCED':
        return (
          <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-950/80 dark:text-blue-300 border border-blue-300 dark:border-blue-700">
            🔵 Balanced
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 border border-gray-300 dark:border-gray-700">
            ⚪ Neutral
          </span>
        );
    }
  };

  const formatAspectScore = (score: number) => {
    const isPos = score > 0.05;
    const isNeg = score < -0.05;
    const colorClass = isPos
      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
      : isNeg
      ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
      : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
    const sign = score > 0 ? '+' : '';
    return (
      <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${colorClass}`}>
        {sign}{score.toFixed(2)}
      </span>
    );
  };

  const aspectLabels: Record<string, string> = {
    demand_revenue: 'Demand & Revenue',
    margins_costs: 'Margins & Costs',
    guidance_outlook: 'Guidance & Outlook',
    capex_debt: 'CapEx & Balance Sheet',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5">
      <div className="relative w-full max-w-3xl rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 flex items-start justify-between bg-gray-50/50 dark:bg-gray-900/50">
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-purple-100 text-purple-800 dark:bg-purple-950/80 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                🎙️ Concall Intelligence
              </span>
              {article.metadata_json?.quarter && (
                <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                  {article.metadata_json.quarter}
                </span>
              )}
              {analysis && (
                <span className="text-[11px] text-gray-500 dark:text-gray-400">
                  Source: {analysis.transcription_source}
                </span>
              )}
              {(article.metadata_json?.transcript_url || (article.url?.toLowerCase().endsWith('.pdf') ? article.url : null)) && (
                <a
                  href={article.metadata_json?.transcript_url || article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-indigo-50 hover:bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:hover:bg-indigo-900 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 transition-colors"
                >
                  <DocumentTextIcon className="w-3.5 h-3.5" />
                  Read Filing PDF
                </a>
              )}
              {article.metadata_json?.audio_url && (
                <a
                  href={article.metadata_json.audio_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-purple-50 hover:bg-purple-100 text-purple-700 dark:bg-purple-950/60 dark:hover:bg-purple-900 dark:text-purple-300 border border-purple-200 dark:border-purple-800 transition-colors"
                >
                  <SpeakerWaveIcon className="w-3.5 h-3.5" />
                  Listen Audio
                </a>
              )}
              {analysis?.hedge_rate_per_100w !== undefined && analysis.hedge_rate_per_100w !== null && (
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded border flex items-center gap-1 ${
                    analysis.hedge_rate_per_100w >= 0.8
                      ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border-rose-200 dark:border-rose-800'
                      : analysis.hedge_rate_per_100w >= 0.3
                      ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border-amber-200 dark:border-amber-800'
                      : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                  }`}
                  title="Hedging & Uncertainty Density: Frequency of cautious or protective words (e.g. 'headwinds', 'volatile', 'uncertainty') per 100 spoken words from Loughran-McDonald financial dictionary. <0.30 reflects high management conviction."
                >
                  Uncertainty / Hedging: {analysis.hedge_rate_per_100w.toFixed(2)} / 100 words (
                  {analysis.hedge_rate_per_100w >= 0.8
                    ? 'High Caution'
                    : analysis.hedge_rate_per_100w >= 0.3
                    ? 'Moderate'
                    : 'Low Uncertainty'}
                  )
                </span>
              )}
            </div>
            <h3 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white leading-snug">
              {article.title}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Close modal"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="px-6 py-5 overflow-y-auto space-y-6">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300">
              {error}
            </div>
          )}

          {!analysis && !loading && (
            <div className="text-center py-10 px-4 rounded-xl border border-dashed border-gray-300 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/20">
              {isAudioOnly ? (
                <SpeakerWaveIcon className="w-10 h-10 text-purple-600 dark:text-purple-400 mx-auto mb-3" />
              ) : (
                <SparklesIcon className="w-10 h-10 text-purple-600 dark:text-purple-400 mx-auto mb-3" />
              )}
              <h4 className="text-base font-semibold text-gray-900 dark:text-white">
                No Concall Analysis Generated Yet
              </h4>
              {isAudioOnly ? (
                <div className="max-w-md mx-auto mt-1 mb-5 space-y-2">
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Official audio podcast is available. Click <strong>Transcribe &amp; Analyze Audio</strong> to transcribe with on-device Faster-Whisper, or paste transcript text manually.
                  </p>
                  <p className="text-[11px] text-purple-800 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800/60 rounded-lg p-2 text-left">
                    ⚡ <strong>On-Device Audio Intelligence:</strong> Powered by Faster-Whisper INT8 (CTranslate2). Transcribes speech directly on-device without cloud APIs or external tools.
                  </p>
                </div>
              ) : (
                <p className="text-xs text-gray-500 dark:text-gray-400 max-w-md mx-auto mt-1 mb-5">
                  Analyze management tone, forward guidance, and extracted key takeaways using edge ML and statutory PDF filing transcripts.
                </p>
              )}
              <div className="flex flex-wrap items-center justify-center gap-3">
                {isAudioOnly && article.metadata_json?.audio_url && (
                  <a
                    href={article.metadata_json.audio_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-800 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-700 transition-colors flex items-center gap-1.5"
                  >
                    <SpeakerWaveIcon className="w-4 h-4" />
                    Listen Audio
                  </a>
                )}
                <button
                  onClick={() => setShowPasteTab(!showPasteTab)}
                  className="px-4 py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex items-center gap-1.5"
                >
                  <DocumentTextIcon className="w-4 h-4" />
                  Paste Custom Transcript
                </button>
                <button
                  onClick={() => handleRunAnalysis()}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-purple-600 text-white hover:bg-purple-700 shadow-sm transition-colors flex items-center gap-1.5"
                >
                  <SparklesIcon className="w-4 h-4" />
                  {isAudioOnly ? 'Transcribe & Analyze Audio' : 'Analyze with Edge Engine'}
                </button>
              </div>
            </div>
          )}

          {loading && (
            <div className="text-center py-12">
              <ArrowPathIcon className="w-8 h-8 text-purple-600 dark:text-purple-400 animate-spin mx-auto mb-3" />
              <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                {isAudioOnly ? 'Transcribing & Analyzing Audio Podcast (~1-2 min)...' : 'Running Edge Concall Intelligence...'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {isAudioOnly
                  ? 'Transcribing speech with Edge Faster-Whisper (INT8 quantized), then evaluating tone with FinBERT'
                  : 'Parsing sections, evaluating FinBERT-Tone polarity, and calculating quantitative metrics'}
              </p>
            </div>
          )}

          {showPasteTab && (
            <div className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/40 space-y-3">
              <h5 className="text-xs font-bold text-gray-800 dark:text-gray-200 uppercase tracking-wider">
                Paste Transcript Text
              </h5>
              <textarea
                value={customText}
                onChange={(e) => setCustomText(e.target.value)}
                placeholder="Paste management discussion and analyst Q&A transcript here..."
                rows={5}
                className="w-full text-xs p-3 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:outline-none"
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setShowPasteTab(false)}
                  className="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400 hover:underline"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleRunAnalysis(customText)}
                  disabled={!customText.trim()}
                  className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
                >
                  Analyze Text
                </button>
              </div>
            </div>
          )}

          {analysis && !loading && (
            <>
              {/* Tone Divergence Gap Alert Banner */}
              {analysis.tone_divergence_summary && (
                <div
                  className={`p-3.5 rounded-xl border flex items-start gap-2.5 text-xs ${
                    (analysis.tone_gap_alert || 0) >= 0.10
                      ? 'bg-amber-50 dark:bg-amber-950/30 border-amber-300 dark:border-amber-800/70 text-amber-900 dark:text-amber-200'
                      : 'bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800/60 text-blue-900 dark:text-blue-200'
                  }`}
                >
                  <ExclamationTriangleIcon
                    className={`w-4 h-4 flex-shrink-0 mt-0.5 ${
                      (analysis.tone_gap_alert || 0) >= 0.10
                        ? 'text-amber-600 dark:text-amber-400'
                        : 'text-blue-600 dark:text-blue-400'
                    }`}
                  />
                  <div>
                    <span className="font-bold">
                      {(analysis.tone_gap_alert || 0) >= 0.10 ? 'Tone Gap Alert: ' : 'Tone Flow: '}
                    </span>
                    {analysis.tone_divergence_summary}
                  </div>
                </div>
              )}

              {/* 1. Tone & Sentiment Gauges */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {/* Management Tone */}
                <div className="p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/60 dark:bg-gray-900/60">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-gray-700 dark:text-gray-300">
                      Management Discussion Tone
                    </span>
                    {getToneBadge(analysis.management_tone.overall)}
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
                    <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                      {analysis.management_tone.positive_pct}% Pos
                    </span>
                    <span>•</span>
                    <span>{analysis.management_tone.neutral_pct}% Neu</span>
                    <span>•</span>
                    <span className="text-rose-600 dark:text-rose-400 font-bold">
                      {analysis.management_tone.negative_pct}% Neg
                    </span>
                  </div>
                </div>

                {/* Analyst Q&A Tone */}
                <div className="p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/60 dark:bg-gray-900/60">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-gray-700 dark:text-gray-300">
                      Analyst Q&A Tone
                    </span>
                    {getToneBadge(analysis.qa_tone.overall)}
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
                    <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                      {analysis.qa_tone.positive_pct}% Pos
                    </span>
                    <span>•</span>
                    <span>{analysis.qa_tone.neutral_pct}% Neu</span>
                    <span>•</span>
                    <span className="text-rose-600 dark:text-rose-400 font-bold">
                      {analysis.qa_tone.negative_pct}% Neg
                    </span>
                  </div>
                </div>
              </div>

              {/* 2. 4-Aspect Sentiment Scorecard */}
              {analysis.topic_sentiment && Object.keys(analysis.topic_sentiment).length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-gray-400 mb-2.5 flex items-center gap-1.5">
                    <ChartBarIcon className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                    Aspect Financial Sentiment Scorecard
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                    {Object.entries(analysis.topic_sentiment).map(([topicKey, score]) => (
                      <div
                        key={topicKey}
                        className="p-3 rounded-lg border border-gray-200 dark:border-gray-800 bg-gray-50/70 dark:bg-gray-900/40 flex flex-col justify-between"
                      >
                        <span className="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1.5">
                          {aspectLabels[topicKey] || topicKey}
                        </span>
                        <div>{formatAspectScore(score)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 3. Cautionary Statements / Extractive Red Flags */}
              {analysis.red_flags && analysis.red_flags.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-rose-700 dark:text-rose-400 mb-2.5 flex items-center gap-1.5">
                    <ExclamationTriangleIcon className="w-4 h-4 text-rose-600 dark:text-rose-400" />
                    Cautionary Remarks & Risk Flags
                  </h4>
                  <div className="space-y-2">
                    {analysis.red_flags.map((rf, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg border border-rose-200 dark:border-rose-900/60 bg-rose-50/40 dark:bg-rose-950/20 text-xs text-gray-800 dark:text-gray-200 leading-relaxed"
                      >
                        <p className="font-medium italic">"{rf.text}"</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 4. Guidance & Capex Highlights */}
              {analysis.guidance_metrics && analysis.guidance_metrics.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-gray-400 mb-2.5 flex items-center gap-1.5">
                    <CurrencyRupeeIcon className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                    Key Guidance & Financial Targets
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {analysis.guidance_metrics.map((g, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg border border-purple-200 dark:border-purple-900/60 bg-purple-50/50 dark:bg-purple-950/20"
                      >
                        <span className="inline-block text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-purple-200 text-purple-800 dark:bg-purple-900 dark:text-purple-200 mb-1">
                          {g.category}
                        </span>
                        <p className="text-xs text-gray-800 dark:text-gray-200 font-medium leading-relaxed">
                          "{g.text}"
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 5. Top Extracted Key Takeaways */}
              {analysis.top_takeaways && analysis.top_takeaways.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-gray-400 mb-2.5 flex items-center gap-1.5">
                    <CheckCircleIcon className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    Top Key Takeaways (Extracted Sentences)
                  </h4>
                  <ul className="space-y-2">
                    {analysis.top_takeaways.map((sent, idx) => (
                      <li
                        key={idx}
                        className="p-3 rounded-lg border border-gray-200 dark:border-gray-800 bg-gray-50/80 dark:bg-gray-900/40 text-xs text-gray-800 dark:text-gray-200 leading-relaxed flex items-start gap-2.5"
                      >
                        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200 font-bold text-[11px] flex items-center justify-center mt-0.5">
                          {idx + 1}
                        </span>
                        <span className="flex-1 font-medium">{sent}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 6. Top Discussion Topics */}
              {analysis.key_themes && analysis.key_themes.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-gray-400 mb-2 flex items-center gap-1.5">
                    <TagIcon className="w-3.5 h-3.5 text-gray-500" />
                    Core Discussion Themes
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {analysis.key_themes.map((t, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 text-xs font-semibold rounded-md bg-gray-200 dark:bg-gray-800 text-gray-800 dark:text-gray-200"
                      >
                        #{t}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-gray-200 dark:border-gray-800 bg-gray-50/70 dark:bg-gray-900/70 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {analysis && (
              <button
                onClick={() => setShowPasteTab(!showPasteTab)}
                className="text-xs text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-1"
              >
                <ChatBubbleLeftRightIcon className="w-3.5 h-3.5" />
                {showPasteTab ? 'Hide Custom Input' : 'Re-analyze with Custom Text'}
              </button>
            )}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-gray-200 dark:bg-gray-800 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
