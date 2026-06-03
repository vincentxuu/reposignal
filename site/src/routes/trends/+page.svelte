<script>
  export let data;
  const changelog = data.analysis.workflow_changelog || {};
  const batch2 = data.batch2?.summary;
  const batch3 = data.batch3?.summary;
</script>

<section class="page-head">
  <div>
    <h1>Trends</h1>
    <p class="muted">Snapshot deltas and configuration-practice coverage.</p>
  </div>
</section>

<section class="grid two">
  <div class="card">
    <h2>Workflow Changelog</h2>
    <p>Added: {changelog.added_workflows?.length || 0}</p>
    <p>Removed: {changelog.removed_workflows?.length || 0}</p>
    <p>Pattern changes: {changelog.changed_patterns?.length || 0}</p>
  </div>
  <div class="card">
    <h2>Config Trends</h2>
    <p>TS strict repos: {batch2?.tsconfig_strict_repos || 0}</p>
    <p>Cargo workspace repos: {batch2?.cargo_workspace_repos || 0}</p>
    <p>Release signal repos: {batch3?.signals?.release_strategy?.repo_count || 0}</p>
  </div>
</section>
