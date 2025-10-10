import type React from "react";
import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { Analytics as VercelAnalytics } from "@vercel/analytics/next";
import { Suspense } from "react";
import { Providers } from "@/components/providers";
import { Analytics } from "@/components/analytics";
import "./globals.css";

// Configure fonts with display: swap for better performance
const geistSans = GeistSans;
const geistMono = GeistMono;

export const metadata: Metadata = {
  title: {
    default: "WhichGLP - Weight-Loss Drugs - Real-World Reviews & Outcomes",
    template: "%s | WhichGLP",
  },
  description:
    "Compare weight-loss drugs like Ozempic, Wegovy, Mounjaro, and Zepbound using real-world data. Make informed decisions based on thousands of user experiences, cost analysis, and outcome predictions.",
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 5,
    userScalable: true,
  },
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
  metadataBase: new URL("https://whichglp.com"),
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://whichglp.com",
    siteName: "WhichGLP",
    title: "WhichGLP - Real-World Weight-Loss Drug Reviews & Outcomes",
    description:
      "Compare weight-loss drugs using real-world data from thousands of user experiences. Get personalized recommendations.",
    images: [
      {
        url: "/icon.svg",
        width: 1200,
        height: 630,
        alt: "WhichGLP - GLP-1 Drug Comparison Platform",
      },
    ],
  },
  // twitter: {
  //   card: "summary_large_image",
  //   title: "WhichGLP - Real-World GLP-1 Drug Reviews",
  //   description:
  //     "Compare GLP-1 medications using real-world data. Make informed decisions about weight loss drugs.",
  //   images: ["/twitter-image.png"],
  //   creator: "@whichglp",
  // },
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
  verification: {
    google: "google-site-verification-code",
  },
};

// "Coming Soon" scrim overlay - commented out for development
// Uncomment to show coming soon message over entire site
// const Scrim = ({ children }: { children: React.ReactNode }) => (
//   <div className="w-full h-full relative">
//     <div className="pointer-events-none fixed inset-0 z-[9999] h-screen w-screen backdrop-blur-[2px] flex items-center justify-center">
//       <div className="pointer-events-auto">
//         <div className="relative overflow-hidden rounded-2xl border border-border/40 px-8 py-6 shadow-2xl" style={{background: 'linear-gradient(135deg, oklch(0.65 0.15 150 / 0.98), oklch(0.55 0.18 240 / 0.98))'}}>
//           <div className="flex items-center gap-3">
//             <div className="h-2 w-2 animate-pulse rounded-full bg-white"></div>
//             <span className="relative inline-block text-lg font-semibold tracking-tight">
//               <span className="text-white">Coming soon!</span>
//               <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent bg-[length:200%_100%] animate-[shimmer_2s_ease-in-out_infinite] bg-clip-text"></span>
//             </span>
//           </div>
//         </div>
//       </div>
//     </div>
//     {children}
//   </div>
// );

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
        <link rel="preconnect" href={process.env.NEXT_PUBLIC_API_URL?.replace('/trpc', '') || ''} crossOrigin="anonymous" />
        <link rel="dns-prefetch" href={process.env.NEXT_PUBLIC_API_URL?.replace('/trpc', '') || ''} />

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
          </Suspense>
          <VercelAnalytics />
        </Providers>
      </body>
    </html>
  );
};

export default RootLayout;
