<script>
  import BarChart from '$lib/charts/BarChart.svelte';
  export let data;
  const repo = data.repo;
  const security = data.security;
  const sources = data.sources || {};

  const base = (p) => (p || '').split('/').pop();
  const rawFor = (w) => sources[base(w.path)] ?? sources[base(w.source_file)] ?? null;

  const dimItems = security?.dimensions
    ? Object.entries(security.dimensions).map(([label, value]) => ({
        label: label.replace(/_/g, ' '),
        value: Math.round(value * 10) / 10
      }))
    : [];
</script>

{#if repo}
  <section class="page-head">
    <div>
      <h1>{repo.repo}</h1>
      <p class="muted">
        {repo.workflow_count} workflows · maturity {repo.maturity_pct}% · {repo.pattern_count} patterns
        · <a class="ext" href={repo.url} target="_blank" rel="noreferrer">GitHub ↗</a>
      </p>
    </div>
    <span class="pill">Security {security?.score ?? '—'}/100</span>
  </section>

  <section class="grid two">
    <div class="card">
      <h2>Practices</h2>
      <div class="flags">
        {#each [['Matrix', repo.has_matrix], ['Permissions', repo.has_permissions], ['Security scan', repo.has_security_scan], ['AI review', repo.has_ai_review], ['Cache', repo.has_cache], ['Concurrency', repo.has_concurrency], ['Reusable workflows', repo.has_reusable_workflows]] as [label, on]}
          <span class="flag" class:on>{on ? '✓' : '○'} {label}</span>
        {/each}
      </div>
      {#if repo.pattern_slugs?.length}
        <h2 style="margin-top:18px;">Detected patterns</h2>
        <div class="flags">
          {#each repo.pattern_slugs as slug}
            <a class="flag on" href={`/patterns/${slug}`}>{slug}</a>
          {/each}
        </div>
      {/if}
    </div>
    <div class="card">
      <h2>Security dimensions</h2>
      {#if dimItems.length}
        <BarChart items={dimItems} />
        {#if security?.security_tools?.length}
          <p class="muted small">Tools: {security.security_tools.join(', ')}</p>
        {/if}
      {:else}
        <p class="muted">No security signals detected.</p>
      {/if}
    </div>
  </section>

  <section class="card" style="margin-top:16px;">
    <h2>Workflows ({repo.workflows.length})</h2>
    {#each repo.workflows as workflow}
      <details class="wf">
        <summary>
          <span class="wf-name">{workflow.name}</span>
          <span class="wf-sig">
            {#if workflow.uses_matrix}<span class="tag">matrix</span>{/if}
            {#if workflow.has_permissions}<span class="tag">perms</span>{/if}
            {#if workflow.has_security_scan}<span class="tag sec">security</span>{/if}
            {#if workflow.has_ai_review}<span class="tag ai">AI</span>{/if}
          </span>
          <code class="wf-path">{workflow.path}</code>
        </summary>
        <div class="wf-body">
          <dl class="meta">
            <dt>Triggers</dt><dd>{workflow.triggers?.join(', ') || '—'}</dd>
            <dt>Runs on</dt><dd>{workflow.runs_on?.join(', ') || '—'}</dd>
            <dt>Jobs</dt><dd>{workflow.jobs?.join(', ') || workflow.job_count || '—'}</dd>
            {#if workflow.uses_matrix}<dt>Matrix</dt><dd>{(workflow.matrix_keys || []).join(', ')}{#if workflow.matrix_values?.length} → {workflow.matrix_values.flat().join(', ')}{/if}</dd>{/if}
            {#if workflow.notable_actions?.length}<dt>Actions</dt><dd>{workflow.notable_actions.join(', ')}</dd>{/if}
            {#if workflow.run_commands?.length}<dt>Commands</dt><dd><ul class="cmds">{#each workflow.run_commands.slice(0, 8) as cmd}<li>{cmd}</li>{/each}</ul></dd>{/if}
          </dl>
          {#if rawFor(workflow)}
            <details class="raw">
              <summary>View raw YAML</summary>
              <pre>{rawFor(workflow)}</pre>
            </details>
          {/if}
        </div>
      </details>
    {/each}
  </section>
{:else}
  <section class="card"><h1>Repository not found</h1></section>
{/if}

<style>
  .ext:hover { text-decoration: underline; }
  .small { font-size: 12px; margin-top: 10px; }
  .flags { display: flex; flex-wrap: wrap; gap: 6px; }
  .flag {
    font-size: 12px; padding: 3px 9px; border-radius: 999px;
    background: #f1f5f9; color: #94a3b8; border: 1px solid #e2e8f0;
  }
  .flag.on { background: #ecfdf5; color: #047857; border-color: #a7f3d0; }
  .wf { border-top: 1px solid #e2e8f0; padding: 4px 0; }
  .wf > summary {
    display: flex; align-items: center; gap: 10px; cursor: pointer;
    padding: 8px 2px; list-style: none;
  }
  .wf > summary::-webkit-details-marker { display: none; }
  .wf > summary::before { content: '▸'; color: #94a3b8; font-size: 11px; }
  .wf[open] > summary::before { content: '▾'; }
  .wf-name { font-weight: 600; font-size: 14px; }
  .wf-sig { display: flex; gap: 4px; }
  .wf-path { margin-left: auto; color: #94a3b8; font-size: 12px; }
  .wf-body { padding: 4px 0 12px 18px; }
  .meta { display: grid; grid-template-columns: 96px 1fr; gap: 4px 14px; margin: 0 0 10px; }
  .meta dt { color: #64748b; font-size: 12px; text-transform: uppercase; }
  .meta dd { margin: 0; font-size: 13px; }
  .cmds { margin: 0; padding-left: 16px; }
  .cmds li { font-family: ui-monospace, monospace; font-size: 12px; color: #334155; }
  .raw > summary { cursor: pointer; color: #0891b2; font-size: 13px; padding: 4px 0; }
  .tag { font-size: 11px; padding: 2px 7px; border-radius: 999px; background: #eef2f6; color: #475569; }
  .tag.sec { background: #fee2e2; color: #b91c1c; }
  .tag.ai { background: #fce7f3; color: #be185d; }
  @media (max-width: 860px) {
    .wf-path { display: none; }
    .meta { grid-template-columns: 1fr; }
  }
</style>
