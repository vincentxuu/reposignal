// Stable color per action category, used by charts and legends.
const COLORS = {
  'CI/Build': '#0891b2',
  Artifacts: '#6366f1',
  'Docker/Container': '#2563eb',
  'Cache/Performance': '#16a34a',
  'Cloud/Deploy': '#d97706',
  Security: '#dc2626',
  Automation: '#9333ea',
  AI: '#db2777',
  Other: '#64748b'
};

export function categoryColor(category) {
  return COLORS[category] || COLORS.Other;
}

export const CATEGORY_LEGEND = Object.entries(COLORS).map(([label, color]) => ({ label, color }));
