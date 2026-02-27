/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/media/**',
      },
      {
        protocol: 'http',
        hostname: 'django',
        port: '8000',
        pathname: '/media/**',
      },
    ],
  },
  async rewrites() {
    const apiBase = process.env.INTERNAL_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/backend/:path*',
        destination: `${apiBase}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
