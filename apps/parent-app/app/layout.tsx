import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "BabyEco - Parent",
  description: "Manage your family's behavioral incentive system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh">
      <body>{children}</body>
    </html>
  );
}
