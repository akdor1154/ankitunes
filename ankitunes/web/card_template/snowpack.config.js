// Snowpack Configuration File
// See all supported options: https://www.snowpack.dev/reference/configuration

/** @type {import("snowpack").SnowpackUserConfig } */
module.exports = {
  root: '.',
  mount: {
      src: '/'
  },
  plugins: [
    /* ... */
  ],
  packageOptions: {
  },
  devOptions: {
    /* ... */
  },
  buildOptions: {
    out: 'dist'
  },
  mode: 'production',
  optimize: {
    entrypoints: ['src/template.ts'],
    bundle: true,
    minify: false,
    target: 'es2018'
  }
};
