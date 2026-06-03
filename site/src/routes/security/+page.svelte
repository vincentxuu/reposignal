<script>
  import Histogram from '$lib/charts/Histogram.svelte';
  import { repoHref } from '$lib/format.js';
  export let data;
  const scores = data.security.scores || [];
  const values = scores.map((s) => s.score);
  const sorted = [...values].sort((a, b) => a - b);
  const median = sorted.length ? sorted[Math.floor(sorted.length / 2)] : 0;
</script>

<section class="page-head">
  <div>
    <h1>Security Dashboard</h1>
    <p class="muted">Weighted posture score: permissions, scanners, supply chain, token handling, and runner hardening.</p>
  </div>
  <span class="pill">Average {data.security.average_score || 0}/100</span>
</section>

<section class="card">
  <h2>Score Distribution</h2>
  <p class="muted" style="margin-top:-6px;">{scores.length} repos · median {median} · 0–100 weighted posture score</p>
  <Histogram values={values} bins={10} min={0} max={100} color="#dc2626" />
</section>

<section class="card" style="margin-top:16px;">
  <table class="table">
    <thead><tr><th>Repository</th><th>Score</th><th>Tools</th><th>Next step</th></tr></thead>
    <tbody>
      {#each scores as item}
        <tr>
          <td><a href={repoHref(item.repo)}>{item.repo}</a></td>
          <td>{item.score}</td>
          <td>{(item.security_tools || []).join(', ') || '-'}</td>
          <td>{item.recommendations?.[0] || 'Keep current controls fresh.'}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</section>
