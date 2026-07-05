/**
 * layout.tsx — CarbonTracker Root Layout
 * =======================================
 * LOCKED: Do NOT modify during feature development.
 * Changes require team review. Controls: fonts, metadata, html/body shell.
 * 
 * Phase L: Added Poppins + Space Grotesk fonts and ThemeProvider wrapper.
 */
import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "../stores/themeStore";
import { AIStoreProvider } from "../stores/aiStore";

export const metadata: Metadata = {
  title: "CarbonTracker | AI-Powered Sustainability Index",
  description: "Track and optimize your daily carbon footprint in real-time using intelligent natural language activity parsing and scientifically accurate IPCC calculations.",
  keywords: ["sustainability", "carbon footprint tracker", "green technology", "climate action", "AI carbon accounting"],
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "CarbonTracker AI",
  },
};

export const viewport = {
  themeColor: "#10b981",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" data-theme="forest">
      <head>
        {/* PWA */}
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#10b981" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        {/* Fonts */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@300;400;500;600;700;800;900&family=Poppins:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased selection:bg-emerald-500/20 selection:text-emerald-300 bg-theme-base text-theme-primary">
        <AIStoreProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </AIStoreProvider>
        {/* Service Worker Registration */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js')
                    .then(function(reg) { console.log('[PWA] Service Worker registered:', reg.scope); })
                    .catch(function(err) { console.warn('[PWA] Service Worker registration failed:', err); });
                });
              }
            `
          }}
        />
      </body>
    </html>
  );
}
