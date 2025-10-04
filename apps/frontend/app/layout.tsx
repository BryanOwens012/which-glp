import type React from "react";
import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { Analytics } from "@vercel/analytics/next";
import { Suspense } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default:
      "WhichGLP - GLP-1 Weight-Loss Drugs - Real-World Reviews & Outcomes",
    template: "%s | WhichGLP",
  },
  description:
    "Compare GLP-1 medications like Ozempic, Wegovy, Mounjaro, and Zepbound using real-world data. Make informed decisions based on thousands of user experiences, cost analysis, and outcome predictions.",
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
    "weight loss medication",
    "GLP-1 agonist",
    "drug comparison",
    "real user reviews",
    "medication outcomes",
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
    title: "WhichGLP - Real-World GLP-1 Drug Reviews & Outcomes",
    description:
      "Compare GLP-1 medications using real-world data from thousands of user experiences. Get personalized predictions for weight loss outcomes.",
    // images: [
    //   {
    //     url: "/og-image.png",
    //     width: 1200,
    //     height: 630,
    //     alt: "WhichGLP - GLP-1 Drug Comparison Platform",
    //   },
    // ],
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

const Scrim = ({ children }: { children: React.ReactNode }) => (
  <div className="w-full h-full relative">
    <div className="pointer-events-none fixed inset-0 z-[9999] h-screen w-screen backdrop-blur-[2px] flex items-center justify-center">
      <div className="pointer-events-auto">
        <div className="relative overflow-hidden rounded-2xl border border-border/40 px-8 py-6 shadow-2xl" style={{background: 'linear-gradient(135deg, oklch(0.65 0.15 150 / 0.98), oklch(0.55 0.18 240 / 0.98))'}}>
          <div className="flex items-center gap-3">
            <div className="h-2 w-2 animate-pulse rounded-full bg-white"></div>
            <span className="relative inline-block text-lg font-semibold tracking-tight">
              <span className="text-white">Coming soon!</span>
              <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent bg-[length:200%_100%] animate-[shimmer_2s_ease-in-out_infinite] bg-clip-text"></span>
            </span>
          </div>
        </div>
      </div>
    </div>
    {children}
  </div>
);

const RootLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => {
  return (
    <html lang="en">
      <body className={`font-sans ${GeistSans.variable} ${GeistMono.variable}`}>
        <Suspense fallback={null}>
          <Scrim>{children}</Scrim>
        </Suspense>
        <Analytics />
      </body>
    </html>
  );
};

export default RootLayout;
