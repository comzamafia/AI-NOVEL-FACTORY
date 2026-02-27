import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import Navbar from "@/components/Navbar";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "NovelFactory — AI-Crafted Stories",
  description:
    "Discover compelling AI-crafted novels. Read chapter by chapter or grab the full book on Amazon.",
  openGraph: {
    title: "NovelFactory — AI-Crafted Stories",
    description: "Discover compelling AI-crafted novels. Read chapter by chapter.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-slate-900 text-slate-100 min-h-screen`}
      >
        <Navbar />
        <main className="min-h-[calc(100vh-64px)]">{children}</main>

        {/* Footer */}
        <footer className="bg-slate-900 border-t border-slate-800 py-8 mt-16">
          <div className="max-w-7xl mx-auto px-4 text-center text-slate-500 text-sm">
            <p>© {new Date().getFullYear()} NovelFactory. AI-crafted stories for curious readers.</p>
            <p className="mt-1">
              All books are AI-assisted and published independently.{' '}
              <a href="/subscribe" className="text-amber-400 hover:text-amber-300 underline">
                Subscribe for unlimited access.
              </a>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
