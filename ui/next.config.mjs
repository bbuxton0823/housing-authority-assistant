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
        source: "/voice/:path*",
        destination: "http://127.0.0.1:8000/voice/:path*",
      },
      {
        source: "/speech-to-text",
        destination: "http://127.0.0.1:8000/speech-to-text",
      },
      {
        source: "/recordings/:path*",
        destination: "http://127.0.0.1:8000/recordings/:path*",
      },
      {
        source: "/elevenlabs/:path*",
        destination: "http://127.0.0.1:8000/elevenlabs/:path*",
      },
    ];
  },
};

export default nextConfig;
