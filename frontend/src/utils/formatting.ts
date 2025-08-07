export const formatCurrency = (value: number | string) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
  }).format(Number(value));
};

export const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const formatPercentage = (value: number | undefined | null): string => {
  if (value === null || typeof value === 'undefined') return 'N/A';
  return `${(value * 100).toFixed(2)}%`;
};