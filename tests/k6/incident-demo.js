import http from 'k6/http';
import { check, sleep } from 'k6';

// Demo incident script — saturates PostgreSQL connections in ~10 seconds.
// Run: k6 run tests/k6/incident-demo.js
export const options = {
  stages: [
    { duration: '3s',  target: 150 },
    { duration: '10s', target: 150 },
    { duration: '2s',  target: 0 },
  ],
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const USERNAME = __ENV.API_USERNAME || 'demo';
const PASSWORD = __ENV.API_PASSWORD || 'orientops2026';

export function setup() {
  const res = http.post(
    `${BASE_URL}/token`,
    `username=${USERNAME}&password=${PASSWORD}`,
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
  );
  const token = res.json('access_token');
  if (!token) {
    throw new Error(`Auth failed: ${res.status} ${res.body}`);
  }
  return { token };
}

export default function (data) {
  const res = http.post(
    `${BASE_URL}/recommend`,
    JSON.stringify({ filiere_souhaitee: 'informatique', moyenne: 14.0, niveau_vise: 'BAC+3' }),
    { headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${data.token}`,
    }},
  );

  check(res, { 'status 200': (r) => r.status === 200 });
}
