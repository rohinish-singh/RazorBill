# RazorBill — Frontend Dashboard

**Owner**: Person 4  
**Detailed Guide**: [`../docs/PERSON_4_FRONTEND_DEMO.md`](../docs/PERSON_4_FRONTEND_DEMO.md)  
**Contract Reference**: [`../SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md)

---

## Overview

The `frontend/` module is a high-performance web dashboard built with **React**, **Vite**, and **TypeScript**. It provides operators with live monitoring, incident list/detail views with keyframes, interactive category and camera filters, conversational natural-language querying, and measured latency/evaluation metrics.

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
│   │   └── api.ts         # Central API client reading VITE_API_BASE_URL
│   ├── components/
│   │   ├── MetricBar.tsx      # Metrics panel showing measured latency
│   │   ├── IncidentFeed.tsx   # Live list of incidents with status
│   │   ├── IncidentDetail.tsx # Incident detail view with keyframe/evidence
│   │   ├── FilterBar.tsx      # Category, camera, and date filters
│   │   ├── QueryPanel.tsx     # Conversational NL query input and results
│   │   └── DemoModal.tsx      # Fallback mode using seeded demo data
│   └── mock/
│       └── mockData.ts        # Mock incident array matching shared contracts
```

---

## Quickstart & Environment

```bash
# From frontend/
npm install
npm run dev
```

### Environment Configuration
The frontend communicates exclusively with the backend via a configurable base URL:
```env
VITE_API_BASE_URL=http://localhost:8000
```
Never hardcode teammate-specific IP addresses or hostnames.

---

## Core Engineering Directives

1. **Independent Mock Mode**: Work with mock data immediately using the schema defined in `SHARED_CONTRACTS.md`. Do not wait for backend implementation to build the UI.
2. **Defensive UI States**: Provide comprehensive loading, empty, error, offline, and missing-frame states.
3. **Status Distinctions**: Distinctly indicate `candidate`, `classified`, `needs_review`, and `failed`. Show pending status rather than freezing the interface.
4. **Resilient Query UX**: When a query is unsupported, display a clear clarification response rather than breaking.
5. **No Fabricated Metrics**: Only display measured latency and verified evaluation data; clearly label mock data when operating in fallback mode.
