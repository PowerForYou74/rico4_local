import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Navigation } from '@/components/Navigation'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'RICO 4.0 Ops Hub',
  description: 'Produktionsreife Rico-Zentrale mit Ops Hub, Cashbot und Finanz-KPIs',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="de">
      <body className={inter.className}>
        <div className="min-h-screen bg-background">
          <Navigation />
          {children}
        </div>
      </body>
    </html>
  )
}
