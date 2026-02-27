/** @type {import('next').NextConfig} */

// Allow overriding the media host in production via environment variable.
// Example: NEXT_PUBLIC_MEDIA_HOST=api.novelsfactory.com
const mediaHost = process.env.NEXT_PUBLIC_MEDIA_HOST;

const remotePatterns = [
  // Local development — Django dev server
  { protocol: 'http',  hostname: 'localhost', port: '8000', pathname: '/media/**' },
  // Docker Compose service name
  { protocol: 'http',  hostname: 'django',    port: '8000', pathname: '/media/**' },
];

if (mediaHost) {
  remotePatterns.push({
    protocol: 'https',
    hostname: mediaHost,
    port: '',
    pathname: '/media/**',
  });
}

const nextConfig = {
  output: 'standalone',
  images: { remotePatterns },
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
