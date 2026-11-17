import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SellerFlow AI - E-commerce Settlement & Reconciliation Workspace",
  description: "Reconcile Amazon settlements, identify fee overcharges, and track true product margins.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col font-sans bg-[#F7F8FA]">{children}</body>
    </html>
  );
}
