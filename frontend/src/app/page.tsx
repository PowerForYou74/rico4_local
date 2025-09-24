export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Rico V5 System
          </h1>
          <p className="text-gray-600 mb-8">
            AI Provider Orchestration System
          </p>
          <div className="space-y-4">
            <div className="p-4 bg-green-50 rounded-lg">
              <h3 className="font-semibold text-green-800">Backend</h3>
              <p className="text-sm text-green-600">FastAPI running on port 8000</p>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold text-blue-800">Frontend</h3>
              <p className="text-sm text-blue-600">Next.js running on port 3000</p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <h3 className="font-semibold text-purple-800">n8n</h3>
              <p className="text-sm text-purple-600">Workflows running on port 5678</p>
            </div>
          </div>
          <div className="mt-8">
            <a 
              href="/api/health" 
              className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Check Health
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}