const path = require('path');
module.exports = {
  entry: './src/index.tsx',
  output: {
    filename: 'index.js',
    path: path.resolve(__dirname, 'dist'),
    libraryTarget: 'umd',
  },
  resolve: { extensions: ['.js', '.ts', '.tsx'] },
  module: {
    rules: [{ test: /\.tsx?$/, loader: 'ts-loader' }]
  }
};