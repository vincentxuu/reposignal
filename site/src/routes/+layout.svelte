<script>
  import '../styles.css';
</script>

<div class="shell">
  <aside class="nav">
    <a class="brand" href="/">
      <span class="mark"></span>
      <span>RepoSignal</span>
    </a>
    <nav>
      <a href="/">Dashboard</a>
      <a href="/repos">Repos</a>
      <a href="/patterns">Patterns</a>
      <a href="/security">Security</a>
      <a href="/trends">Trends</a>
      <a href="/reports">Reports</a>
      <a href="/tools">Tools</a>
    </nav>
  </aside>
  <main>
    <slot />
  </main>
</div>
