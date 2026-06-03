<script>
  export let data;
  let left = data.repos[0] || '';
  let right = data.repos[1] || data.repos[0] || '';
  let stack = 'python';
  let output = '';

  async function callTool(url) {
    const res = await fetch(url);
    output = JSON.stringify(await res.json(), null, 2);
  }
</script>

<section class="page-head">
  <div>
    <h1>CI/CD Tools</h1>
    <p class="muted">Interactive utilities backed by RepoSignal analysis data.</p>
  </div>
</section>

<section class="grid two">
  <div class="card">
    <h2>Workflow Diff</h2>
    <label for="left-repo">Left repo</label>
    <select id="left-repo" bind:value={left}>{#each data.repos as repo}<option>{repo}</option>{/each}</select>
    <label for="right-repo">Right repo</label>
    <select id="right-repo" bind:value={right}>{#each data.repos as repo}<option>{repo}</option>{/each}</select>
    <button on:click={() => callTool(`/api/diff?left=${encodeURIComponent(left)}&right=${encodeURIComponent(right)}`)}>Compare</button>
  </div>

  <div class="card">
    <h2>Workflow Generator</h2>
    <label for="stack">Stack</label>
    <select id="stack" bind:value={stack}>
      <option>python</option>
      <option>node</option>
      <option>rust</option>
      <option>docker</option>
    </select>
    <button on:click={() => callTool(`/api/workflow-generator?stack=${encodeURIComponent(stack)}`)}>Generate</button>
  </div>

  <div class="card">
    <h2>Operations</h2>
    <button on:click={() => callTool('/api/ai-reviewer-kit')}>AI reviewer kit</button>
    <button on:click={() => callTool(`/api/ci-copilot?repo=${encodeURIComponent(left)}`)}>CI copilot</button>
    <button on:click={() => callTool('/api/flaky-test-detective')}>Flaky test detective</button>
    <button on:click={() => callTool('/api/migrator?from=gitlab&to=github')}>Workflow migrator</button>
    <button on:click={() => callTool(`/api/health-check/${left}`)}>Repo health check</button>
  </div>

  <div class="card">
    <h2>Result</h2>
    <pre>{output || 'Run a tool to see JSON output.'}</pre>
  </div>
</section>
