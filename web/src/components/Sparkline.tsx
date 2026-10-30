export function Sparkline({ values, height = 56 }: { values: number[]; height?: number }) {
  if (values.length < 2) return <p className="muted">The rating trend appears after two tracked matches.</p>;
  const w = 300;
  const min = Math.min(...values, 5);
  const max = Math.max(...values, 10);
  const x = (i: number) => (i / (values.length - 1)) * w;
  const y = (v: number) => height - 4 - ((v - min) / (max - min || 1)) * (height - 8);
  const points = values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${height}`} preserveAspectRatio="none" width="100%" height={height} role="img" aria-label="Match rating trend">
      <defs>
        <linearGradient id="spark" x1="0" x2="1">
          <stop offset="0" stopColor="var(--purple)" />
          <stop offset="1" stopColor="var(--green)" />
        </linearGradient>
      </defs>
      <polyline points={points} fill="none" stroke="url(#spark)" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}
