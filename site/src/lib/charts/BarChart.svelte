<script>
  // Horizontal bar chart. items: [{ label, value, color?, href?, sub? }]
  export let items = [];
  export let unit = '';
  export let formatValue = (v) => `${v}${unit}`;
  const max = Math.max(1, ...items.map((d) => Number(d.value) || 0));
</script>

<div class="barchart">
  {#each items as d}
    <div class="bc-row">
      <div class="bc-label" title={d.label}>
        {#if d.href}<a href={d.href}>{d.label}</a>{:else}{d.label}{/if}
        {#if d.sub}<span class="bc-sub">{d.sub}</span>{/if}
      </div>
      <div class="bc-track">
        <span class="bc-fill" style={`width:${(Number(d.value) || 0) / max * 100}%;background:${d.color || 'linear-gradient(90deg,#0891b2,#22c55e)'}`}></span>
      </div>
      <div class="bc-value">{formatValue(d.value)}</div>
    </div>
  {/each}
</div>

<style>
  .barchart { display: grid; gap: 2px; }
  .bc-row {
    display: grid;
    grid-template-columns: minmax(140px, 230px) 1fr 64px;
    gap: 12px;
    align-items: center;
    padding: 6px 0;
  }
  .bc-label { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .bc-label a:hover { text-decoration: underline; }
  .bc-sub { color: #94a3b8; font-size: 11px; margin-left: 6px; }
  .bc-track { height: 12px; border-radius: 999px; background: #eef2f6; overflow: hidden; }
  .bc-fill { display: block; height: 100%; border-radius: 999px; }
  .bc-value { text-align: right; font-variant-numeric: tabular-nums; font-size: 13px; color: #334155; }
  @media (max-width: 860px) {
    .bc-row { grid-template-columns: minmax(110px, 160px) 1fr 56px; }
  }
</style>
