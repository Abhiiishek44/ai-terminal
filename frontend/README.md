# AI Terminal - Electron Frontend

A beautiful Electron desktop application for the AI Terminal backend. Convert natural language commands into executable terminal commands using AI.

## 🚀 Quick Start

### Prerequisites
- Node.js 20+ and npm
- Backend server running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install
```

### Development

```bash
# Run in development mode (React dev server + Electron)
npm start

# Or run separately:
# Terminal 1 - Start React dev server
npm run dev

# Terminal 2 - Start Electron
npm run electron:dev
```

### Production Build

```bash
# Build React app and package Electron
npm run package
```

## 🎨 Features

- **Beautiful UI**: Modern dark theme with smooth animations
- **Real-time AI**: Convert natural language to commands instantly
- **Command History**: View all your past queries and results
- **Safety Indicators**: Color-coded safety levels for commands

## 🔧 Configuration

Environment Variables (`.env`):
```env
VITE_API_URL=http://localhost:8000
```

## 📦 Scripts

- `npm start` - Run both Vite and Electron concurrently
- `npm run dev` - Start Vite dev server only
- `npm run electron:dev` - Start Electron in development mode
- `npm run build` - Build React app for production
- `npm run package` - Package app for distribution

## 🛠️ Built With

- **Electron** - Desktop app framework
- **React** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Axios** - HTTP client

## 📄 License

MIT License
