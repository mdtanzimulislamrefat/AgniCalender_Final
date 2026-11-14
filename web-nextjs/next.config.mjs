/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export: the built site in out/ works on any static host
  // (GitHub Pages, Vercel static, Netlify, any web server) with no
  // Node server, no backend and no login.
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
