import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getBrokerCredentials, syncBrokerApi, BrokerCredentialResponse } from '../../services/brokerApi';
import { ArrowPathIcon, CloudArrowDownIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/solid';

interface PortfolioOption {
  id: string;
  name: string;
}

interface BrokerApiSyncCardProps {
  portfolios: PortfolioOption[] | undefined;
  isLoadingPortfolios: boolean;
}

export const BrokerApiSyncCard: React.FC<BrokerApiSyncCardProps> = ({
  portfolios,
  isLoadingPortfolios,
}) => {
  const navigate = useNavigate();
  const broker = 'icici_breeze';
  const [selectedPortfolio, setSelectedPortfolio] = useState<string>('');
  const [importType, setImportType] = useState<'holdings' | 'trades'>('holdings');
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [asOfDate, setAsOfDate] = useState<string>('');
  
  const [credentials, setCredentials] = useState<BrokerCredentialResponse[]>([]);
  const [isLoadingCreds, setIsLoadingCreds] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadCredentials = async () => {
    try {
      setIsLoadingCreds(true);
      const data = await getBrokerCredentials();
      setCredentials(data);
    } catch (err) {
      console.error('Failed to load broker credentials', err);
    } finally {
      setIsLoadingCreds(false);
    }
  };

  useEffect(() => {
    loadCredentials();
  }, []);

  const activeCred = credentials.find((c) => c.provider_name === broker);
  const isConnected = activeCred && activeCred.is_active && activeCred.is_authenticated;

  const handleSync = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPortfolio) {
      alert('Please select a target portfolio.');
      return;
    }
    if (!isConnected) {
      alert('Please authenticate your broker account in Settings first.');
      return;
    }

    try {
      setIsSyncing(true);
      setErrorMsg(null);
      const session = await syncBrokerApi({
        provider_name: broker,
        portfolio_id: selectedPortfolio,
        import_type: importType,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        as_of_date: asOfDate || undefined,
      });

      if (session && session.id) {
        navigate(`/import/${session.id}/preview`);
      }
    } catch (err: any) {
      let detail = 'Failed to sync from broker API.';
      const resDetail = err.response?.data?.detail;
      if (typeof resDetail === 'string') {
        detail = resDetail;
      } else if (Array.isArray(resDetail)) {
        detail = resDetail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
      } else if (resDetail && typeof resDetail === 'object') {
        detail = JSON.stringify(resDetail);
      } else if (err.message) {
        detail = err.message;
      }
      setErrorMsg(detail);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="card max-w-2xl mx-auto mt-8 border border-blue-200 dark:border-blue-900 bg-blue-50/20 dark:bg-gray-800/40 p-6 rounded-xl shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <CloudArrowDownIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            Direct Broker API Sync (ICICI Breeze)
          </h2>
        </div>

        {/* Connection status badge */}
        <div>
          {isLoadingCreds ? (
            <span className="text-xs text-gray-500">Checking auth...</span>
          ) : isConnected ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300">
              <CheckCircleIcon className="h-3.5 w-3.5" />
              Connected
            </span>
          ) : activeCred ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300">
              <ExclamationTriangleIcon className="h-3.5 w-3.5" />
              Daily Auth Required
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
              Not Configured
            </span>
          )}
        </div>
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
        Sync current demat portfolio holdings or historical trade book / orders directly from your connected ICICI Direct Breeze account without file uploads.
      </p>

      <form onSubmit={handleSync} className="space-y-5">
        {/* Provider Info Banner */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm text-gray-900 dark:text-gray-100">Provider:</span>
            <span className="px-2 py-0.5 text-xs font-semibold rounded bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">
              ICICI Direct Breeze API
            </span>
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            For Zerodha, import Tradebook CSV via File Upload
          </span>
        </div>

        {/* Portfolio Selector */}
        <div className="form-group">
          <label htmlFor="broker-portfolio" className="form-label">
            Target Portfolio
          </label>
          <select
            id="broker-portfolio"
            value={selectedPortfolio}
            onChange={(e) => setSelectedPortfolio(e.target.value)}
            className="form-select"
            disabled={isLoadingPortfolios || isSyncing}
            required
          >
            <option value="" disabled>
              {isLoadingPortfolios ? 'Loading portfolios...' : 'Select a portfolio'}
            </option>
            {portfolios?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Import Type */}
        <div>
          <label className="form-label font-medium mb-2 block">Import Mode</label>
          <div className="flex gap-4">
            <label className="inline-flex items-center gap-2 cursor-pointer text-sm text-gray-800 dark:text-gray-200">
              <input
                type="radio"
                name="importType"
                value="holdings"
                checked={importType === 'holdings'}
                onChange={() => setImportType('holdings')}
                className="form-radio text-blue-600"
              />
              Current Holdings Snapshot
            </label>
            <label className="inline-flex items-center gap-2 cursor-pointer text-sm text-gray-800 dark:text-gray-200">
              <input
                type="radio"
                name="importType"
                value="trades"
                checked={importType === 'trades'}
                onChange={() => setImportType('trades')}
                className="form-radio text-blue-600"
              />
              Trade Book History
            </label>
          </div>
        </div>

        {/* Date pickers for holdings or trades */}
        {importType === 'holdings' && (
          <div className="pt-2 space-y-2">
            <div className="flex items-start gap-2 p-2.5 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
              <ExclamationTriangleIcon className="h-4 w-4 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-amber-800 dark:text-amber-300">
                <strong>Note:</strong> The ICICI holdings API returns a current portfolio snapshot with average purchase prices, but <strong>does not include original buy dates</strong>. All transactions will be dated with the snapshot date below. For full historical trade dates, switch to <strong>Trade Book History</strong> mode above.
              </p>
            </div>
            <label className="form-label text-xs">
              Import Date for All Holdings
              <span className="text-gray-400 dark:text-gray-500 ml-1">(defaults to today)</span>
            </label>
            <input
              type="date"
              value={asOfDate}
              onChange={(e) => setAsOfDate(e.target.value)}
              className="form-input text-sm"
            />
          </div>
        )}

        {importType === 'trades' && (
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div>
              <label className="form-label text-xs">From Date (Optional)</label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="form-input text-sm"
              />
            </div>
            <div>
              <label className="form-label text-xs">To Date (Optional)</label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="form-input text-sm"
              />
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div className="alert alert-error text-sm p-3 rounded-lg bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300">
            {errorMsg}
          </div>
        )}

        {/* Sync Trigger Button */}
        <div className="pt-2">
          {isConnected ? (
            <button
              type="submit"
              className="btn btn-primary w-full flex items-center justify-center gap-2 py-2.5"
              disabled={isSyncing || !selectedPortfolio}
            >
              {isSyncing ? (
                <>
                  <ArrowPathIcon className="h-5 w-5 animate-spin" />
                  Syncing from ICICI Breeze...
                </>
              ) : (
                <>
                  <CloudArrowDownIcon className="h-5 w-5" />
                  Sync & Preview {importType === 'holdings' ? 'Holdings' : 'Trade Book'}
                </>
              )}
            </button>
          ) : (
            <div className="text-center p-3 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm text-gray-600 dark:text-gray-400">
              Please configure and authenticate ICICI Breeze under{' '}
              <button
                type="button"
                onClick={() => navigate('/profile')}
                className="text-blue-600 dark:text-blue-400 font-semibold underline"
              >
                Profile / Settings
              </button>{' '}
              to use direct sync.
            </div>
          )}
        </div>
      </form>
    </div>
  );
};
