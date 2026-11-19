import React, { useCallback, useEffect, useState } from 'react';
import {
  BellIcon,
  CheckCircleIcon,
  XMarkIcon,
  BanknotesIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import {
  dismissAllCorporateActionEvents,
  dismissCorporateActionEvent,
  getCorporateActionEvents,
} from '../../services/corporateActionsApi';
import { CorporateActionEventItem } from '../../types/corporateActions';

interface CorporateActionNotificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCountChange?: (unreadCount: number) => void;
}

export const CorporateActionNotificationModal: React.FC<CorporateActionNotificationModalProps> = ({
  isOpen,
  onClose,
  onCountChange,
}) => {
  const [events, setEvents] = useState<CorporateActionEventItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [dismissingAll, setDismissingAll] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getCorporateActionEvents(undefined, 0, 50);
      setEvents(res.items);
      if (onCountChange) {
        onCountChange(res.unread_count);
      }
    } catch (err: unknown) {
      console.error('Failed to load corporate actions:', err);
      setError('Failed to load automated activity receipts.');
    } finally {
      setLoading(false);
    }
  }, [onCountChange]);

  useEffect(() => {
    if (isOpen) {
      fetchEvents();
    }
  }, [isOpen, fetchEvents]);

  const handleDismissOne = async (eventId: string) => {
    try {
      setActionLoading((prev) => ({ ...prev, [eventId]: true }));
      await dismissCorporateActionEvent(eventId);
      setEvents((prev) =>
        prev.map((e) => (e.id === eventId ? { ...e, status: 'DISMISSED' } : e))
      );
      const newUnread = events.filter(
        (e) => e.id !== eventId && e.status === 'NEW'
      ).length;
      if (onCountChange) {
        onCountChange(newUnread);
      }
    } catch (err: unknown) {
      console.error('Failed to dismiss event:', err);
    } finally {
      setActionLoading((prev) => ({ ...prev, [eventId]: false }));
    }
  };

  const handleDismissAll = async () => {
    try {
      setDismissingAll(true);
      await dismissAllCorporateActionEvents();
      setEvents((prev) => prev.map((e) => ({ ...e, status: 'DISMISSED' })));
      if (onCountChange) {
        onCountChange(0);
      }
    } catch (err: unknown) {
      console.error('Failed to dismiss all events:', err);
    } finally {
      setDismissingAll(false);
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(val);
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  if (!isOpen) return null;

  const unreadEvents = events.filter((e) => e.status === 'NEW');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col border border-gray-200 dark:border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400 rounded-lg">
              <BellIcon className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                Automated Activity
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Scheduled bond coupons, dividends, stock splits, and bonus issues
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {unreadEvents.length > 0 && (
              <button
                onClick={handleDismissAll}
                disabled={dismissingAll}
                className="px-3 py-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 rounded-md transition"
              >
                {dismissingAll ? 'Clearing...' : 'Dismiss All'}
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
              aria-label="Close"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="overflow-y-auto p-5 flex-1 space-y-3">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
              <ArrowPathIcon className="h-7 w-7 animate-spin mb-2" />
              <p className="text-sm">Loading activity receipts...</p>
            </div>
          ) : error ? (
            <div className="text-center py-8 text-rose-500 text-sm">{error}</div>
          ) : events.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <CheckCircleIcon className="h-12 w-12 text-gray-300 dark:text-gray-600 mb-2" />
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                No automated receipts recorded
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                Upcoming bond coupon payments, stock dividends, and corporate actions will appear here.
              </p>
            </div>
          ) : (
            events.map((event) => {
              const isUnread = event.status === 'NEW';
              const assetName =
                event.stock_name ||
                event.bond_name ||
                (event.details?.stock_name as string) ||
                (event.details?.bond_name as string) ||
                'Asset';

              const getBadgeConfig = (type: string) => {
                switch (type) {
                  case 'BOND_COUPON':
                    return {
                      label: 'Coupon Payout',
                      badgeColor:
                        'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300',
                      iconBg:
                        'bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-300',
                    };
                  case 'DIVIDEND':
                    return {
                      label: 'Dividend Payout',
                      badgeColor:
                        'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300',
                      iconBg:
                        'bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-300',
                    };
                  case 'BOND_MATURITY':
                    return {
                      label: 'Maturity Redemption',
                      badgeColor:
                        'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300',
                      iconBg:
                        'bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-300',
                    };
                  case 'SPLIT':
                    return {
                      label: 'Stock Split',
                      badgeColor:
                        'bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-300',
                      iconBg:
                        'bg-purple-100 dark:bg-purple-900/50 text-purple-600 dark:text-purple-300',
                    };
                  case 'BONUS':
                    return {
                      label: 'Bonus Shares',
                      badgeColor:
                        'bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300',
                      iconBg:
                        'bg-amber-100 dark:bg-amber-900/50 text-amber-600 dark:text-amber-300',
                    };
                  default:
                    return {
                      label: type,
                      badgeColor:
                        'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300',
                      iconBg:
                        'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300',
                    };
                }
              };

              const badge = getBadgeConfig(event.event_type);
              const hasCashAmount = Number(event.amount) > 0;
              const ratioText =
                (event.details?.split_ratio as string) ||
                (event.details?.bonus_ratio as string);

              return (
                <div
                  key={event.id}
                  className={`p-4 rounded-lg border transition-all ${
                    isUnread
                      ? 'bg-emerald-50/40 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800/60 shadow-sm'
                      : 'bg-gray-50 dark:bg-gray-700/30 border-gray-200 dark:border-gray-700 opacity-80'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg mt-0.5 ${badge.iconBg}`}>
                        <BanknotesIcon className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                            {assetName}
                          </h4>
                          <span
                            className={`px-2 py-0.5 text-xs font-semibold rounded-full ${badge.badgeColor}`}
                          >
                            {badge.label}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                          Date: {formatDate(event.event_date)} • Units: {Number(event.units).toLocaleString()}
                          {event.isin ? ` • ISIN: ${event.isin}` : ''}
                          {ratioText ? ` • Ratio: ${ratioText}` : ''}
                        </p>
                      </div>
                    </div>

                    <div className="text-right">
                      {hasCashAmount ? (
                        <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
                          +{formatCurrency(Number(event.amount))}
                        </div>
                      ) : ratioText ? (
                        <div className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                          {ratioText}
                        </div>
                      ) : null}
                      {isUnread && (
                        <button
                          onClick={() => handleDismissOne(event.id)}
                          disabled={actionLoading[event.id]}
                          className="mt-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 underline"
                        >
                          {actionLoading[event.id] ? 'Dismissing...' : 'Dismiss'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
