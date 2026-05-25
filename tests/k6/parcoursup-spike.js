import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

export const errorRate = new Rate('orient_errors');
export const recommendLatency = new Trend('orient_recommend_latency', true);

// Staged ramp-up simulating a Parcoursup results day traffic pattern.
// Phase 1: warm-up to nominal load (200 req/s).
// Phase 2: hold nominal load for 5 minutes.
// Phase 3: spike to Parcoursup peak (1 000 req/s over 3 minutes).
// Phase 4: hold the peak for 5 minutes — this is where DB saturation occurs.
// Phase 5: ramp back down.
export const options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '3m', target: 200 },
    { duration: '5m', target: 200 },
    { duration: '3m', target: 1000 },
    { duration: '5m', target: 1000 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    orient_errors: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

const PROFILES = [
  { filiere_souhaitee: 'informatique', moyenne: 14.5, niveau_vise: 'BAC+3' },
  { filiere_souhaitee: 'informatique', moyenne: 11.0, niveau_vise: 'BAC+2' },
  { filiere_souhaitee: 'gestion',      moyenne: 12.0, niveau_vise: 'BAC+2' },
  { filiere_souhaitee: 'gestion',      moyenne: 15.5, niveau_vise: 'BAC+5' },
  { filiere_souhaitee: 'commerce',     moyenne: 13.5, niveau_vise: 'BAC+3' },
  { filiere_souhaitee: 'droit',        moyenne: 15.0, niveau_vise: 'BAC+5' },
  { filiere_souhaitee: 'sciences',     moyenne: 16.0, niveau_vise: 'BAC+5' },
  { filiere_souhaitee: 'sante',        moyenne: 14.0, niveau_vise: 'BAC+3' },
  { filiere_souhaitee: 'langues',      moyenne: 13.0, niveau_vise: 'BAC+3' },
];

const HEADERS = { 'Content-Type': 'application/json' };

export default function () {
  const profile = PROFILES[Math.floor(Math.random() * PROFILES.length)];

  // Health probe (10% of traffic)
  if (Math.random() < 0.1) {
    const health = http.get(`${BASE_URL}/health`);
    check(health, { 'health ok': (r) => r.status === 200 });
  }

  // Recommendation request
  const res = http.post(
    `${BASE_URL}/recommend`,
    JSON.stringify(profile),
    { headers: HEADERS },
  );

  recommendLatency.add(res.timings.duration);

  const ok = check(res, {
    'status 200':          (r) => r.status === 200,
    'body has formations': (r) => {
      try {
        return JSON.parse(r.body).total >= 0;
      } catch {
        return false;
      }
    },
    'latency < 500ms':     (r) => r.timings.duration < 500,
  });

  errorRate.add(!ok);

  // Small think time to avoid pure hammering
  sleep(0.05);
}

export function handleSummary(data) {
  return {
    'tests/k6/results/summary.json': JSON.stringify(data, null, 2),
  };
}
