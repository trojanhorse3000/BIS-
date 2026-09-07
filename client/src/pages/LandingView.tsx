import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MessageSquare, BookOpen, Table, Gem, LayoutDashboard,
  ShieldCheck, Search, ChevronRight, CheckCircle2, Clock,
  ExternalLink, Building2, Globe, FileText, Scale,
  Zap, Cpu,
} from 'lucide-react';

export default function LandingView() {
  const navigate = useNavigate();
  const [activePreview, setActivePreview] = useState(0);
  const [streamed, setStreamed] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const charIndexRef = useRef(0);

  const previews = [
    {
      user: 'What is IS 1293 about?',
      ai: 'IS 1293 is the Indian Standard for **Portland composite cement**. It specifies requirements for a blend of Portland cement clinker, limestone, and gypsum. The current version is IS 1293:2022 (6th revision), which replaced IS 1293:1988.\n\n**Key highlights:**\n- Applicable to Portland composite cement of grade 33\n- Sets limits on physical and chemical properties\n- Governs packaging and marking requirements',
      intent: 'STANDARD_LOOKUP',
    },
    {
      user: '22 क्यरेट सोनो का हॉलमार्क क्यो होतो है?',
      ai: '22 क्यरेट (916) सोनो का हॉलमार्क तिन भानगों मैं कियाम जातो है:\n\n1. **पवित्रतान चिन्ह** — 916 अंक (91.6% स्वर्ण)\n2. **हॉलमारकिंग कैंद्र कं कोड** — 6 अंकों का HUID\n3. **वैश्लेषिक केंद्र कं लोको** — BIS चिन्ह\n\nयह IS 2118:2016 कें अधीन अनिवार्य हें और निर्माताओं कों compulsory registration प्राप्त होना आवश्यक हई।',
      intent: 'HUID_VERIFICATION',
    },
    {
      user: 'Which QCO applies to steel rods?',
      ai: 'Steel rods fall under **QCO 38/2020** (Iron & Steel Sections).\n\n**Applicable standards:**\n- IS 1786 (TMT bars)\n- IS 432 (Mild steel rods)\n- IS 275 (Common steel rods)\n\nThe QCO mandates BIS certification for manufacturing, sale, and distribution. Compliance is **compulsory** for all domestic manufacturers and importers.',
      intent: 'CROSSWALK_LOOKUP',
    },
  ];

  const features = [
    {
      num: '[01]',
      icon: <MessageSquare size={18} />,
      title: 'AI-Powered Chat',
      desc: 'Ask questions in English or Hindi about BIS standards, QCO orders, and hallmarking — get instant, sourced answers.',
      path: '/chat',
    },
    {
      num: '[02]',
      icon: <BookOpen size={18} />,
      title: 'Standards Browser',
      desc: 'Search 10,000+ Indian Standards by IS number, keyword, or technical committee. Filter by status and category.',
      path: '/standards',
    },
    {
      num: '[03]',
      icon: <Table size={18} />,
      title: 'QCO Crosswalk',
      desc: 'Map products to mandatory Quality Control Orders. Find which QCO applies to your product category.',
      path: '/crosswalk',
    },
    {
      num: '[04]',
      icon: <Gem size={18} />,
      title: 'HUID Reference',
      desc: 'Gold hallmarking grades, carving marks, and verification guidelines under IS 2112:2016.',
      path: '/huid',
    },
    {
      num: '[05]',
      icon: <LayoutDashboard size={18} />,
      title: 'Analytics Dashboard',
      desc: 'Query volume, intent distribution, latency trends, and system health at a glance.',
      path: '/dashboard',
    },
    {
      num: '[06]',
      icon: <ShieldCheck size={18} />,
      title: 'Verified Answers',
      desc: 'Every response is cross-referenced against official BIS documents with traceable citations.',
      path: '/chat',
    },
  ];

  // ── Streaming animation ──
  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = null;
    charIndexRef.current = 0;
    setStreamed('');
    setIsStreaming(true);

    const fullText = previews[activePreview].ai;

    const startTimer = setTimeout(() => {
      setIsStreaming(true);
      intervalRef.current = setInterval(() => {
        charIndexRef.current += 1;
        setStreamed(fullText.slice(0, charIndexRef.current));
        if (charIndexRef.current >= fullText.length) {
          if (intervalRef.current) clearInterval(intervalRef.current);
          intervalRef.current = null;
          setIsStreaming(false);
        }
      }, 18);
    }, 800);

    return () => {
      clearTimeout(startTimer);
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
    };
  }, [activePreview]); // eslint-disable-line react-hooks/exhaustive-deps

  const bisPortalLinks = [
    { name: 'BIS Official Website', url: 'https://www.bis.gov.in', icon: <Globe size={14} /> },
    { name: 'BIS Standards Catalogue', url: 'https://standards.bis.gov.in', icon: <FileText size={14} /> },
    { name: 'QCO Notifications', url: 'https://www.bis.gov.in/qco', icon: <Scale size={14} /> },
    { name: 'Hallmarking Portal', url: 'https://hallmarking.bis.gov.in', icon: <Gem size={14} /> },
    { name: 'CRILS — Certification', url: 'https://crils.bis.gov.in', icon: <CheckCircle2 size={14} /> },
    { name: 'BIS Dealer Licensing', url: 'https://www.bis.gov.in/dealer', icon: <Building2 size={14} /> },
  ];

  return (
    <div className="min-h-screen bg-bg" id="main-content">

      {/* ── Top accent line ── */}
      <div className="h-px bg-gradient-to-r from-transparent via-accent/50 to-transparent" aria-hidden="true" />

      {/* ── Header / Navbar ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-bg/80 backdrop-blur-md border-b border-border" role="navigation" aria-label="Main navigation">
        <div className="max-w-6xl mx-auto px-6 py-3.5 flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-3 group"
            aria-label="ManakSetu home"
          >
            <div className="w-8 h-8 rounded flex items-center justify-center border border-accent/40 bg-accent/10 group-hover:border-accent transition-colors">
              <svg viewBox="0 0 24 24" fill="none" className="text-accent" width={16} height={16}>
                <path d="M12 2L2 7l10 5 10-5-10-5z" fill="currentColor" opacity="0.4" />
                <path d="M2 17l10 5 10-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 12l10 5 10-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div>
              <div className="text-ink font-bold text-sm tracking-widest uppercase">ManakSetu</div>
              <div className="text-[10px] text-muted font-mono">mānak setu</div>
            </div>
          </button>

          <div className="flex items-center gap-3">
            <button className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono text-muted border border-border hover:border-accent/40 hover:text-accent transition-colors cursor-pointer uppercase tracking-wider">
              <Globe size={12} />
              EN / हिं
            </button>
            <button
              onClick={() => navigate('/chat')}
              className="flex items-center gap-2 px-4 py-2 bg-accent text-black text-sm font-semibold rounded hover:bg-accent/90 transition-all cursor-pointer uppercase tracking-wide"
            >
              <Zap size={14} />
              Try Now
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="pt-32 pb-20 px-6" aria-labelledby="hero-heading">
        <div className="max-w-6xl mx-auto grid lg:grid-cols-2 gap-16 items-center hero-anim">
          {/* Left: Copy */}
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-accent-dim text-accent text-xs font-mono rounded mb-6 border border-accent/20 uppercase tracking-widest">
              <span>[01]</span>
              India&apos;s National Standards Authority
            </div>
            <h1 id="hero-heading" className="text-4xl sm:text-5xl font-bold text-ink leading-tight mb-6">
              An AI agent that works
              <span className="text-accent"> inside your </span>
              regulatory workflow
            </h1>
            <p className="text-lg text-muted leading-relaxed mb-8 max-w-lg">
              Ask natural-language questions about BIS regulations, Indian Standards, QCO orders,
              and hallmarking — get verified answers with official citations in seconds.
            </p>

            {/* Value props */}
            <div className="flex flex-wrap gap-4 mb-8">
              {['Faster iterations', 'Fewer mistakes', 'Less busywork'].map(label => (
                <div key={label} className="flex items-center gap-2 text-xs font-mono text-muted uppercase tracking-wider">
                  <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                  {label}
                </div>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <button
                onClick={() => navigate('/chat')}
                className="flex items-center gap-2 px-8 py-3.5 bg-primary text-white font-bold rounded hover:bg-primary/90 transition-all cursor-pointer uppercase tracking-wide"
              >
                <MessageSquare size={18} />
                Start Chatting
                <ChevronRight size={16} />
              </button>
              <button
                onClick={() => navigate('/standards')}
                className="flex items-center gap-2 px-8 py-3.5 bg-transparent text-ink font-bold rounded border border-border hover:border-white/40 transition-all cursor-pointer uppercase tracking-wide"
              >
                <Search size={18} />
                Browse Standards
              </button>
            </div>
          </div>

          {/* Right: Conversational UI Preview */}
          <div className="relative">
            {/* Loading sequence */}
            <div className="mb-4 font-mono text-[10px] text-muted space-y-0.5">
              <div className="loading-seq-item">{'>'} 001 INITIALIZE CORE SYSTEM...</div>
              <div className="loading-seq-item">{'>'} 002 CONNECTING TO BIS DATABASES...</div>
              <div className="loading-seq-item">{'>'} 003 LOADING STANDARDS INDEX (10,247 RECORDS)...</div>
              <div className="loading-seq-item">{'>'} 004 RUNNING RETRIEVAL PIPELINE...</div>
              <div className="loading-seq-item">{'>'} 005 LLM INFERENCE COMPLETE</div>
              <div className="loading-seq-item text-accent">{'>'} 006 READY — AWAITING INPUT_</div>
            </div>

            <div className="bg-bg-card border border-border rounded-lg overflow-hidden">
              {/* Preview header */}
              <div className="flex items-center gap-2 px-4 py-2.5 bg-bg-elevated border-b border-border">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
                <div className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
                <span className="ml-2 text-xs text-muted font-mono">manaksetu.exe</span>
                <span className="ml-auto text-[10px] font-mono text-muted">v2.0.1</span>
              </div>

              {/* Preview tabs */}
              <div className="flex border-b border-border bg-bg-elevated">
                {previews.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setActivePreview(i)}
                    className={`flex-1 px-3 py-2 text-xs font-mono transition-colors cursor-pointer ${
                      activePreview === i
                        ? 'text-accent border-b-2 border-accent bg-accent-dim'
                        : 'text-muted hover:text-ink'
                    }`}
                    aria-selected={activePreview === i}
                    role="tab"
                  >
                    {i === 0 ? '01_EN' : i === 1 ? '02_HI' : '03_QCO'}
                  </button>
                ))}
              </div>

              {/* Preview messages */}
              <div className="p-4 space-y-4 min-h-[280px] max-h-[360px] overflow-y-auto">
                {previews[activePreview] && (() => {
                  const p = previews[activePreview];
                  return (
                    <>
                      <div className="flex justify-end">
                        <div className="preview-bubble-user">
                          {p.user}
                        </div>
                      </div>
                      <div className="flex justify-start items-start gap-2">
                        <div className="w-6 h-6 rounded bg-accent/20 flex items-center justify-center flex-shrink-0 mt-0.5 border border-accent/30">
                          <Cpu size={12} className="text-accent" />
                        </div>
                        <div className="preview-bubble-ai whitespace-pre-wrap">
                          {isStreaming ? (
                            <>
                              {streamed}
                              <span className="streaming-cursor inline" />
                            </>
                          ) : streamed ? (
                            <>
                              {streamed}
                              <div className="mt-2 flex items-center gap-3 text-[10px] font-mono text-muted">
                                <span className="flex items-center gap-1"><CheckCircle2 size={10} className="text-green" /> VERIFIED</span>
                                <span className="flex items-center gap-1"><Clock size={10} /> 1.2s</span>
                                <span className="ml-auto">{p.intent.replace(/_/g, ' ')}</span>
                              </div>
                            </>
                          ) : (
                            <div className="typing-dots">
                              <span />
                              <span />
                              <span />
                            </div>
                          )}
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>

              {/* Preview input */}
              <div className="px-4 py-3 bg-bg-elevated border-t border-border">
                <div className="flex items-center gap-2 bg-bg border border-border rounded px-3 py-2">
                  <span className="text-xs text-muted font-mono">$ ask about bis standards…</span>
                  <div className="ml-auto flex items-center gap-2">
                    <span className="text-[10px] font-mono text-muted bg-bg-hover px-1.5 py-0.5 rounded">EN</span>
                    <div className="w-6 h-6 rounded bg-accent flex items-center justify-center cursor-pointer">
                      <ChevronRight size={12} className="text-black" />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating badge */}
            <div className="absolute -bottom-3 -right-3 bg-bg-card border border-border rounded px-3 py-2 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green animate-pulse" />
              <span className="text-xs font-mono text-muted">10,247 standards indexed</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats bar ── */}
      <section className="py-8 px-6 border-y border-border bg-bg-elevated" aria-label="Key statistics">
        <div className="max-w-4xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
          {[
            { label: 'Standards', value: '10,247', icon: <BookOpen size={14} /> },
            { label: 'QCO Orders', value: '200+', icon: <Table size={14} /> },
            { label: 'Gold Grades', value: '13', icon: <Gem size={14} /> },
            { label: 'Latency', value: '<2s', icon: <Clock size={14} /> },
          ].map(s => (
            <div key={s.label} className="flex flex-col items-center gap-1.5">
              <div className="text-2xl font-bold text-ink font-mono">{s.value}</div>
              <div className="text-xs text-muted uppercase tracking-widest font-mono">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── About BIS ── */}
      <section className="py-20 px-6" aria-labelledby="bis-heading">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-accent-dim text-accent text-xs font-mono rounded mb-4 border border-accent/20 uppercase tracking-widest">
                <span>[02]</span> About the Authority
              </div>
              <h2 id="bis-heading" className="text-3xl font-bold text-ink mb-4 uppercase tracking-tight">
                What is <span className="text-accent">BIS</span>?
              </h2>
              <p className="text-muted leading-relaxed mb-4">
                The <strong className="text-ink">Bureau of Indian Standards (BIS)</strong> is the National Standard Body of India
                established under the <strong className="text-ink">BIS Act, 2016</strong>. It is the premier standards body responsible for
                standardization, certification, and quality mark administration across the country.
              </p>
              <p className="text-muted leading-relaxed mb-6">
                BIS works under the Ministry of Consumer Affairs, Food &amp; Public Distribution, Government of India.
                It sets standards for over 23,000 products spanning agriculture, textiles, electronics, construction
                materials, chemicals, and more — ensuring safety, quality, and interoperability.
              </p>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'ESTABLISHED', value: '1986 (Act 2016)' },
                  { label: 'HQ', value: 'New Delhi, India' },
                  { label: 'PRODUCTS', value: '23,000+' },
                  { label: 'SCHEMES', value: '40+' },
                ].map(item => (
                  <div key={item.label} className="bg-bg-card rounded p-3 border border-border">
                    <div className="text-sm font-bold text-ink font-mono">{item.value}</div>
                    <div className="text-[10px] text-muted uppercase tracking-wider">{item.label}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-bg-card border border-border rounded p-6">
              <h3 className="text-sm font-bold text-ink mb-4 flex items-center gap-2 uppercase tracking-wider border-b border-border pb-3">
                <Scale size={14} className="text-accent" />
                BIS Key Functions
              </h3>
              <ul className="space-y-2.5">
                {[
                  'Setting and promoting Indian Standards',
                  'Product Certification (ISI, AGMARK, Hallmark)',
                  'Licensing of manufacturers and dealers',
                  'Quality Control and Inspection',
                  'Conducting tests and surveys',
                  'Advising Central &amp; State Governments on standards',
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-muted">
                    <ChevronRight size={14} className="text-accent flex-shrink-0 mt-0.5" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-20 px-6" aria-labelledby="features-heading">
        <div className="max-w-6xl mx-auto">
          <div className="mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-accent-dim text-accent text-xs font-mono rounded mb-4 border border-accent/20 uppercase tracking-widest">
              <span>[03]</span> Platform Modules
            </div>
            <h2 id="features-heading" className="text-3xl font-bold text-ink mb-3 uppercase tracking-tight">
              Everything you need for BIS compliance
            </h2>
            <p className="text-muted max-w-xl">
              From standards lookup to hallmarking verification — one platform for all your regulatory needs.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 cards-anim">
            {features.map(f => (
              <button
                key={f.title}
                onClick={() => navigate(f.path)}
                className="text-left bg-bg-card border border-border rounded p-5 hover:border-accent/40 hover:bg-bg-hover transition-all duration-200 group cursor-pointer"
                aria-label={`Go to ${f.title}`}
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[10px] font-mono text-muted">{f.num}</span>
                  <div className="w-9 h-9 rounded bg-accent/10 text-accent flex items-center justify-center border border-accent/20 group-hover:bg-accent group-hover:text-black transition-colors">
                    {f.icon}
                  </div>
                </div>
                <h3 className="text-sm font-bold text-ink mb-1.5 uppercase tracking-wide">{f.title}</h3>
                <p className="text-xs text-muted leading-relaxed">{f.desc}</p>
                <div className="mt-4 flex items-center gap-1 text-xs text-accent font-mono opacity-0 group-hover:opacity-100 transition-opacity uppercase tracking-wider">
                  Explore <ChevronRight size={12} />
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── Learn / FAQ Section ── */}
      <section className="py-20 px-6 bg-bg-elevated" aria-labelledby="learn-heading">
        <div className="max-w-6xl mx-auto">
          <div className="mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-accent-dim text-accent text-xs font-mono rounded mb-4 border border-accent/20 uppercase tracking-widest">
              <span>[04]</span> Knowledge Base
            </div>
            <h2 id="learn-heading" className="text-3xl font-bold text-ink mb-3 uppercase tracking-tight">
              Frequently asked about BIS
            </h2>
            <p className="text-muted max-w-xl">
              New to Indian standards and certification? Start here — short answers to the questions we get most.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            {[
              {
                icon: <Scale size={18} />,
                q: 'What is BIS?',
                a: 'The Bureau of Indian Standards (BIS) is India\'s national standards body, established under the BIS Act, 2016. It sets standards for 23,000+ products across construction, electronics, food, textiles, and more — ensuring safety, quality, and interoperability.',
              },
              {
                icon: <FileText size={18} />,
                q: 'What is an HS Code?',
                a: 'A Harmonized System (HS) code is an internationally standardized code (6–10 digits) used to classify traded products. India uses an 8-digit Indian Customs excise duty (ICED) code. BIS crosswalks HS codes to the Indian Standards that apply to each product category.',
              },
              {
                icon: <ShieldCheck size={18} />,
                q: 'What is a QCO?',
                a: 'A Quality Control Order (QCO) is a government notification under the BIS Act making compliance with a specific Indian Standard mandatory for certain products. Manufacture, sale, or import without BIS certification under a QCO is illegal.',
              },
              {
                icon: <Gem size={18} />,
                q: 'What is HUID Hallmarking?',
                a: 'HUID (Hallmarking Unique Identification) is a 6-digit code stamped on gold and silver jewellery under IS 2112:2016. It uniquely identifies the article, the jeweller, and the assay centre — making it verifiable on the BIS CARE mobile app.',
              },
              {
                icon: <CheckCircle2 size={18} />,
                q: 'What are ISI & CRS Marks?',
                a: 'The ISI Mark (Scheme I) is the quality certification for products like cables, cement, and steel. The CRS (Compulsory Registration Scheme, Scheme II) applies to electronics and IT goods. Both guarantee the product meets the relevant Indian Standard.',
              },
              {
                icon: <Globe size={18} />,
                q: 'Who needs BIS certification?',
                a: 'Any manufacturer, importer, or assembler whose product falls under a BIS QCO or Indian Standard must obtain BIS certification. This includes foreign manufacturers exporting to India — they must register through a local authorized representative.',
              },
              {
                icon: <MessageSquare size={18} />,
                q: 'What is the BIS Certification Process?',
                a: 'The process involves: (1) Application submission online, (2) Product testing at BIS-recognized labs, (3) Factory inspection by BIS officers, (4) Grant of license with BIS standard mark, (5) Periodic surveillance and re-testing to maintain compliance.',
              },
              {
                icon: <BookOpen size={18} />,
                q: 'What is an Indian Standard (IS)?',
                a: 'An Indian Standard (IS) is a technical specification published by BIS that defines requirements for a product, process, or service. Examples: IS 1293 for cement, IS 1786 for TMT steel, IS 1417 for hallmarking. Each IS has a unique number, edition year, and scope.',
              },
            ].map((item, i) => (
              <button
                key={i}
                onClick={() => {
                  navigate('/chat');
                  setTimeout(() => {
                    window.dispatchEvent(new CustomEvent('bis-suggest', { detail: item.q }));
                  }, 100);
                }}
                className="text-left bg-bg-card border border-border rounded p-4 hover:border-accent/40 hover:bg-bg-hover transition-all duration-200 group cursor-pointer"
              >
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded bg-accent/10 text-accent flex items-center justify-center flex-shrink-0 group-hover:bg-accent group-hover:text-black transition-colors border border-accent/20">
                    {item.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-[10px] font-mono text-muted mb-0.5 uppercase tracking-wider">
                      Q{String(i + 1).padStart(2, '0')}
                    </div>
                    <h3 className="text-sm font-bold text-ink mb-1 uppercase tracking-wide">{item.q}</h3>
                    <p className="text-xs text-muted leading-relaxed line-clamp-2">{item.a}</p>
                    <div className="mt-2 flex items-center gap-1 text-xs text-accent font-mono opacity-0 group-hover:opacity-100 transition-opacity uppercase tracking-wider">
                      Ask in chat <ChevronRight size={12} />
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── Demo CTA ── */}
      <section className="py-24 px-6" aria-labelledby="cta-heading">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-accent-dim text-accent text-xs font-mono rounded mb-6 border border-accent/20 uppercase tracking-widest">
            <span>[05]</span> Get Started
          </div>
          <h2 id="cta-heading" className="text-3xl sm:text-4xl font-bold text-ink mb-4 uppercase tracking-tight">
            Ready to explore BIS regulations?
          </h2>
          <p className="text-muted text-lg mb-10 max-w-lg mx-auto">
            Start a conversation and discover how AI can help you navigate Indian Standards, QCO orders, and hallmarking rules.
          </p>
          <button
            onClick={() => navigate('/chat')}
            className="inline-flex items-center gap-2 px-10 py-4 bg-accent text-black font-bold rounded hover:bg-accent/90 transition-all cursor-pointer uppercase tracking-wide"
          >
            <Zap size={18} />
            Launch ManakSetu
            <ChevronRight size={16} />
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-border bg-bg-elevated" role="contentinfo">
        {/* Top accent */}
        <div className="h-px bg-gradient-to-r from-transparent via-accent/30 to-transparent" aria-hidden="true" />

        <div className="py-12 px-6">
          <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-10 mb-10">
            {/* Column 1: Brand */}
            <div>
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-8 h-8 rounded flex items-center justify-center border border-accent/40 bg-accent/10">
                  <ShieldCheck className="text-accent" size={16} />
                </div>
                <div>
                  <div className="text-ink font-bold text-sm tracking-widest uppercase">ManakSetu</div>
                  <div className="text-[10px] text-muted font-mono">mānak setu · v2.0</div>
                </div>
              </div>
              <p className="text-sm text-muted leading-relaxed mb-4">
                AI-powered regulatory assistant for BIS standards, QCO orders, and hallmarking — making Indian Standards accessible to all.
              </p>
              <p className="text-xs text-muted/60 font-mono">
                An initiative to support industry, consumers, and policymakers in navigating India&apos;s quality infrastructure.
              </p>
            </div>

            {/* Column 2: BIS Portal Links */}
            <div>
              <h3 className="text-xs font-bold text-ink mb-4 uppercase tracking-widest flex items-center gap-2">
                <ExternalLink size={12} className="text-accent" />
                BIS Portals
              </h3>
              <ul className="space-y-2">
                {bisPortalLinks.map(link => (
                  <li key={link.name}>
                    <a
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-muted hover:text-accent transition-colors cursor-pointer group font-mono"
                      aria-label={`Open ${link.name} in new tab`}
                    >
                      <span className="text-accent opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                        {link.icon}
                      </span>
                      {link.name}
                      <ExternalLink size={11} className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Column 3: Platform Navigation */}
            <div>
              <h3 className="text-xs font-bold text-ink mb-4 uppercase tracking-widest">Platform</h3>
              <ul className="space-y-2">
                {[
                  { label: '01 — Chat', path: '/chat' },
                  { label: '02 — Standards', path: '/standards' },
                  { label: '03 — QCO Crosswalk', path: '/crosswalk' },
                  { label: '04 — HUID Reference', path: '/huid' },
                  { label: '05 — Dashboard', path: '/dashboard' },
                ].map(item => (
                  <li key={item.label}>
                    <button
                      onClick={() => navigate(item.path)}
                      className="text-sm text-muted hover:text-ink transition-colors cursor-pointer font-mono"
                    >
                      {item.label}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="border-t border-border pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-muted font-mono">
            <p>© 2026 ManakSetu · Bureau of Indian Standards</p>
            <nav aria-label="Footer navigation">
              <div className="flex items-center gap-5">
                <a href="https://www.bis.gov.in" target="_blank" rel="noopener noreferrer" className="hover:text-ink transition-colors cursor-pointer">BIS Official</a>
                <a href="https://standards.bis.gov.in" target="_blank" rel="noopener noreferrer" className="hover:text-ink transition-colors cursor-pointer">Standards</a>
                <a href="https://www.bis.gov.in/privacy-policy" target="_blank" rel="noopener noreferrer" className="hover:text-ink transition-colors cursor-pointer">Privacy</a>
                <a href="https://www.bis.gov.in/terms" target="_blank" rel="noopener noreferrer" className="hover:text-ink transition-colors cursor-pointer">Terms</a>
              </div>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}
