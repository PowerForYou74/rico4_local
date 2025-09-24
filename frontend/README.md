# Rico Orchestrator Frontend

Next.js 14 Frontend für das Rico Orchestrator System mit TypeScript, Zustand und shadcn/ui.

## 🚀 Quick Start

```bash
# Dependencies installieren
npm install

# Environment konfigurieren
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Development Server starten
npm run dev
```

## 📋 Features

- **Next.js 14** mit App Router
- **TypeScript** für Type Safety
- **Zustand** für State Management
- **shadcn/ui** für UI Components
- **Tailwind CSS** für Styling
- **Responsive Design** für alle Geräte

## 🛠️ Development

### Scripts

```bash
npm run dev          # Development Server
npm run build        # Production Build
npm run start        # Production Server
npm run lint         # ESLint
npm run type-check   # TypeScript Check
```

### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📱 Pages

### Dashboard (`/`)
- System Health Overview
- Quick Stats
- Provider Status
- Recent Activity
- Quick Actions

### Agent Workflows (`/agents`)
- Prompt Generator
- Run Analysis
- Knowledge Base Search
- Provider Selection

## 🎨 UI Components

### Core Components

- **Card** - Container für Content
- **Button** - Interaktive Buttons
- **Input** - Form Inputs
- **Textarea** - Multi-line Inputs
- **Select** - Dropdown Selection
- **Tabs** - Tab Navigation
- **Badge** - Status Indicators
- **Skeleton** - Loading States

### Custom Components

- **HealthPanel** - System Health Display
- **ProviderStatus** - Provider Status Indicators

## 🏗️ Architektur

### App Structure

```
src/
├── app/
│   ├── layout.tsx          # Root Layout
│   ├── page.tsx            # Dashboard
│   ├── providers.tsx       # App Providers
│   └── agents/
│       └── page.tsx        # Agent Workflows
├── components/
│   └── ui/                 # shadcn/ui Components
├── lib/
│   ├── api.ts             # API Client
│   └── utils.ts           # Utility Functions
└── store/
    └── app-store.ts        # Zustand Store
```

### State Management

Das System verwendet Zustand für State Management:

```typescript
// Store Structure
interface AppState {
  // System state
  systemHealth: SystemHealth | null
  isLoading: boolean
  error: string | null
  
  // UI state
  sidebarOpen: boolean
  theme: 'light' | 'dark' | 'system'
  
  // Actions
  setSystemHealth: (health: SystemHealth | null) => void
  setLoading: (loading: boolean) => void
  // ... more actions
}
```

### API Integration

```typescript
// API Client
export const api = {
  async getSystemHealth(): Promise<SystemHealth>
  async createPrompt(request: PromptRequest): Promise<PromptResponse>
  async createScan(request: ScanRequest): Promise<ScanResult>
  // ... more endpoints
}
```

## 🎨 Styling

### Tailwind CSS

Das System verwendet Tailwind CSS für Styling:

```css
/* Custom Styles */
.rico-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.rico-card {
  @apply bg-card border border-border rounded-lg shadow-sm;
}

.health-indicator {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium;
}
```

### Theme System

- **Light Theme** - Standard Light Mode
- **Dark Theme** - Dark Mode Support
- **System Theme** - Automatische Theme-Erkennung

## 📊 Components

### HealthPanel

```typescript
interface HealthPanelProps {
  health: SystemHealth | null
  isLoading: boolean
}
```

Zeigt System Health Status mit:
- Overall Status
- Provider Status
- Latency Information
- Error Handling

### Provider Status

```typescript
// Status Colors
.health-healthy    // Green
.health-unhealthy  // Red
.health-unknown    // Gray
```

## 🔧 Configuration

### Next.js Config

```javascript
// next.config.js
const nextConfig = {
  experimental: {
    appDir: true,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}
```

### Tailwind Config

```javascript
// tailwind.config.js
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Custom color palette
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

## 🧪 Testing

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

### Build Testing

```bash
npm run build
```

## 🚀 Deployment

### Development

```bash
npm run dev
```

### Production

```bash
npm run build
npm run start
```

### Docker

```bash
docker build -t rico-frontend .
docker run -p 3000:3000 rico-frontend
```

## 📱 Responsive Design

Das Frontend ist vollständig responsive:

- **Mobile** - Optimiert für Smartphones
- **Tablet** - Optimiert für Tablets
- **Desktop** - Optimiert für Desktop

### Breakpoints

```css
/* Tailwind Breakpoints */
sm: 640px   /* Small devices */
md: 768px   /* Medium devices */
lg: 1024px  /* Large devices */
xl: 1280px  /* Extra large devices */
2xl: 1536px /* 2X large devices */
```

## 🎯 Performance

### Optimizations

- **Next.js 14** - Latest Next.js Features
- **App Router** - Modern Routing
- **TypeScript** - Type Safety
- **Zustand** - Lightweight State Management
- **Tailwind CSS** - Optimized CSS

### Bundle Size

- **Tree Shaking** - Unused Code Elimination
- **Code Splitting** - Automatic Code Splitting
- **Image Optimization** - Next.js Image Optimization

## 🔒 Security

### Best Practices

- **Environment Variables** - Secure Configuration
- **Type Safety** - TypeScript for Safety
- **Input Validation** - Form Validation
- **XSS Protection** - Built-in Protection

## 🤝 Contributing

1. Fork das Repository
2. Erstelle einen Feature Branch
3. Committe deine Änderungen
4. Push zum Branch
5. Erstelle einen Pull Request

## 📄 Lizenz

MIT License - siehe LICENSE Datei für Details.
