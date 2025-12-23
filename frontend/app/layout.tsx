import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Todo AI Chatbot",
  description: "Manage your tasks with natural language using AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
