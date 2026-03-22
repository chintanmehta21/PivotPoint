export const sentimentData = {
  score: 32,
  label: 'Fear',
  description: 'Market participants showing elevated caution amid geopolitical uncertainty.',
  isPlaceholder: true,
  zones: [
    { min: 0, max: 20, label: 'Extreme Fear', color: 'negative' },
    { min: 20, max: 40, label: 'Fear', color: 'negative' },
    { min: 40, max: 60, label: 'Neutral', color: 'muted' },
    { min: 60, max: 80, label: 'Greed', color: 'positive' },
    { min: 80, max: 100, label: 'Extreme Greed', color: 'positive' },
  ],
}
