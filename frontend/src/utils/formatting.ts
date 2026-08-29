import { usePrivacy } from '../context/PrivacyContext';

export const formatCurrency = (value: number | string, currency?: string | null) => {
  const numericValue = Number(value);
  const currencyCode = currency || 'INR';

  const formatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currencyCode,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  if (isNaN(numericValue) || value === null) {
    return formatter.format(0);
  }
  return formatter.format(numericValue).replace('₹-', '-₹');
};

export const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

export const formatPercentage = (value: number | undefined | null): string => {
  if (value === null || typeof value === 'undefined' || isNaN(value)) {
    return 'N/A';
  }
  return `${(value * 100).toFixed(2)}%`;
};

export const formatInterestRate = (value: number | string | undefined | null): string => {
  if (value === null || typeof value === 'undefined') {
    return 'N/A';
  }
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (typeof numValue !== 'number' || isNaN(numValue)) {
    return 'N/A';
  }
  return `${numValue.toFixed(2)}%`;
}

export const usePrivacySensitiveCurrency = () => {
  const { isPrivacyMode } = usePrivacy();

  const format = (value: number | string, currency?: string | null) => {
    if (isPrivacyMode) {
      return '₹**,***.**';
    }
    return formatCurrency(value, currency);
  };

  return format;
};

export const getCurrentFinancialYear = (date: Date = new Date()): string => {
  const year = date.getFullYear();
  const month = date.getMonth(); // 0-indexed: April is 3
  const startYear = month >= 3 ? year : year - 1;
  return `${startYear}-${startYear + 1}`;
};

export const getFinancialYearOptions = (
  currentDate: Date = new Date(),
  count: number = 4
): string[] => {
  const currentFY = getCurrentFinancialYear(currentDate);
  const startYear = parseInt(currentFY.split('-')[0], 10);
  const options: string[] = [];

  for (let i = 0; i < count; i++) {
    const y = startYear - i;
    options.push(`${y}-${y + 1}`);
  }
  return options;
};