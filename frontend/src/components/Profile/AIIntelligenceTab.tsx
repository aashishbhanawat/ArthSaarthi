import React, { useState } from 'react';
import {
  SparklesIcon,
  CpuChipIcon,
  CloudIcon,
  CheckCircleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

export const AIIntelligenceTab: React.FC = () => {
  const [provider, setProvider] = useState<'ollama' | 'gemini' | 'openai'>('ollama');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [ollamaModel, setOllamaModel] = useState('llama3:latest');
  const [apiKey, setApiKey] = useState('');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('ai_provider', provider);
    localStorage.setItem('ai_ollama_url', ollamaUrl);
    localStorage.setItem('ai_ollama_model', ollamaModel);
    if (apiKey) {
      localStorage.setItem(`ai_${provider}_key`, apiKey);
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <SparklesIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">AI & Intelligence Settings</h2>
          <span className="ml-2 text-xs font-semibold px-2.5 py-0.5 rounded bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300">
            Roadmap & LLM Hub
          </span>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Configure local or cloud-based Large Language Models (LLM) to power holding analysis, earnings call summaries, and news intelligence.
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
            <span className="text-xs text-gray-500 mt-1 block">Stored securely in client local preferences</span>
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
  );
};

export default AIIntelligenceTab;
