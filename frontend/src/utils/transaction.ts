import { Transaction } from '../types/portfolio';

export const isEditable = (tx: Transaction): boolean => {
  if (tx.details && (tx.details as Record<string, unknown>)._fd_id) {
    return false;
  }
  if (tx.asset.asset_type === 'PPF' && tx.transaction_type === 'INTEREST_CREDIT') {
    return false;
  }
  return true;
};

export const isDeletable = (tx: Transaction): boolean => {
  if (tx.asset.asset_type === 'PPF' && tx.transaction_type === 'INTEREST_CREDIT') {
    return false;
  }
  if (tx.details && (tx.details as Record<string, unknown>)._fd_id) {
    return tx.transaction_type === 'FD_MATURITY';
  }
  return true;
};

export const getDisabledTitle = (tx: Transaction, action: 'edit' | 'delete'): string | undefined => {
  if (tx.asset.asset_type === 'PPF' && tx.transaction_type === 'INTEREST_CREDIT') {
    return `PPF interest credit transactions are system-generated and cannot be ${action === 'edit' ? 'modified' : 'deleted'}.`;
  }
  if (tx.details && (tx.details as Record<string, unknown>)._fd_id) {
    if (action === 'edit') {
      return 'Fixed Deposit transactions are system-generated and cannot be modified.';
    } else if (tx.transaction_type !== 'FD_MATURITY') {
      return 'Fixed Deposit transactions are system-generated and cannot be deleted.';
    }
  }
  return undefined;
};
