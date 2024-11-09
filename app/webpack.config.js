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

// Preload script configuration - Modified to be more explicit
const preloadConfig = {
    ...commonConfig,
    entry: {
        preload: './src/preload/preload.ts',
    },
    target: 'electron-preload',
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: '[name].js'
    },
    // Remove unnecessary rules
    module: {
        rules: [
            {
                test: /\.ts$/,
                include: /src/,
                use: [{ loader: 'ts-loader' }]
            }
        ]
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
module.exports = [mainConfig, preloadConfig, rendererConfig];