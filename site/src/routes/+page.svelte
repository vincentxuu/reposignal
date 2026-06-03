<script>
  import { pct, repoHref } from '$lib/format.js';
  import BarChart from '$lib/charts/BarChart.svelte';
  import { categoryColor, CATEGORY_LEGEND } from '$lib/categoryColors.js';
  export let data;
  const analysis = data.analysis;
  const patterns = analysis.pattern_detection?.patterns || [];
  const topPatterns = patterns.slice(0, 8);
  const security = analysis.security_posture || {};
  const quality = analysis.data_quality || {};

  const topActions = (analysis.popular_actions_categorized || []).slice(0, 15).map((a) => ({
    label: a.action,
    value: a.count,
    color: categoryColor(a.category),
    href: a.url,
    sub: a.category
  }));
  const usedCategories = new Set((analysis.popular_actions_categorized || []).slice(0, 15).map((a) => a.category));
  const legend = CATEGORY_LEGEND.filter((c) => usedCategories.has(c.label));
</script>

<section class="page-head">
  <div>
    <h1>Engineering Intelligence Dashboard</h1>
    <p class="muted">Cross-repo CI/CD, security, and engineering-practice signals from open-source repositories.</p>
  </div>
  <span class="pill">Generated {analysis.generated_at || 'not yet'}</span>
</section>

<section class="grid stats">
  <div class="card"><div class="metric">{analysis.total_repos}</div><div class="label">Repositories</div></div>
  <div class="card"><div class="metric">{analysis.total_workflows}</div><div class="label">Workflows</div></div>
  <div class="card"><div class="metric">{patterns.filter((p) => p.repo_count > 0).length}</div><div class="label">Patterns detected</div></div>
  <div class="card"><div class="metric">{security.average_score || 0}</div><div class="label">Avg security score</div></div>
</section>

<section class="grid two" style="margin-top: 16px;">
  <div class="card">
    <h2>Pattern Adoption</h2>
    <BarChart
      items={topPatterns.map((p) => ({ label: p.name, value: Math.round(p.adoption_pct || 0), href: `/patterns/${p.slug}` }))}
      formatValue={(v) => `${v}%`}
    />
  </div>
  <div class="card">
    <h2>Security Leaders</h2>
    <table class="table">
      <thead><tr><th>Repo</th><th>Score</th></tr></thead>
      <tbody>
        {#each (security.top || []).slice(0, 8) as item}
          <tr>
            <td><a href={repoHref(item.repo)}>{item.repo}</a></td>
            <td>{item.score}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</section>

<section class="card" style="margin-top: 16px;">
  <div class="chart-head">
    <h2>Top 15 GitHub Actions</h2>
    <div class="legend">
      {#each legend as c}<span class="leg"><span class="dot" style={`background:${c.color}`}></span>{c.label}</span>{/each}
    </div>
  </div>
  <BarChart items={topActions} formatValue={(v) => v.toLocaleString()} />
</section>

<section class="grid two" style="margin-top: 16px;">
  <div class="card">
    <h2>Data Quality</h2>
    <p>Status: <strong>{quality.status}</strong></p>
    <p class="muted">Rows: {quality.row_count || 0}, duplicate workflows: {quality.duplicate_count || 0}</p>
    {#if quality.issues?.length}
      <ul>{#each quality.issues as issue}<li>{issue}</li>{/each}</ul>
    {/if}
  </div>
  <div class="card">
    <h2>Beyond CI Signals</h2>
    <p class="muted">Batch outputs loaded: {[data.batch1, data.batch2, data.batch3].filter(Boolean).length}/3</p>
    <p>File presence, config trends, release strategy, development environment, and decision-record signals are generated under <code>data/configs/</code>.</p>
  </div>
</section>

<style>
  .chart-head { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; flex-wrap: wrap; }
  .legend { display: flex; flex-wrap: wrap; gap: 10px; }
  .leg { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; color: #64748b; }
  .dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
</style>
