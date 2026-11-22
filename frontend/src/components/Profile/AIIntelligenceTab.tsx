import React, { useEffect, useState } from 'react';
import {
  SparklesIcon,
  CpuChipIcon,
  CloudIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import {
  deleteEdgeModel,
  downloadEdgeModel,
  EdgeModelInfo,
  getEdgeModels,
  getModelProgress,
  SentimentTestResult,
  testSentiment,
} from '../../services/mlApi';

export const AIIntelligenceTab: React.FC = () => {
  const [provider, setProvider] = useState<'ollama' | 'gemini' | 'openai'>('ollama');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [ollamaModel, setOllamaModel] = useState('llama3:latest');
  const [apiKey, setApiKey] = useState('');
  const [saved, setSaved] = useState(false);

  // Edge ML Models state
  const [models, setModels] = useState<EdgeModelInfo[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [testHeadline, setTestHeadline] = useState(
    'Tata Motors reports 45% surge in Q3 consolidated profit, declares special dividend'
  );
  const [testResult, setTestResult] = useState<SentimentTestResult | null>(null);
  const [testingSentiment, setTestingSentiment] = useState(false);

  const fetchModels = async () => {
    try {
      setLoadingModels(true);
      const data = await getEdgeModels();
      setModels(data);
    } catch {
      // Silently fall back to empty
    } finally {
      setLoadingModels(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  // Poll while model download is in progress
  useEffect(() => {
    const hasDownloading = models.some((m) => m.status === 'DOWNLOADING');
    if (!hasDownloading) return;

    const interval = setInterval(async () => {
      try {
        const data = await getEdgeModels();
        setModels(data);
      } catch {
        // Silently handle polling error
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [models]);

  const handleDownload = async (modelId: string) => {
    try {
      const updated = await downloadEdgeModel(modelId);
      setModels((prev) => prev.map((m) => (m.id === modelId ? updated : m)));
    } catch {
      // Refresh status on failure
      const data = await getModelProgress(modelId).catch(() => null);
      if (data) setModels((prev) => prev.map((m) => (m.id === modelId ? data : m)));
    }
  };

  const handleDelete = async (modelId: string) => {
    try {
      await deleteEdgeModel(modelId);
      fetchModels();
    } catch {
      // Ignore
    }
  };

  const handleTestSentiment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testHeadline.trim()) return;
    try {
      setTestingSentiment(true);
      const res = await testSentiment(testHeadline.trim());
      setTestResult(res);
    } catch {
      // Ignore
    } finally {
      setTestingSentiment(false);
    }
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('ai_provider', provider);
    localStorage.setItem('ai_ollama_url', ollamaUrl);
    localStorage.setItem('ai_ollama_model', ollamaModel);
    // Cloud LLM API keys will be managed via backend vault encryption in v1.6
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="pb-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <SparklesIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">AI & Intelligence Settings</h2>
          <span className="ml-2 text-xs font-semibold px-2.5 py-0.5 rounded bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300">
            Coming Soon
          </span>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Configure on-demand Edge ML models and local or cloud LLMs to power holding analysis, earnings call summaries, and news intelligence.
        </p>
      </div>

      {/* Edge ML Models Section */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <CpuChipIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            Edge Financial Models (On-Demand & 100% Private)
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Download specialized financial transformers directly to your device for private, offline market sentiment analysis.
          </p>
        </div>

        <div className="space-y-3">
          {models.map((model) => (
            <div
              key={model.id}
              className="p-5 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 flex flex-col gap-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900 dark:text-white">{model.name}</span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">({model.size_mb} MB)</span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-xl">
                    {model.description}
                  </p>
                </div>

                {/* Status Badges */}
                <div>
                  {model.status === 'ACTIVE' && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
                      <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                      Active (ONNX Inference)
                    </span>
                  )}
                  {model.status === 'DOWNLOADING' && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-300">
                      <ArrowPathIcon className="h-3.5 w-3.5 animate-spin" />
                      Downloading ({model.progress_percentage}%)
                    </span>
                  )}
                  {model.status === 'FAILED' && (
                    <span
                      title={model.error_message || undefined}
                      className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-300"
                    >
                      Download Failed
                    </span>
                  )}
                  {model.status === 'NOT_DOWNLOADED' && (
                    <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                      Using Fast Financial Lexicon
                    </span>
                  )}
                </div>
              </div>

              {/* Error message if failed */}
              {model.status === 'FAILED' && model.error_message && (
                <div className="p-2.5 rounded bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-xs text-red-700 dark:text-red-300">
                  {model.error_message}
                </div>
              )}

              {/* Progress Bar when downloading */}
              {model.status === 'DOWNLOADING' && (
                <div className="w-full space-y-1">
                  <div className="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${model.progress_percentage}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-[11px] text-gray-500">
                    <span>Downloading quantized ONNX weights...</span>
                    <span>{model.progress_percentage}%</span>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center gap-3 pt-1 border-t border-gray-200 dark:border-gray-700">
                {model.status !== 'ACTIVE' && model.status !== 'DOWNLOADING' && (
                  <button
                    type="button"
                    onClick={() => handleDownload(model.id)}
                    className="btn btn-primary text-xs flex items-center gap-1.5 py-1.5 px-3"
                  >
                    <ArrowDownTrayIcon className="h-4 w-4" />
                    {model.status === 'FAILED' ? 'Retry Download' : `Download Model (${model.size_mb} MB)`}
                  </button>
                )}

                {model.status === 'ACTIVE' && (
                  <button
                    type="button"
                    onClick={() => handleDelete(model.id)}
                    className="btn btn-secondary text-xs flex items-center gap-1.5 py-1.5 px-3 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/20"
                  >
                    <TrashIcon className="h-4 w-4" />
                    Delete Model (Free Space)
                  </button>
                )}

                <button
                  type="button"
                  onClick={fetchModels}
                  disabled={loadingModels}
                  className="btn btn-secondary text-xs flex items-center gap-1 py-1.5 px-2.5 text-gray-500"
                  title="Check status"
                >
                  <ArrowPathIcon className={`h-3.5 w-3.5 ${loadingModels ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Live Headline Sentiment Playground */}
        <div className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 space-y-3">
          <div className="font-semibold text-sm text-gray-900 dark:text-white">
            🧪 Test Active Sentiment Engine
          </div>
          <form onSubmit={handleTestSentiment} className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={testHeadline}
              onChange={(e) => setTestHeadline(e.target.value)}
              placeholder="Enter financial headline or earnings comment..."
              className="form-input text-xs flex-grow"
            />
            <button
              type="submit"
              disabled={testingSentiment || !testHeadline.trim()}
              className="btn btn-primary text-xs whitespace-nowrap py-2 px-4 flex items-center justify-center gap-1"
            >
              {testingSentiment ? <ArrowPathIcon className="h-4 w-4 animate-spin" /> : 'Analyze'}
            </button>
          </form>

          {testResult && (
            <div className="flex items-center gap-3 text-xs p-2.5 rounded bg-gray-50 dark:bg-gray-750 border border-gray-200 dark:border-gray-700">
              <span className="text-gray-500">Result:</span>
              <span
                className={`font-bold px-2 py-0.5 rounded ${
                  testResult.label === 'POSITIVE'
                    ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300'
                    : testResult.label === 'NEGATIVE'
                    ? 'bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-300'
                    : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                {testResult.label} ({Math.round(testResult.score * 100)}%)
              </span>
              <span className="text-gray-400">Engine:</span>
              <span className="font-mono text-purple-600 dark:text-purple-400">
                {testResult.engine}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Cloud & Local LLM Provider Section */}
      <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <SparklesIcon className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            Large Language Models (LLM) Integration
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Connect private local Ollama or cloud LLMs for conversational portfolio audits and concall summaries.
          </p>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-start gap-3">
          <InformationCircleIcon className="h-6 w-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900 dark:text-blue-200">
            <p className="font-semibold mb-1">Local & Private First</p>
            <p>
              ArthSaarthi is architected to keep your financial data strictly private. When enabled, you can connect a local Ollama server running entirely on your machine, ensuring no portfolio data ever leaves your personal environment.
            </p>
          </div>
        </div>

        <form onSubmit={handleSave} className="card space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              LLM Provider
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setProvider('ollama')}
                className={`p-4 rounded-lg border flex flex-col items-center gap-2 text-center transition ${
                  provider === 'ollama'
                    ? 'border-purple-600 bg-purple-50 dark:bg-purple-950/30 text-purple-900 dark:text-purple-200 ring-2 ring-purple-500/20'
                    : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750'
                }`}
              >
                <CpuChipIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                <div className="font-semibold text-sm">Ollama (Local)</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">100% Private, Offline</div>
              </button>

              <button
                type="button"
                onClick={() => setProvider('gemini')}
                className={`p-4 rounded-lg border flex flex-col items-center gap-2 text-center transition ${
                  provider === 'gemini'
                    ? 'border-purple-600 bg-purple-50 dark:bg-purple-950/30 text-purple-900 dark:text-purple-200 ring-2 ring-purple-500/20'
                    : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750'
                }`}
              >
                <CloudIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                <div className="font-semibold text-sm">Google Gemini</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Flash & Pro Models</div>
              </button>

              <button
                type="button"
                onClick={() => setProvider('openai')}
                className={`p-4 rounded-lg border flex flex-col items-center gap-2 text-center transition ${
                  provider === 'openai'
                    ? 'border-purple-600 bg-purple-50 dark:bg-purple-950/30 text-purple-900 dark:text-purple-200 ring-2 ring-purple-500/20'
                    : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750'
                }`}
              >
                <SparklesIcon className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
                <div className="font-semibold text-sm">OpenAI</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">GPT-4o & Mini</div>
              </button>
            </div>
          </div>

          {provider === 'ollama' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Ollama Host URL</label>
                <input
                  type="text"
                  value={ollamaUrl}
                  onChange={(e) => setOllamaUrl(e.target.value)}
                  placeholder="http://localhost:11434"
                  className="form-input"
                />
                <span className="text-xs text-gray-500 mt-1 block">Default local port is 11434</span>
              </div>
              <div>
                <label className="form-label">Model Name</label>
                <input
                  type="text"
                  value={ollamaModel}
                  onChange={(e) => setOllamaModel(e.target.value)}
                  placeholder="llama3:latest"
                  className="form-input"
                />
                <span className="text-xs text-gray-500 mt-1 block">E.g., llama3, mistral, deepseek-r1</span>
              </div>
            </div>
          ) : (
            <div>
              <label className="form-label">
                {provider === 'gemini' ? 'Gemini API Key' : 'OpenAI API Key'}
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API secret key"
                className="form-input font-mono"
              />
              <span className="text-xs text-gray-500 mt-1 block">Cloud API key storage will be managed securely via backend vault upon LLM launch</span>
            </div>
          )}

          <div className="pt-2 flex items-center justify-between">
            <button type="submit" className="btn btn-primary flex items-center gap-2">
              {saved ? (
                <>
                  <CheckCircleIcon className="h-5 w-5 text-white" />
                  Saved Preferences
                </>
              ) : (
                'Save AI Preferences'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AIIntelligenceTab;
