import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CarbonTracker | AI-Powered Sustainability Index",
  description: "Track and optimize your daily carbon footprint in real-time using intelligent natural language activity parsing and scientifically accurate IPCC calculations.",
  keywords: ["sustainability", "carbon footprint tracker", "green technology", "climate action", "AI carbon accounting"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased selection:bg-forest-600/30 selection:text-forest-400">
        {children}
      </body>
    </html>
  );
}
