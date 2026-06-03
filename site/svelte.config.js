import adapter from '@sveltejs/adapter-cloudflare';

const config = {
  kit: {
    // Every page is prerendered; only the API endpoints need the Pages
    // Function. Including just /api/* keeps _routes.json tiny and avoids the
    // 100-rule limit that 200+ prerendered repo pages would otherwise blow past.
    adapter: adapter({ routes: { include: ['/api/*'], exclude: [] } }),
    alias: {
      $data: '../data'
    }
  }
};

export default config;
