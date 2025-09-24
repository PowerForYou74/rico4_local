'use client'

import { useState, useEffect } from 'react'
import { getPrompts } from '@/lib/api'
import { Button } from '@/components/Button'
import { Plus, Edit, Trash2, Copy } from 'lucide-react'

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadPrompts()
  }, [])

  const loadPrompts = async () => {
    try {
      setLoading(true)
      const data = await getPrompts()
      setPrompts(data)
    } catch (error) {
      console.error('Failed to load prompts:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Prompt Library</h1>
          <p className="text-gray-600">Verwalten Sie Ihre System-Prompts</p>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Prompts</h2>
              <Button className="bg-green-600 hover:bg-green-700">
                <Plus className="h-4 w-4 mr-2" />
                Neuer Prompt
              </Button>
            </div>
          </div>
          
          <div className="p-6">
            {loading ? (
              <div className="text-center py-8">
                <p className="text-gray-500">Lade Prompts...</p>
              </div>
            ) : prompts.length > 0 ? (
              <div className="space-y-4">
                {prompts.map((prompt) => (
                  <div key={prompt.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{prompt.name}</h3>
                        <p className="text-sm text-gray-600 mb-2">
                          Role: {prompt.role} | Tags: {prompt.tags}
                        </p>
                        <p className="text-xs text-gray-500">
                          Erstellt: {new Date(prompt.created_at).toLocaleDateString('de-DE')}
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        <Button size="sm" variant="outline">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline">
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">Keine Prompts gefunden</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
