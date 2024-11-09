const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

// Create separate configurations for main and renderer processes
const commonConfig = {
    mode: 'development',
    devtool: 'source-map',
    module: {
        rules: [
            {
                test: /\.ts(x?)$/,
                include: /src/,
                use: [{ loader: 'ts-loader' }]
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            }
        ]
    },
    resolve: {
        extensions: ['.js', '.ts', '.tsx', '.jsx']
    }
};

// Main process configuration
const mainConfig = {
    ...commonConfig,
    entry: './src/main/main.ts',
    target: 'electron-main',
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'main.js'
    }
};

// Renderer process configuration
const rendererConfig = {
    ...commonConfig,
    entry: './src/renderer/index.tsx',
    target: 'electron-renderer',
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'renderer.js'
    },
    plugins: [
        new HtmlWebpackPlugin({
            template: './src/renderer/index.html'
        })
    ]
};

// Export array of configurations
module.exports = [mainConfig, rendererConfig];