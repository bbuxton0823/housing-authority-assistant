import type React from "react";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Housing Authority Assistant",
  description: "Multi-agent assistant for HQS inspections, Section 8 services, HPS appointments, and general housing questions",
  icons: {
    icon: "/openai_logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
