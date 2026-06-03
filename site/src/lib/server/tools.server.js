export function findRepo(analysis, repoName) {
  return (analysis.repo_summaries || []).find((repo) => repo.repo === repoName);
}

export function diffRepos(left, right) {
  if (!left || !right) return null;
  const practiceKeys = ['has_matrix', 'has_permissions', 'has_ai_review', 'has_security_scan', 'has_cache', 'has_concurrency'];
  return {
    left: summarizeRepo(left, practiceKeys),
    right: summarizeRepo(right, practiceKeys),
    practice_delta: practiceKeys.map((key) => ({
      key,
      left: Boolean(left[key]),
      right: Boolean(right[key])
    })),
    workflow_delta: {
      left_only: workflowNames(left).filter((name) => !workflowNames(right).includes(name)),
      right_only: workflowNames(right).filter((name) => !workflowNames(left).includes(name))
    }
  };
}

export function generateWorkflow(stack = 'python') {
  const normalized = stack.toLowerCase();
  if (normalized.includes('node') || normalized.includes('javascript') || normalized.includes('typescript')) {
    return workflow('Node CI', 'npm ci\\nnpm test', "node-version: ['20', '22']");
  }
  if (normalized.includes('rust')) {
    return workflow('Rust CI', 'cargo test --locked', "rust: ['stable']");
  }
  if (normalized.includes('go') || normalized.includes('golang')) {
    return workflow('Go CI', 'go test ./...', "go: ['1.22', '1.23']");
  }
  if (normalized.includes('java') || normalized.includes('maven') || normalized.includes('gradle')) {
    return workflow('Java CI', 'mvn -B verify', "java: ['17', '21']");
  }
  if (normalized.includes('docker')) {
    return workflow('Docker CI', 'docker buildx build --load -t app:test .', "platform: ['linux/amd64']");
  }
  return workflow('Python CI', 'uv sync --frozen\\nuv run python -m pytest tests/ -q', "python-version: ['3.12', '3.13']");
}

export function aiReviewerKit() {
  return `name: AI PR Review
on:
  pull_request:
permissions:
  contents: read
  pull-requests: write
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          direct_prompt: Review this PR for correctness, security, and maintainability.`;
}

export function copilotRecommendations(repo, security) {
  if (!repo) return [];
  const recommendations = [];
  for (const item of repo.missing_en || []) {
    recommendations.push(`Add ${item}.`);
  }
  for (const item of security?.recommendations || []) {
    recommendations.push(item);
  }
  return recommendations.slice(0, 8);
}

export function flakySignals(analysis) {
  const pattern = (analysis.pattern_detection?.patterns || []).find((item) => item.slug === 'flaky-test-retry');
  return {
    count: pattern?.repo_count || 0,
    examples: pattern?.examples || [],
    guidance: [
      'Separate retry workflows from root-cause tracking.',
      'Capture test name, platform, runtime version, and failure signature.',
      'Trend flakes by package and owner before raising retry counts.'
    ]
  };
}

export function migrateWorkflow(from = 'gitlab', to = 'github') {
  return {
    from,
    to,
    notes: [
      'Map stages to jobs with explicit needs dependencies.',
      'Move cache keys to actions/cache or language-specific cache actions.',
      'Translate protected deploy jobs to GitHub environments.'
    ],
    template: generateWorkflow('python')
  };
}

function summarizeRepo(repo, practiceKeys) {
  return {
    repo: repo.repo,
    workflow_count: repo.workflow_count,
    maturity_pct: repo.maturity_pct,
    practices: Object.fromEntries(practiceKeys.map((key) => [key, Boolean(repo[key])]))
  };
}

function workflowNames(repo) {
  return (repo.workflows || []).map((workflow) => workflow.name);
}

function workflow(name, testCommand, matrixLine) {
  return `name: ${name}
on:
  push:
  pull_request:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        ${matrixLine}
    steps:
      - uses: actions/checkout@v4
      - run: ${testCommand}`;
}
