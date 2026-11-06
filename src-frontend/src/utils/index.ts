export function cn(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ');
}

export function formatNumber(num: number, decimals = 1): string {
  if (num === 0) return '0';
  if (Math.abs(num) < 1000) return num.toFixed(decimals);
  if (Math.abs(num) < 1000000) {
    return `${(num / 1000).toFixed(decimals)}K`;
  }
  return `${(num / 1000000).toFixed(decimals)}M`;
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getStatusColor(status: string): string {
  const statusLower = status.toLowerCase();
  if (statusLower === 'active' || statusLower === 'high' || statusLower === 'completed') {
    return 'text-green-600 bg-green-100';
  }
  if (statusLower === 'moderate') {
    return 'text-yellow-600 bg-yellow-100';
  }
  if (statusLower === 'on leave' || statusLower === 'draft') {
    return 'text-blue-600 bg-blue-100';
  }
  return 'text-gray-600 bg-gray-100';
}

export function getStatusBadge(status: string): string {
  const statusLower = status.toLowerCase();
  if (statusLower === 'active' || statusLower === 'high' || statusLower === 'completed') {
    return 'bg-green-100 text-green-800';
  }
  if (statusLower === 'moderate') {
    return 'bg-yellow-100 text-yellow-800';
  }
  if (statusLower === 'on leave' || statusLower === 'draft') {
    return 'bg-blue-100 text-blue-800';
  }
  return 'bg-gray-100 text-gray-800';
}

export function calculatePercentile(value: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((value / total) * 100);
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}