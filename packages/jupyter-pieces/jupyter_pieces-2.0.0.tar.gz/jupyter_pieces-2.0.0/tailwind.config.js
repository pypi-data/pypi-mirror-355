/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.ts',
    './style/**/*.css',
    './node_modules/copilot/src/**/*.ts',
    './node_modules/copilot/src/style/copilot.css',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
  corePlugins: {
    preflight: false,
  },
};
