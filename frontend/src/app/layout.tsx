import './globals.css'

export const metadata = {
  title: 'Rico V5 System',
  description: 'AI Provider Orchestration System',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}