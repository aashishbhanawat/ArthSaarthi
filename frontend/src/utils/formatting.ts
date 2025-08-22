export const formatCurrency = (value: number | string, currency = 'INR') => {
  const numericValue = Number(value);
  if (isNaN(numericValue) || value === null) {
    return '₹0.00';
  }
  const formatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  // Handle negative numbers correctly by replacing the default minus sign
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