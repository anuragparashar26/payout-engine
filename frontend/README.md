# Frontend

React + Vite frontend for Payout Engine.

## Prerequisites

- Node.js 18+
- Backend API running at http://localhost:8000

## Local Installation

```bash
npm install
```

Create a `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Development

```bash
npm run dev
```

Access at http://localhost:5173

## Docker Installation

The frontend is built via the root `docker-compose.yml`:

```bash
docker-compose up --build frontend
```

Frontend runs on port 5173.

## Build

```bash
npm run build
```