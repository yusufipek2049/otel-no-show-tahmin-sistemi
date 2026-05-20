import type { Metadata } from "next";
import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";

import "./globals.css";

const bodyFont = IBM_Plex_Sans({
  subsets: ["latin", "latin-ext"],
  variable: "--font-body",
  weight: ["400", "500", "600"],
});

const displayFont = Space_Grotesk({
  subsets: ["latin", "latin-ext"],
  variable: "--font-display",
  weight: ["500", "700"],
});

export const metadata: Metadata = {
  title: "Otel Gerçekleşmeme Takip Ekranı",
  description: "Riskli rezervasyonları arama ve takip havuzunda yöneten iç operasyon arayüzü.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="tr">
      <body className={`${bodyFont.variable} ${displayFont.variable}`}>{children}</body>
    </html>
  );
}
