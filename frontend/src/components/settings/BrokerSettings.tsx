import React, { useCallback, useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import {
  KeyIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  TrashIcon,
  ArrowPathIcon,
  ArrowTopRightOnSquareIcon,
} from '@heroicons/react/24/outline';
import {
  BrokerCredentialResponse,
  deleteBrokerCredentials,
  getBrokerCredentials,
  getIciciLoginUrl,
  saveBrokerCredentials,
  authenticateIciciSession,
} from '../../services/brokerApi';
import { useToast } from '../../context/ToastContext';

export const BrokerSettings: React.FC = () => {
  const [credentials, setCredentials] = useState<BrokerCredentialResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [showIciciForm, setShowIciciForm] = useState<boolean>(false);
  const [showSessionModal, setShowSessionModal] = useState<boolean>(false);

  // Form states
  const [apiKey, setApiKey] = useState<string>('');
  const [apiSecret, setApiSecret] = useState<string>('');
  const [sessionToken, setSessionToken] = useState<string>('');

  const { showToast } = useToast();

  const fetchCredentials = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getBrokerCredentials();
      setCredentials(data);
    } catch {
      showToast('Failed to load broker credentials status.', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  const iciciCred = credentials.find((c) => c.provider_name === 'icici_breeze');

  const handleSaveIcici = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim() || !apiSecret.trim()) {
      showToast('Please enter both API Key and API Secret', 'error');
      return;
    }
    try {
      setSaving(true);
      await saveBrokerCredentials({
        provider_name: 'icici_breeze',
        api_key: apiKey.trim(),
        api_secret: apiSecret.trim(),
      });
      showToast('ICICI Breeze API credentials saved securely!', 'success');
      setApiKey('');
      setApiSecret('');
      setShowIciciForm(false);
      await fetchCredentials();
    } catch (err: unknown) {
      const msg = isAxiosError(err) && err.response?.data?.detail ? err.response.data.detail : 'Failed to save credentials';
      showToast(msg, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleOpenIciciLogin = async () => {
    try {
      const res = await getIciciLoginUrl();
      if (res.login_url) {
        window.open(res.login_url, '_blank', 'noopener,noreferrer');
        setShowSessionModal(true);
      }
    } catch (err: unknown) {
      const msg = isAxiosError(err) && err.response?.data?.detail ? err.response.data.detail : 'Please configure API Key first.';
      showToast(msg, 'error');
    }
  };

  const handleAuthenticateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sessionToken.trim()) {
      showToast('Please enter the session token obtained after login.', 'error');
      return;
    }
    try {
      setSaving(true);
      await authenticateIciciSession(sessionToken.trim());
      showToast('ICICI Breeze daily session authenticated successfully!', 'success');
      setSessionToken('');
      setShowSessionModal(false);
      await fetchCredentials();
    } catch (err: unknown) {
      const msg = isAxiosError(err) && err.response?.data?.detail ? err.response.data.detail : 'Authentication failed. Verify your token.';
      showToast(msg, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (provider: string) => {
    if (!window.confirm(`Are you sure you want to remove ${provider} integration?`)) return;
    try {
      await deleteBrokerCredentials(provider);
      showToast(`Deleted ${provider} credentials`, 'success');
      await fetchCredentials();
    } catch {
      showToast('Failed to delete credentials', 'error');
    }
  };


  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <KeyIcon className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            Broker API Integration (NFR12)
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Connect your broker account (ICICI Breeze) for direct real-time market data quotes.
          </p>
        </div>
        <button
          onClick={fetchCredentials}
          className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
          title="Refresh statuses"
        >
          <ArrowPathIcon className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* ICICI Breeze Card */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-5 bg-gray-50 dark:bg-gray-900/50 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center font-bold text-orange-600 dark:text-orange-400">
              ICICI
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">ICICI Direct Breeze API</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {iciciCred ? `API Key: ${iciciCred.api_key}` : 'Not Configured'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {iciciCred ? (
              iciciCred.is_authenticated ? (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
                  <CheckCircleIcon className="w-4 h-4" /> Active Session
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400">
                  <ExclamationCircleIcon className="w-4 h-4" /> Auth Required
                </span>
              )
            ) : (
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                Unconfigured
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons for ICICI */}
        <div className="flex flex-wrap items-center gap-3 pt-2">
          {!iciciCred ? (
            <button
              onClick={() => setShowIciciForm(!showIciciForm)}
              className="px-4 py-2 text-sm font-medium text-white bg-orange-600 hover:bg-orange-700 rounded-lg transition-colors"
            >
              Configure ICICI API Key
            </button>
          ) : (
            <>
              <button
                onClick={handleOpenIciciLogin}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg flex items-center gap-1.5 transition-colors"
              >
                <ArrowTopRightOnSquareIcon className="w-4 h-4" /> Login & Authenticate
              </button>
              <button
                onClick={() => setShowIciciForm(!showIciciForm)}
                className="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Edit Keys
              </button>
              <button
                onClick={() => handleDelete('icici_breeze')}
                className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                title="Delete Integration"
              >
                <TrashIcon className="w-5 h-5" />
              </button>
            </>
          )}
        </div>

        {/* Configure Credentials Form */}
        {showIciciForm && (
          <form onSubmit={handleSaveIcici} className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                ICICI Breeze API Key (App Key)
              </label>
              <input
                type="text"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter App Key"
                required
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                ICICI Breeze Secret Key
              </label>
              <input
                type="password"
                value={apiSecret}
                onChange={(e) => setApiSecret(e.target.value)}
                placeholder="Enter Secret Key"
                required
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                🔒 Credentials are encrypted using Fernet (AES-256) before storing in database.
              </p>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Encrypted Credentials'}
              </button>
              <button
                type="button"
                onClick={() => setShowIciciForm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Enter Session Token Modal / Panel */}
        {showSessionModal && (
          <form onSubmit={handleAuthenticateSession} className="pt-4 border-t border-indigo-200 dark:border-indigo-800 space-y-4 bg-indigo-50/50 dark:bg-indigo-950/30 p-4 rounded-lg">
            <h4 className="text-sm font-semibold text-indigo-900 dark:text-indigo-200">
              Complete ICICI Breeze OAuth Session Authentication
            </h4>
            <p className="text-xs text-indigo-700 dark:text-indigo-300">
              After logging in on ICICI Direct, copy the session token / API code displayed in the redirect URL or webpage response and paste it below:
            </p>
            <div>
              <input
                type="text"
                value={sessionToken}
                onChange={(e) => setSessionToken(e.target.value)}
                placeholder="Paste Session Token here"
                required
                className="w-full px-3 py-2 text-sm rounded-lg border border-indigo-300 dark:border-indigo-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:opacity-50"
              >
                {saving ? 'Validating...' : 'Validate Session Token'}
              </button>
              <button
                type="button"
                onClick={() => setShowSessionModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
              >
                Dismiss
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
