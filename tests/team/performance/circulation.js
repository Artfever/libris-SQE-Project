import http from 'k6/http';
import { Trend, Counter } from 'k6/metrics';
import { sleep } from 'k6';
import exec from 'k6/execution';

const config = JSON.parse(open(__ENV.CONFIG));
const base = config.base_url;
const borrowLatency = new Trend('borrow_latency_ms', true);
const returnLatency = new Trend('return_latency_ms', true);
const borrowCompleted = new Counter('borrow_completed');
const returnCompleted = new Counter('return_completed');
const unexpected = new Counter('unexpected_failures');
const operations = new Counter('operations');
const warmupEnds = Date.now() + 5000;

export const options = {
  noCookiesReset: true,
  scenarios: {
    circulation: {
      executor: 'constant-vus',
      vus: Number(__ENV.VUS || '1'),
      duration: '65s',
      gracefulStop: '10s',
    },
  },
  thresholds: {
    borrow_latency_ms: ['p(95)<1000'],
    return_latency_ms: ['p(95)<1000'],
    borrow_completed: ['count>0'],
    return_completed: ['count>0'],
    unexpected_failures: ['count==0'],
  },
};

let session;
let activeLoan;

function csrf() {
  const response = http.get(`${base}/api/auth/csrf`);
  if (response.status !== 200) exec.test.abort(`CSRF bootstrap HTTP ${response.status}`);
  const cookie = http.cookieJar().cookiesForURL(base)['XSRF-TOKEN'];
  if (!cookie || !cookie.length) exec.test.abort('CSRF cookie missing');
  return decodeURIComponent(cookie[0]);
}

function login() {
  const user = config.users[__VU - 1];
  if (!user) exec.test.abort(`No fixture for VU ${__VU}`);
  let token = csrf();
  const response = http.post(`${base}/api/auth/login`, JSON.stringify({
    username: user.username, password: user.password,
  }), { headers: { 'Content-Type': 'application/json', 'X-XSRF-TOKEN': token } });
  if (response.status !== 200) exec.test.abort(`Login HTTP ${response.status}`);
  token = csrf();
  session = { user, token };
}

function request(path, body) {
  return http.post(`${base}${path}`, body === null ? null : JSON.stringify(body), {
    headers: { 'Content-Type': 'application/json', 'X-XSRF-TOKEN': session.token },
  });
}

export default function () {
  if (!session) login();
  if (Date.now() < warmupEnds) { sleep(0.1); return; }
  if (activeLoan) {
    // A prior return failed; do not create a second loan until the state reconciles.
    const retry = request(`/api/borrow-records/${activeLoan}/return`, null);
    if (retry.status === 204) activeLoan = null;
    else { sleep(0.1); return; }
  }
  const payload = {
    bookId: session.user.book_id,
    studentId: config.student_id,
    borrowDate: config.borrow_date,
  };
  const borrow = request('/api/borrow-records', payload);
  operations.add(1);
  borrowLatency.add(borrow.timings.duration);
  if (borrow.status !== 201) {
    unexpected.add(1);
    exec.test.abort(`Borrow HTTP ${borrow.status}`);
  }
  borrowCompleted.add(1);
  activeLoan = borrow.json('id');
  const returned = request(`/api/borrow-records/${activeLoan}/return`, null);
  operations.add(1);
  returnLatency.add(returned.timings.duration);
  if (returned.status === 204) {
    returnCompleted.add(1);
    activeLoan = null;
  } else {
    unexpected.add(1);
    exec.test.abort(`Return HTTP ${returned.status}`);
  }
  sleep(0.05);
}
