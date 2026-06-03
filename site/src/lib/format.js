export function pct(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

export function repoHref(repo) {
  const [owner, name] = repo.split('/');
  return `/repos/${owner}/${name}`;
}
