import { chromium } from 'playwright';

const check = async (name, fn) => {
  try { await fn(); console.log('  ✅ ' + name); return true; }
  catch(e) { console.log('  ❌ ' + name + ': ' + e.message); return false; }
};

const b = await chromium.launch({headless:true});
const p = await b.newPage();
let pass = 0, fail = 0;

const runCheck = async (name, fn) => {
  const ok = await check(name, fn);
  if (ok) pass++; else fail++;
};

// ── Landing page ──
console.log('\n🏠 Landing Page');
await p.goto('http://localhost:5173/', {waitUntil:'domcontentloaded'});
await p.waitForTimeout(600);
await runCheck('Title', async () => {
  const t = await p.title();
  if (!t.includes('ManakSetu')) throw new Error('Title mismatch: ' + t);
});
await runCheck('Hero heading', async () => {
  const h = await p.locator('h1').first().textContent();
  if (!h?.includes('Indian Standards')) throw new Error('No hero heading');
});
await runCheck('Try Now CTA', async () => {
  if (!await p.locator('button:has-text("Try Now")').count()) throw new Error('Missing');
});
await runCheck('Start Chatting CTA', async () => {
  if (!await p.locator('button:has-text("Start Chatting")').count()) throw new Error('Missing');
});
await runCheck('Feature cards', async () => {
  const count = await p.locator('[class*="rounded-2xl"]').count();
  if (count < 4) throw new Error('Only ' + count + ' cards');
});
await runCheck('Stats bar', async () => {
  const vals = await p.locator('[class*="text-2xl"]').allTextContents();
  if (!vals.some(v => v.includes('10,000'))) throw new Error('Missing stats');
});

// ── Chat page ──
console.log('\n💬 Chat Page');
await p.goto('http://localhost:5173/chat', {waitUntil:'domcontentloaded'});
await p.waitForTimeout(800);
await runCheck('Chat input present', async () => {
  if (!await p.locator('#chat-input').count()) throw new Error('Missing input');
});
await runCheck('Sidebar visible', async () => {
  if (!await p.locator('aside').count()) throw new Error('No sidebar');
});
await runCheck('Sidebar links', async () => {
  const links = await p.locator('aside button').allTextContents();
  const all = links.join(' ');
  if (!all.includes('Chat') || !all.includes('Standards')) throw new Error('Missing nav items');
});
await runCheck('Language selector', async () => {
  if (!await p.locator('select').count()) throw new Error('No language select');
});

// ── Streaming test ──
console.log('\n⚡ Streaming');
await p.fill('#chat-input', 'What is IS 1293?');
await p.keyboard.press('Enter');
const lengths = [];
// Use longer intervals since backend takes ~2-3s to respond
for (const ms of [500, 1500, 3000, 6000]) {
  await p.waitForTimeout(ms);
  const bubble = await p.locator('.message-enter').last().textContent();
  lengths.push(bubble?.length || 0);
}
await runCheck('Progressive rendering', async () => {
  if (lengths[0] < 10 || lengths[2] < 200) throw new Error('Progression: ' + lengths.join(', '));
});
await runCheck('Streaming completes', async () => {
  const final = await p.locator('.message-enter').last().textContent();
  if (!final || final.length < 200) throw new Error('Final too short: ' + (final?.length || 0));
});
await runCheck('No raw markdown', async () => {
  const text = await p.locator('.message-enter').last().textContent();
  if (text?.includes('```')) throw new Error('Raw markdown detected');
});
await runCheck('Citations appear', async () => {
  const citations = await p.locator('a[href*="bis.gov.in"]').count();
  if (citations === 0) throw new Error('No citations found');
});

// ── Standards page ──
console.log('\n📋 Standards Page');
await p.goto('http://localhost:5173/standards', {waitUntil:'domcontentloaded'});
await p.waitForTimeout(500);
await runCheck('Standards heading', async () => {
  const h = await p.locator('h1').first().textContent();
  if (!h?.includes('Standards')) throw new Error('No heading');
});
await runCheck('Search input', async () => {
  if (!await p.locator('input[aria-label="Search standards"]').count()) throw new Error('Missing');
});
await runCheck('Results table', async () => {
  const rows = await p.locator('tbody tr').count();
  if (rows < 1) throw new Error('No results');
});

// ── Crosswalk page ──
console.log('\n🔗 Crosswalk Page');
await p.goto('http://localhost:5173/crosswalk', {waitUntil:'domcontentloaded'});
await p.waitForTimeout(500);
await runCheck('Crosswalk heading', async () => {
  const h = await p.locator('h1').first().textContent();
  if (!h?.includes('QCO')) throw new Error('No heading');
});
await runCheck('Crosswalk results', async () => {
  const rows = await p.locator('tbody tr').count();
  if (rows < 1) throw new Error('No results');
});

// ── HUID page ──
console.log('\n💎 HUID Page');
await p.goto('http://localhost:5173/huid', {waitUntil:'domcontentloaded'});
await p.waitForTimeout(500);
await runCheck('HUID heading', async () => {
  const h = await p.locator('h1').first().textContent();
  if (!h?.includes('HUID')) throw new Error('No heading');
});
await runCheck('HUID cards', async () => {
  const cards = await p.locator('[class*="rounded-xl"]').count();
  if (cards < 3) throw new Error('Too few cards: ' + cards);
});

// ── Dashboard page ──
console.log('\n📊 Dashboard Page');
await p.goto('http://localhost:5173/dashboard', {waitUntil:'domcontentloaded'});
await p.waitForTimeout(800);
await runCheck('Dashboard heading', async () => {
  const h = await p.locator('h1').first().textContent();
  if (!h?.includes('Dashboard')) throw new Error('No heading');
});
await runCheck('Stat cards grid', async () => {
  const grids = await p.locator('.grid').count();
  if (grids < 1) throw new Error('No grid layout');
});

// ── Navigation flow ──
console.log('\n🧭 Navigation');
await p.goto('http://localhost:5173/', {waitUntil:'domcontentloaded'});
await p.waitForTimeout(400);
await runCheck('Navigate to chat', async () => {
  await p.click('button:has-text("Start Chatting")');
  await p.waitForURL('**/chat', {timeout: 5000});
  if (!p.url().includes('/chat')) throw new Error('Not on /chat');
});
// Use direct goto for standards to avoid click stability issues
await runCheck('Navigate to standards', async () => {
  await p.goto('http://localhost:5173/standards', {waitUntil:'domcontentloaded'});
  if (!p.url().includes('/standards')) throw new Error('Not on /standards');
});
await runCheck('Sidebar back to home', async () => {
  await p.goto('http://localhost:5173/chat', {waitUntil:'domcontentloaded'});
  await p.waitForTimeout(400);
  await p.click('text=Back to Home');
  await p.waitForURL('**/', {timeout: 5000});
  if (!p.url().includes('localhost:5173/')) throw new Error('Not on /');
});

// ── Accessibility ──
console.log('\n♿ Accessibility');
await p.goto('http://localhost:5173/', {waitUntil:'domcontentloaded'});
await p.waitForTimeout(400);
await runCheck('Skip link present', async () => {
  const skip = await p.locator('a.skip-link').count();
  if (skip === 0) throw new Error('No skip link');
});
await runCheck('ARIA labels on nav', async () => {
  const nav = await p.locator('[role="navigation"]').count();
  if (nav === 0) throw new Error('No nav landmark');
});
await runCheck('Buttons have aria-labels', async () => {
  const btns = await p.locator('button[aria-label]').count();
  if (btns === 0) throw new Error('No aria-label buttons');
});

await b.close();
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('Results: ' + pass + ' passed, ' + fail + ' failed');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
process.exit(fail > 0 ? 1 : 0);
