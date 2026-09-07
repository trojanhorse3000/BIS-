const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({headless:true});
  const p = await b.newPage();
  let pass = 0, fail = 0;
  const check = async (name, fn) => {
    try { await fn(p); pass++; console.log('  ✅ ' + name); }
    catch(e) { fail++; console.log('  ❌ ' + name + ': ' + e.message); }
  };

  console.log('\n🏠 Landing Page');
  await p.goto('http://localhost:5173/', {waitUntil:'domcontentloaded'});
  await p.waitForTimeout(600);
  await check('Title', async (pg) => {
    const t = await pg.title();
    if (!t.includes('BIS AI')) throw new Error('Title mismatch: ' + t);
  });
  await check('Hero heading', async (pg) => {
    const h = await pg.locator('h1').first().textContent();
    if (!h?.includes('Indian Standards')) throw new Error('No hero heading');
  });
  await check('Try Now CTA', async (pg) => {
    if (!await pg.locator('button:has-text("Try Now")').count()) throw new Error('Missing');
  });
  await check('Start Chatting CTA', async (pg) => {
    if (!await pg.locator('button:has-text("Start Chatting")').count()) throw new Error('Missing');
  });
  await check('Feature cards', async (pg) => {
    const count = await pg.locator('[class*="rounded-2xl"]').count();
    if (count < 4) throw new Error('Only ' + count + ' cards');
  });
  await check('Stats bar', async (pg) => {
    const vals = await pg.locator('[class*="text-2xl"]').allTextContents();
    if (!vals.some(v => v.includes('10,000'))) throw new Error('Missing stats');
  });

  console.log('\n💬 Chat Page');
  await p.goto('http://localhost:5173/', {waitUntil:'domcontentloaded'});
  await p.waitForTimeout(400);
  await p.click('button:has-text("Try Now")');
  await p.waitForTimeout(800);
  await check('Chat input present', async (pg) => {
    if (!await pg.locator('#chat-input').count()) throw new Error('Missing input');
  });
  await check('Sidebar visible', async (pg) => {
    if (!await pg.locator('aside').count()) throw new Error('No sidebar');
  });
  await check('Sidebar links', async (pg) => {
    const links = await pg.locator('aside button').allTextContents();
    const all = links.join(' ');
    if (!all.includes('Chat') || !all.includes('Standards')) throw new Error('Missing nav items');
  });
  await check('Language selector', async (pg) => {
    if (!await pg.locator('select').count()) throw new Error('No language select');
  });

  console.log('\n⚡ Streaming');
  await p.fill('#chat-input', 'What is IS 1293?');
  await p.keyboard.press('Enter');
  const lengths = [];
  for (const ms of [500, 1500, 3000, 6000]) {
    await p.waitForTimeout(ms);
    const bubble = await p.locator('[class*="bg-white"]').last().textContent();
    lengths.push(bubble?.length || 0);
  }
  await check('Progressive rendering', async () => {
    if (lengths[0] < 10 || lengths[2] < 200) throw new Error('Progression: ' + lengths.join(', '));
  });
  await check('Streaming completes', async () => {
    await p.waitForTimeout(3000);
    const final = await p.locator('[class*="bg-white"]').last().textContent();
    if (!final || final.length < 200) throw new Error('Final too short: ' + (final?.length || 0));
  });
  await check('No raw markdown', async () => {
    await p.waitForTimeout(1000);
    const text = await p.locator('[class*="bg-white"]').last().textContent();
    if (text?.includes('```')) throw new Error('Raw markdown detected');
  });
  await check('Citations appear', async () => {
    await p.waitForTimeout(2000);
    const citations = await p.locator('a[href*="bis.gov.in"]').count();
    if (citations === 0) throw new Error('No citations found');
  });

  console.log('\n📋 Standards Page');
  await p.goto('http://localhost:5173/standards', {waitUntil:'domcontentloaded'});
  await p.waitForTimeout(500);
  await check('Standards heading', async (pg) => {
    const h = await pg.locator('h1').first().textContent();
    if (!h?.includes('Standards')) throw new Error('No heading');
  });
  await check('Search input', async (pg) => {
    if (!await pg.locator('input[aria-label="Search standards"]').count()) throw new Error('Missing');
  });
  await check('Results table', async (pg) => {
    const rows = await pg.locator('tbody tr').count();
    if (rows < 1) throw new Error('No results');
  });

  console.log('\n🔗 Crosswalk Page');
  await p.goto('http://localhost:5173/crosswalk', {waitUntil:'domcontentloaded'});
  await p.waitForTimeout(500);
  await check('Crosswalk heading', async (pg) => {
    const h = await pg.locator('h1').first().textContent();
    if (!h?.includes('QCO')) throw new Error('No heading');
  });
  await check('Crosswalk results', async (pg) => {
    const rows = await pg.locator('tbody tr').count();
    if (rows < 1) throw new Error('No results');
  });

  console.log('\n💎 HUID Page');
  await p.goto('http://localhost:5173/huid', {waitUntil:'domcontentloaded'});
  await p.waitForTimeout(500);
  await check('HUID heading', async (pg) => {
    const h = await pg.locator('h1').first().textContent();
    if (!h?.includes('HUID')) throw new Error('No heading');
  });
  await check('HUID cards', async (pg) => {
    const cards = await pg.locator('[class*="rounded-xl"]').count();
    if (cards < 3) throw new Error('Too few cards: ' + cards);
  });

  console.log('\n📊 Dashboard Page');
  await p.goto('http://localhost:5173/dashboard', {waitUntil:'domcontentloaded'});
  await p.waitForTimeout(800);
  await check('Dashboard heading', async (pg) => {
    const h = await pg.locator('h1').first().textContent();
    if (!h?.includes('Dashboard')) throw new Error('No heading');
  });
  await check('Stat cards grid', async (pg) => {
    const grids = await pg.locator('.grid').count();
    if (grids < 1) throw new Error('No grid layout');
  });

  console.log('\n🧭 Navigation');
  await p.goto('http://localhost:5173/', {waitUntil:'domcontentloaded'});
  await p.waitForTimeout(400);
  await check('Navigate to chat', async (pg) => {
    await pg.click('button:has-text("Start Chatting")');
    await pg.waitForURL('**/chat', {timeout: 3000});
    if (!pg.url().includes('/chat')) throw new Error('Not on /chat');
  });
  await check('Navigate to standards', async (pg) => {
    await pg.click('button:has-text("Browse Standards")');
    await pg.waitForURL('**/standards', {timeout: 3000});
    if (!pg.url().includes('/standards')) throw new Error('Not on /standards');
  });
  await check('Sidebar back to home', async (pg) => {
    await pg.goto('http://localhost:5173/chat', {waitUntil:'domcontentloaded'});
    await pg.waitForTimeout(400);
    await pg.click('text=Back to Home');
    await pg.waitForURL('**/', {timeout: 3000});
    if (!pg.url().includes('localhost:5173/')) throw new Error('Not on /');
  });

  console.log('\n♿ Accessibility');
  await p.goto('http://localhost:5173/', {waitUntil:'domcontentloaded'});
  await p.waitForTimeout(400);
  await check('Skip link present', async (pg) => {
    const skip = await pg.locator('a.skip-link').count();
    if (skip === 0) throw new Error('No skip link');
  });
  await check('ARIA labels on nav', async (pg) => {
    const nav = await pg.locator('[role="navigation"]').count();
    if (nav === 0) throw new Error('No nav landmark');
  });
  await check('Buttons have aria-labels', async (pg) => {
    const btns = await pg.locator('button[aria-label]').count();
    if (btns === 0) throw new Error('No aria-label buttons');
  });

  await b.close();
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('Results: ' + pass + ' passed, ' + fail + ' failed');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  process.exit(fail > 0 ? 1 : 0);
})();
