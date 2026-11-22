import React, { useCallback, useEffect, useState } from 'react';
import {
  ArrowPathIcon,
  ArrowTopRightOnSquareIcon,
  DocumentChartBarIcon,
  NewspaperIcon,
  SpeakerWaveIcon,
  TagIcon,
} from '@heroicons/react/24/outline';
import {
  getResearchFeed,
  getResearchSummary,
  refreshMarketNews,
} from '../../services/newsApi';
import {
  MarketNewsArticle,
  ResearchFeedSummary,
} from '../../types/marketNews';

interface ResearchIntelligenceFeedProps {
  initialSymbol?: string;
}

export const ResearchIntelligenceFeed: React.FC<ResearchIntelligenceFeedProps> = ({
  initialSymbol,
}) => {
  const [articles, setArticles] = useState<MarketNewsArticle[]>([]);
  const [summary, setSummary] = useState<ResearchFeedSummary | null>(null);
  const [trackedSymbols, setTrackedSymbols] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedSymbol, setSelectedSymbol] = useState<string>(initialSymbol || 'ALL');
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [feedRes, summaryRes] = await Promise.all([
        getResearchFeed({
          category: selectedCategory === 'ALL' ? undefined : selectedCategory,
          symbol: selectedSymbol === 'ALL' ? undefined : selectedSymbol,
          only_holdings: true,
          limit: 30,
        }),
        getResearchSummary(true),
      ]);
      setArticles(feedRes.items);
      setTrackedSymbols(feedRes.symbols);
      setSummary(summaryRes);
    } catch (err: unknown) {
      console.error('Failed to load research feed:', err);
      setError('Unable to load market research intelligence feed.');
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, selectedSymbol]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      setRefreshMessage(null);
      const res = await refreshMarketNews();
      setRefreshMessage(res.message);
      await loadData();
      setTimeout(() => setRefreshMessage(null), 4000);
    } catch (err: unknown) {
      console.error('Manual feed refresh failed:', err);
      setError('Feed refresh failed. Please try again later.');
    } finally {
      setRefreshing(false);
    }
  };

  const formatRelativeTime = (isoString: string): string => {
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      if (diffHours < 1) {
        const diffMins = Math.max(1, Math.floor(diffMs / (1000 * 60)));
        return `${diffMins}m ago`;
      }
      if (diffHours < 24) {
        return `${diffHours}h ago`;
      }
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    } catch {
      return '';
    }
  };

  const getSentimentBadge = (sentiment: string) => {
    switch (sentiment) {
      case 'POSITIVE':
        return (
          <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
            Bullish
          </span>
        );
      case 'NEGATIVE':
        return (
          <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300">
            Bearish
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300">
            Neutral
          </span>
        );
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'BROKER_REPORT':
        return <DocumentChartBarIcon className="w-4 h-4 text-amber-500 mr-1 inline" />;
      case 'CONCALL':
        return <SpeakerWaveIcon className="w-4 h-4 text-purple-500 mr-1 inline" />;
      case 'RESULT':
        return <TagIcon className="w-4 h-4 text-indigo-500 mr-1 inline" />;
      default:
        return <NewspaperIcon className="w-4 h-4 text-blue-500 mr-1 inline" />;
    }
  };

  const getRecommendationBadge = (rec?: string) => {
    if (!rec) return null;
    const upper = rec.toUpperCase();
    if (upper === 'BUY' || upper === 'ACCUMULATE') {
      return (
        <span className="px-2 py-0.5 text-xs font-bold rounded bg-emerald-500 text-white dark:bg-emerald-600">
          {upper}
        </span>
      );
    }
    if (upper === 'SELL' || upper === 'REDUCE') {
      return (
        <span className="px-2 py-0.5 text-xs font-bold rounded bg-rose-500 text-white dark:bg-rose-600">
          {upper}
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-xs font-bold rounded bg-amber-500 text-white dark:bg-amber-600">
        {upper}
      </span>
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 mb-6 transition-all">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-4 border-b border-gray-100 dark:border-gray-700">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              Holding Intelligence & Research
            </h2>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Curated holding news, broker target prices, and earnings concall insights
          </p>
        </div>
        <div className="flex items-center gap-2">
          {refreshMessage && (
            <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
              {refreshMessage}
            </span>
          )}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
            title="Sync latest market news and research feeds"
          >
            <ArrowPathIcon className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Syncing...' : 'Sync Now'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 mt-4 overflow-x-auto pb-2 scrollbar-none">
        {[
          { id: 'ALL', label: 'All Insights', count: undefined },
          { id: 'NEWS', label: 'News & Pulse', count: summary?.news_count },
          { id: 'BROKER_REPORT', label: 'Broker Targets', count: summary?.broker_reports_count },
          { id: 'CONCALL', label: 'Earnings Concalls', count: summary?.concalls_count },
          { id: 'RESULT', label: 'Quarterly Results', count: summary?.results_count },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedCategory(tab.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all flex items-center gap-1.5 ${
              selectedCategory === tab.id
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            {getCategoryIcon(tab.id)}
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <span
                className={`ml-1 px-1.5 py-0.2 text-[10px] rounded-full ${
                  selectedCategory === tab.id
                    ? 'bg-blue-800 text-blue-100'
                    : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300'
                }`}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Ticker Filter Chips */}
      {trackedSymbols.length > 0 && (
        <div className="flex items-center gap-1.5 mt-3 overflow-x-auto pb-1 scrollbar-none text-xs">
          <span className="text-gray-400 dark:text-gray-500 font-medium whitespace-nowrap mr-1">
            Filter Ticker:
          </span>
          <button
            onClick={() => setSelectedSymbol('ALL')}
            className={`px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
              selectedSymbol === 'ALL'
                ? 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            All Holdings ({trackedSymbols.length})
          </button>
          {trackedSymbols.map((sym) => (
            <button
              key={sym}
              onClick={() => setSelectedSymbol(sym)}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold whitespace-nowrap transition-colors ${
                selectedSymbol === sym
                  ? 'bg-blue-600 text-white dark:bg-blue-500'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {sym}
            </button>
          ))}
        </div>
      )}

      {/* Content Feed List */}
      <div className="mt-4 space-y-3">
        {loading && articles.length === 0 ? (
          <div className="py-12 text-center text-gray-500 dark:text-gray-400">
            <ArrowPathIcon className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-500" />
            <p className="text-xs">Fetching research intelligence updates...</p>
          </div>
        ) : error ? (
          <div className="py-8 text-center text-rose-500 text-xs">
            {error}
          </div>
        ) : articles.length === 0 ? (
          <div className="py-12 text-center border border-dashed border-gray-200 dark:border-gray-700 rounded-xl">
            <NewspaperIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              No intelligence updates found
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-sm mx-auto">
              Sync feeds to pull the latest news, broker target prices, and conference calls for your portfolio.
            </p>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="mt-4 px-4 py-1.5 text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
            >
              Fetch Latest Insights
            </button>
          </div>
        ) : (
          articles.map((item) => (
            <div
              key={item.id}
              className="group p-3.5 rounded-lg border border-gray-100 dark:border-gray-700/80 bg-gray-50/60 dark:bg-gray-750/50 hover:bg-gray-50 dark:hover:bg-gray-700/60 transition-all"
            >
              {/* Meta row */}
              <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-300">
                    {item.source}
                  </span>
                  <span className="text-gray-300 dark:text-gray-600">•</span>
                  <span className="text-[11px] text-gray-500 dark:text-gray-400">
                    {formatRelativeTime(item.published_at)}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  {getSentimentBadge(item.sentiment)}
                  {item.category === 'BROKER_REPORT' && item.metadata_json && (
                    <>
                      {getRecommendationBadge(item.metadata_json.recommendation)}
                      {item.metadata_json.target_price && (
                        <span className="px-2 py-0.5 text-xs font-mono font-bold rounded bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
                          Target: ₹{Number(item.metadata_json.target_price).toFixed(2)}
                        </span>
                      )}
                    </>
                  )}
                  {item.category === 'CONCALL' && item.metadata_json?.quarter && (
                    <span className="px-2 py-0.5 text-xs font-semibold rounded bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300">
                      {item.metadata_json.quarter}
                    </span>
                  )}
                </div>
              </div>

              {/* Title & external link */}
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-semibold text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 group-hover:underline flex items-start gap-1.5 transition-colors"
              >
                <span>{item.title}</span>
                <ArrowTopRightOnSquareIcon className="w-3.5 h-3.5 text-gray-400 group-hover:text-blue-500 flex-shrink-0 mt-0.5" />
              </a>

              {/* Summary */}
              {item.summary && (
                <p className="text-xs text-gray-600 dark:text-gray-300 mt-1 line-clamp-2 leading-relaxed">
                  {item.summary}
                </p>
              )}

              {/* Bottom footer: Broker name or Concall audio link & Symbol tags */}
              <div className="flex flex-wrap items-center justify-between gap-2 mt-2.5 pt-2 border-t border-gray-200/60 dark:border-gray-700/60">
                <div className="flex items-center gap-2">
                  {item.metadata_json?.broker && (
                    <span className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">
                      Broker: <strong className="text-gray-700 dark:text-gray-200">{item.metadata_json.broker}</strong>
                    </span>
                  )}
                  {item.metadata_json?.audio_url && (
                    <a
                      href={item.metadata_json.audio_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-purple-600 dark:text-purple-400 hover:underline"
                    >
                      <SpeakerWaveIcon className="w-3.5 h-3.5" />
                      Listen Concall Audio
                    </a>
                  )}
                </div>

                {/* Symbols */}
                {item.symbols && item.symbols.length > 0 && (
                  <div className="flex items-center gap-1">
                    {item.symbols.map((sym) => (
                      <span
                        key={sym}
                        className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                      >
                        {sym}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default React.memo(ResearchIntelligenceFeed);
