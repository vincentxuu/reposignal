import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.cwd(), '..');

export function loadAnalysis() {
  const file = path.join(root, 'data', 'analysis', 'current.json');
  if (!fs.existsSync(file)) {
    return emptyAnalysis();
  }
  return JSON.parse(fs.readFileSync(file, 'utf-8'));
}

export function loadRepoSources(owner, name) {
  // Build-time read of raw workflow YAML for a single repo (prerender only).
  const dir = path.join(root, 'data', 'raw', owner, name);
  if (!fs.existsSync(dir)) return {};
  const sources = {};
  for (const file of fs.readdirSync(dir)) {
    if (!/\.ya?ml$/.test(file)) continue;
    try {
      sources[file] = fs.readFileSync(path.join(dir, file), 'utf-8');
    } catch {
      // skip unreadable files
    }
  }
  return sources;
}

export function loadConfigBatch(name) {
  const file = path.join(root, 'data', 'configs', `${name}.json`);
  if (!fs.existsSync(file)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(file, 'utf-8'));
}

export async function loadRuntimeAnalysis(platform) {
  const kv = platform?.env?.REPOSIGNAL_KV;
  if (kv) {
    const value = await kv.get('analysis:current', { type: 'json' });
    if (value) return value;
  }
  return loadAnalysis();
}

function emptyAnalysis() {
  return {
    generated_at: null,
    total_repos: 0,
    total_workflows: 0,
    pattern_detection: { patterns: [], categories: [], detected_patterns: 0, total_patterns: 0 },
    security_posture: { average_score: 0, top: [], bottom: [], scores: [] },
    repo_summaries: [],
    workflow_changelog: { added_workflows: [], removed_workflows: [], changed_patterns: [] },
    data_quality: { status: 'unknown', issues: [] }
  };
}
