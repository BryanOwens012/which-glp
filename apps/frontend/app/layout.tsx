import type React from "react";
import type { Metadata, Viewport } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { Analytics as VercelAnalytics } from "@vercel/analytics/next";
import { Suspense } from "react";
import { Providers } from "@/components/providers";
import { Analytics } from "@/components/analytics";
import { SpeedInsights } from "@vercel/speed-insights/next";
import "./globals.css";

// Configure fonts with display: swap for better performance
const geistSans = GeistSans;
const geistMono = GeistMono;

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
};

export const metadata: Metadata = {
  title: {
    default: "WhichGLP - Weight-Loss Drugs - Real-World Reviews & Outcomes",
    template: "%s | WhichGLP",
  },
  description:
    "Compare weight-loss drugs like Ozempic and Zepbound using real-world data. Get recommendations based on your profile, location, and health conditions.",
  keywords: [
    "GLP-1",
    "agonist",
    "weight loss",
    "Ozempic",
    "Wegovy",
    "Mounjaro",
    "Zepbound",
    "Saxenda",
    "semaglutide",
    "tirzepatide",
    "weight loss drug",
    "GLP-1 agonist",
    "drug comparison",
    "real user reviews",
    "drug outcomes",
  ],
  authors: [{ name: "WhichGLP" }],
  creator: "WhichGLP",
  publisher: "WhichGLP",
  metadataBase: new URL("https://www.whichglp.com"),
  alternates: {
    canonical: "https://www.whichglp.com",
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://www.whichglp.com",
    siteName: "WhichGLP",
    title: "WhichGLP - Real-World Weight-Loss Drug Reviews & Outcomes",
    description:
      "Compare weight-loss drugs like Ozempic and Zepbound using real-world data. Get recommendations based on your profile, location, and health conditions.",
    images: [
      {
        url: "icon.png",
        width: 1200,
        height: 630,
        alt: "WhichGLP - GLP-1 Drug Comparison Platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "WhichGLP - Real-World GLP-1 Drug Reviews",
    description:
      "Compare weight-loss drugs like Ozempic and Zepbound using real-world data. Get recommendations based on your profile, location, and health conditions.",
    images: ["icon.png"],
    creator: "@whichglp",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

const RootLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => {
  return (
    <html lang="en">
      <head>
        {/* Preconnect to external domains for faster resource loading */}
        <link rel="preconnect" href="https://www.googletagmanager.com" />
        <link rel="dns-prefetch" href="https://www.googletagmanager.com" />
        <link rel="preconnect" href="https://www.google-analytics.com" />
        <link rel="dns-prefetch" href="https://www.google-analytics.com" />
        {/* Preconnect to API domain for faster tRPC requests */}
        <link
          rel="preconnect"
          href={process.env.NEXT_PUBLIC_API_URL?.replace("/trpc", "") || ""}
          crossOrigin="anonymous"
        />
        <link
          rel="dns-prefetch"
          href={process.env.NEXT_PUBLIC_API_URL?.replace("/trpc", "") || ""}
        />

        {/* Inline critical CSS for immediate render */}
        <style
          dangerouslySetInnerHTML={{
            __html: `
              :root {
                --background: oklch(1 0 0);
                --foreground: oklch(0.145 0 0);
                --primary: oklch(0.319 0.462 296.0);
                --primary-foreground: oklch(0.985 0 0);
                --muted: oklch(0.97 0 0);
                --muted-foreground: oklch(0.556 0 0);
                --border: oklch(0.922 0 0);
                --radius: 0.625rem;
              }
              .dark {
                --background: oklch(0.145 0 0);
                --foreground: oklch(0.985 0 0);
                --primary: oklch(0.667 0.326 274.1);
                --primary-foreground: oklch(0.145 0 0);
                --muted: oklch(0.269 0 0);
                --muted-foreground: oklch(0.708 0 0);
                --border: oklch(0.269 0 0);
              }
              * { border-color: var(--border); }
              body {
                background-color: var(--background);
                color: var(--foreground);
                font-family: system-ui, -apple-system, sans-serif;
                margin: 0;
              }
            `,
          }}
        />

        {/* Google tag (gtag.js) - deferred to load after page interactive */}
        {process.env.NEXT_PUBLIC_GA_TAG && (
          <>
            <script
              defer
              src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_TAG}`}
            ></script>
            <script
              defer
              dangerouslySetInnerHTML={{
                __html: `
                  window.dataLayer = window.dataLayer || [];
                  function gtag(){dataLayer.push(arguments);}
                  gtag('js', new Date());
                  gtag('config', '${process.env.NEXT_PUBLIC_GA_TAG}');
                `,
              }}
            />
          </>
        )}
      </head>
      <body className={`font-sans ${geistSans.variable} ${geistMono.variable}`}>
        <Providers>
          <Suspense fallback={null}>
            {/* <Scrim>{children}</Scrim> */}
            {children}
            <Analytics />
            <SpeedInsights />
          </Suspense>
          <VercelAnalytics />
        </Providers>
      </body>
    </html>
  );
};

export default RootLayout;
