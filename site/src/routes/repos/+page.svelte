<script>
  import { repoHref } from '$lib/format.js';
  export let data;

  let query = '';
  let sortKey = 'security_score';
  let sortDir = 'desc';

  const SORTS = [
    { key: 'repo', label: 'Name' },
    { key: 'workflow_count', label: 'Workflows' },
    { key: 'maturity_pct', label: 'Maturity' },
    { key: 'security_score', label: 'Security' },
    { key: 'pattern_count', label: 'Patterns' }
  ];

  function setSort(key) {
    if (sortKey === key) {
      sortDir = sortDir === 'desc' ? 'asc' : 'desc';
    } else {
      sortKey = key;
      sortDir = key === 'repo' ? 'asc' : 'desc';
    }
  }

  $: filtered = data.repos
    .filter((r) => r.repo.toLowerCase().includes(query.trim().toLowerCase()))
    .sort((a, b) => {
      const av = a[sortKey] ?? -1;
      const bv = b[sortKey] ?? -1;
      const cmp = typeof av === 'string' ? av.localeCompare(bv) : av - bv;
      return sortDir === 'asc' ? cmp : -cmp;
    });
</script>

<section class="page-head">
  <div>
    <h1>Repositories</h1>
    <p class="muted">All {data.repos.length} analyzed repos. Search, sort, and open any repo for its parsed config and raw workflow YAML.</p>
  </div>
  <span class="pill">{filtered.length} shown</span>
</section>

<section class="card">
  <input class="search" type="search" placeholder="Filter repositories…" bind:value={query} />
  <table class="table">
    <thead>
      <tr>
        {#each SORTS as s}
          <th>
            <button class="th-sort" on:click={() => setSort(s.key)}>
              {s.label}{#if sortKey === s.key}<span class="arrow">{sortDir === 'asc' ? '▲' : '▼'}</span>{/if}
            </button>
          </th>
        {/each}
        <th>Signals</th>
      </tr>
    </thead>
    <tbody>
      {#each filtered as r}
        <tr>
          <td><a href={repoHref(r.repo)}>{r.repo}</a></td>
          <td>{r.workflow_count}</td>
          <td>{r.maturity_pct}%</td>
          <td>{r.security_score ?? '—'}</td>
          <td>{r.pattern_count}</td>
          <td class="sig">
            {#if r.has_matrix}<span class="tag">matrix</span>{/if}
            {#if r.has_permissions}<span class="tag">perms</span>{/if}
            {#if r.has_security_scan}<span class="tag sec">security</span>{/if}
            {#if r.has_ai_review}<span class="tag ai">AI</span>{/if}
            {#if r.has_cache}<span class="tag">cache</span>{/if}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</section>

<style>
  .search { margin-bottom: 12px; }
  .th-sort {
    width: auto; min-height: 0; margin: 0; padding: 0;
    background: none; border: none; color: #475569;
    font: inherit; font-size: 12px; text-transform: uppercase;
    cursor: pointer; display: inline-flex; gap: 4px; align-items: center;
  }
  .th-sort:hover { color: #0f172a; background: none; }
  .arrow { font-size: 9px; }
  .sig { display: flex; flex-wrap: wrap; gap: 4px; }
  .tag {
    font-size: 11px; padding: 2px 7px; border-radius: 999px;
    background: #eef2f6; color: #475569;
  }
  .tag.sec { background: #fee2e2; color: #b91c1c; }
  .tag.ai { background: #fce7f3; color: #be185d; }
</style>
