<script>
  import { pct } from '$lib/format.js';
  export let data;
  const categories = data.analysis.pattern_detection?.categories || [];
</script>

<section class="page-head">
  <div>
    <h1>Pattern Library</h1>
    <p class="muted">Seven CI/CD architecture categories with adoption counts and examples.</p>
  </div>
</section>

<div class="grid">
  {#each categories as category}
    <section class="card">
      <h2>{category.category}</h2>
      <table class="table">
        <thead><tr><th>Pattern</th><th>Adoption</th><th>Examples</th></tr></thead>
        <tbody>
          {#each category.patterns as pattern}
            <tr>
              <td><a href={`/patterns/${pattern.slug}`}>{pattern.name}</a></td>
              <td>{pattern.repo_count} repos ({pct(pattern.adoption_pct)})</td>
              <td>{(pattern.repos || []).slice(0, 3).join(', ') || '-'}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </section>
  {/each}
</div>
