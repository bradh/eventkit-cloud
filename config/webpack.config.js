var webpack = require('webpack');
var path = require('path');
var WriteFilePlugin = require('write-file-webpack-plugin');
var ExtractTextPlugin = require('extract-text-webpack-plugin');

var BASE_DIR = path.resolve('/var', 'lib', 'eventkit', 'eventkit_cloud', 'ui', 'static', 'ui')
var BUILD_DIR = path.resolve(BASE_DIR, 'build');
var APP_DIR = path.resolve(BASE_DIR, 'app');

var config = {
    entry: [
        'webpack-dev-server/client?http://0.0.0.0:8080', // WebpackDevServer host and port
        'webpack/hot/dev-server', // "only" prevents reload on syntax errors
        APP_DIR + '/index.js',
    ],
    output: {
        path: BUILD_DIR,
        filename: 'bundle.js',
        publicPath: BUILD_DIR
    }
    ,
    resolve: {
        extensions: ['', '.js', '.jsx']
    }
    ,
    module: {
        loaders: [
            {
                test: /\.jsx?$/,
                exclude: /node_modules/,
                loader: ['babel-loader'],
                query: {
                    presets: ['es2015', 'react']
                }
            },
            {
                test: /\.(jpe?g|png|gif|svg)$/i,
                loaders: [
                    'file?hash=sha512&digest=hex&name=[hash].[ext]',
                    'image-webpack?bypassOnDebug&optimizationLevel=7&interlaced=false'
                ]
            },
            {
                test: /\.css$/,
                loader: 'style-loader'
            }, {
                test: /\.css$/,
                loader: 'css-loader',
                query: {
                    modules: true,
                    localIdentName: '[name]__[local]___[hash:base64:5]'
                }
            }

        ],
    },
    plugins: [
        new webpack.HotModuleReplacementPlugin(),
        new WriteFilePlugin(),
        new ExtractTextPlugin('styles.css'),
    ],
    devServer: {
        hot: true,
        contentBase: BASE_DIR,
        outputPath: BUILD_DIR,
        host: "0.0.0.0",
        port: 8080,
    },
    watchOptions: {
        poll: true
    },
};

module.exports = config;