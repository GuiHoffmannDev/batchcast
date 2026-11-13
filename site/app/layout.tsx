import type { Metadata } from "next";
import { Schibsted_Grotesk } from "next/font/google";
import { site } from "@/content";
import "./globals.css";

const schibsted = Schibsted_Grotesk({
  variable: "--font-schibsted",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: site.title,
  description: site.description,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${schibsted.variable} antialiased`}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
