const { createProxyMiddleware } = require('http-proxy-middleware');

// You can change this URL to your custom API address
const API_URL = 'https://your-custom-api-url.com';

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: API_URL,
      changeOrigin: true,
      secure: false, // In case your API uses HTTPS
      pathRewrite: {
        '^/api': '/api', // Keep /api prefix when forwarding
      },
    })
  );
}; 