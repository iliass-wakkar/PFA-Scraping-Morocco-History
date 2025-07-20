import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "../components/Navbar";
import { LanguageProvider } from "../contexts/LanguageContext";
import { SearchProvider } from '../contexts/SearchContext';
import { TimelineDataProvider } from '../contexts/TimelineDataContext';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: 'swap',
  preload: true,
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: 'swap',
  preload: true,
});

export const metadata: Metadata = {
  title: "Morocco History Timeline",
  description: "Explore the rich history of Morocco through an interactive timeline",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <link rel="icon" type="image/x-icon" href="/favicon.ico" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
        suppressHydrationWarning={true}
      >
        <LanguageProvider>
          <SearchProvider>
            <TimelineDataProvider>
              {/* Fixed background image for all pages */}
              <div className="fixed inset-0 w-screen h-screen -z-10 pointer-events-none select-none">
                
              </div>
              <Navbar />
              <div className="pt-20">
                {children}
              </div>
            </TimelineDataProvider>
          </SearchProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
