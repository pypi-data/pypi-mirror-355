const path = require('path');
const webpack = require('webpack');
const tsConfigPathPlugin = require('tsconfig-paths-webpack-plugin');

module.exports = {
  entry: './src/index.ts',
  mode: 'development',
  output: {
    path: path.resolve(__dirname, 'lib'),
    filename: 'index.js',
    libraryTarget: 'commonjs2',
  },
  devtool: 'eval-source-map',
  plugins: [
    new webpack.ProvidePlugin({
      process: 'process/browser',
    }),
  ],
  resolve: {
    plugins: [
      new tsConfigPathPlugin.TsconfigPathsPlugin({
        configFile: './tsconfig.json',
      }),
    ],
    extensions: ['.ts', '.js'],
    fallback: {
      url: false,
      buffer: false,
      crypto: false,
      // See https://github.com/webpack/webpack/blob/3471c776059ac2d26593ea39f9c47c1874253dbb/lib/ModuleNotFoundError.js#L13-L42
      path: require.resolve('path-browserify'),
      process: require.resolve('process/browser'),
    },
  },
  module: {
    rules: [
      {
        test: /\.ts$/,
        exclude: /node_modules/,
        use: [
          {
            loader: 'ts-loader',
          },
        ],
      },
    ],
  },
  externals: [
    // Everything that starts with "@phosphor/"
    /^@phosphor\/.+$/,
    /^@jupyterlab\/.+$/,
  ],
};
