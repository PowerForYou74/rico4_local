'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Brain, TrendingUp, Euro, Users, FileText, Activity, Settings } from 'lucide-react'

const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Agents', href: '/agents', icon: Brain },
  { name: 'Cashbot', href: '/cashbot', icon: TrendingUp },
  { name: 'Finance', href: '/finance', icon: Euro },
  { name: 'Practice', href: '/practice', icon: Users },
  { name: 'Prompts', href: '/prompts', icon: FileText },
  { name: 'Runs', href: '/runs', icon: Activity },
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">RICO 4.0</h1>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navigation.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      isActive
                        ? 'border-blue-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    <item.icon className="h-4 w-4 mr-2" />
                    {item.name}
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
