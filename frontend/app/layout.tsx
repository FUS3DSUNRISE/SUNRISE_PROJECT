import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import ServiceStatusBoundary from "@/components/ServiceStatusBoundary";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ScaiLab 3D Generator",
  description: "Frontend for prompt-based 3D model generation.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <ServiceStatusBoundary>{children}</ServiceStatusBoundary>
      </body>
    </html>
  );
}
