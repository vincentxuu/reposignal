<script>
  // SVG histogram. values: number[]; bins across [min,max].
  export let values = [];
  export let bins = 10;
  export let min = 0;
  export let max = 100;
  export let unit = '';
  export let color = '#0891b2';

  const W = 640, H = 220, padL = 34, padR = 12, padT = 12, padB = 28;
  const step = (max - min) / bins;
  const counts = Array.from({ length: bins }, () => 0);
  for (const v of values) {
    if (v == null || Number.isNaN(+v)) continue;
    let i = Math.floor((+v - min) / step);
    if (i < 0) i = 0;
    if (i >= bins) i = bins - 1;
    counts[i] += 1;
  }
  const peak = Math.max(1, ...counts);
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;
  const bw = plotW / bins;
  const yTicks = 4;
  const x0 = (i) => padL + i * bw;
  const barH = (c) => (c / peak) * plotH;
</script>

<svg viewBox={`0 0 ${W} ${H}`} class="hist" role="img" aria-label="distribution histogram">
  {#each Array(yTicks + 1) as _, t}
    {@const y = padT + plotH - (t / yTicks) * plotH}
    <line x1={padL} y1={y} x2={W - padR} y2={y} stroke="#e2e8f0" stroke-width="1" />
    <text x={padL - 6} y={y + 4} text-anchor="end" class="ax">{Math.round((t / yTicks) * peak)}</text>
  {/each}
  {#each counts as c, i}
    <rect x={x0(i) + 2} y={padT + plotH - barH(c)} width={bw - 4} height={barH(c)} fill={color} rx="2">
      <title>{Math.round(min + i * step)}–{Math.round(min + (i + 1) * step)}{unit}: {c}</title>
    </rect>
  {/each}
  {#each Array(bins + 1) as _, i}
    {#if i % 2 === 0}
      <text x={x0(i)} y={H - 8} text-anchor="middle" class="ax">{Math.round(min + i * step)}</text>
    {/if}
  {/each}
</svg>

<style>
  .hist { width: 100%; height: auto; display: block; }
  .ax { fill: #94a3b8; font-size: 10px; font-variant-numeric: tabular-nums; }
</style>
