# RazorBill — Frontend Dashboard

**Owner**: Person 4  
**Detailed Guide**: [`../docs/PERSON_4_FRONTEND_DEMO.md`](../docs/PERSON_4_FRONTEND_DEMO.md)  
**Contract Reference**: [`../SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md)

---

## Overview

The `frontend/` module is a high-performance web dashboard built with **React**, **Vite**, and **TypeScript**. It provides operators with live incident feeds, evidence frame inspections, category filters, aggregate statistics, conversational query search, and demo failover controls.

---

## Planned Directory Structure

```
frontend/
├── README.md
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── src/
│   ├── main.tsx           # React DOM root
│   ├── App.tsx            # App shell with navbar and tab/panel routing
│   ├── types/
│   │   └── contracts.ts   # TypeScript interfaces matching SHARED_CONTRACTS.md
│   ├── services/
│   │   └── api.ts         # Axios/Fetch client for backend endpoints
│   ├── components/
│   │   ├── MetricBar.tsx      # KPI stats summary cards
│   │   ├── IncidentFeed.tsx   # Live list/grid of incidents
│   │   ├── IncidentCard.tsx   # Individual card with image thumbnail
│   │   ├── FilterBar.tsx      # Category and camera select controls
│   │   ├── QueryPanel.tsx     # Conversational natural-language query bar
│   │   └── DemoModal.tsx      # Seed data fallback & scenario selector
│   └── mock/
│       └── fallbackData.ts    # Seeded incident array for offline demo
```

---

## Quickstart & Environment

```bash
# From frontend/
npm install
npm run dev
```

The application runs on `http://localhost:5173` and proxies or connects directly to the backend at `http://localhost:8000`.

---

## Core Engineering Directives

1. **Dual Timestamps**: Visually separate video source offset (`timestamp_seconds`, e.g. `00:42.5`) from wall-clock creation time (`created_at`, e.g. `21:45:00 UTC`).
2. **Contract Type Safety**: Use `types/contracts.ts` generated strictly from [`../SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md).
3. **Resilient Query UX**: When `POST /api/query` returns `unsupported`, render a clear clarification prompt (e.g., *"Try searching by category like 'fighting' or camera name"*), rather than breaking or presenting blank results.
4. **Offline Demo Readiness**: Provide a 1-click fallback toggle to load mock incidents from `mock/fallbackData.ts` if the backend connection is interrupted during presentation.

