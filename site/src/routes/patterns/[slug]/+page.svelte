<script>
  export let data;
  const pattern = data.pattern;
</script>

{#if pattern}
  <section class="page-head">
    <div>
      <h1>{pattern.name}</h1>
      <p class="muted">{pattern.category} · Tier {pattern.tier}</p>
    </div>
    <span class="pill">{pattern.repo_count} repos</span>
  </section>
  <section class="card">
    <p>{pattern.description}</p>
    <h2>Examples</h2>
    <table class="table">
      <thead><tr><th>Repo</th><th>Workflow</th><th>Source</th></tr></thead>
      <tbody>
        {#each pattern.examples || [] as example}
          <tr><td>{example.repo}</td><td>{example.workflow || '-'}</td><td>{example.path || example.source_file || '-'}</td></tr>
        {/each}
      </tbody>
    </table>
  </section>
{:else}
  <section class="card"><h1>Pattern not found</h1></section>
{/if}
