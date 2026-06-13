export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount)
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium' }).format(new Date(date))
}

export function burnRatioColor(ratio: number): string {
  if (ratio < 1.0) return 'text-green-600'
  if (ratio < 1.2) return 'text-yellow-500'
  if (ratio < 1.5) return 'text-orange-500'
  return 'text-red-600'
}

export function daysUntil(date: string | Date): number {
  return Math.ceil((new Date(date).getTime() - Date.now()) / 86400000)
}
