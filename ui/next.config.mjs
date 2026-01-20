/** @type {import('next').NextConfig} */
const nextConfig = {
  devIndicators: false,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  // Proxy API requests to the backend server
  async rewrites() {
    return [
      {
        source: "/chat",
        destination: "http://127.0.0.1:8000/chat",
      },
      {
        source: "/search/:path*",
        destination: "http://127.0.0.1:8000/search/:path*",
      },
      {
        source: "/weather/:path*",
        destination: "http://127.0.0.1:8000/weather/:path*",
      },
      {
        source: "/booking",
        destination: "http://127.0.0.1:8000/booking",
      },
      {
        source: "/health",
        destination: "http://127.0.0.1:8000/health",
      },
    ];
  },
};

export default nextConfig;
