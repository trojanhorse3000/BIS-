import { useState } from 'react';
import {
  MessageSquare, BookOpen, Table, Gem, LayoutDashboard,
  Menu, X, Home,
} from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

const navItems = [
  { path: '/chat', label: 'Chat', icon: MessageSquare },
  { path: '/standards', label: 'Standards', icon: BookOpen },
  { path: '/crosswalk', label: 'QCO Crosswalk', icon: Table },
  { path: '/huid', label: 'HUID Reference', icon: Gem },
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
];

export function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) => location.pathname === path;

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-3 left-3 z-50 p-2 rounded-lg bg-bg-card border border-border hover:border-accent/40 transition-all cursor-pointer"
        aria-label="Toggle navigation menu"
        aria-expanded={mobileOpen}
      >
        {mobileOpen ? <X size={18} className="text-ink" /> : <Menu size={18} className="text-ink" />}
      </button>

      {/* Backdrop */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 z-40"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-40
          w-56 bg-bg-elevated border-r border-border
          flex flex-col
          transition-transform duration-200 ease-in-out
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
        role="navigation"
        aria-label="Main navigation"
      >
        {/* Logo area */}
        <div className="px-5 py-5 border-b border-border">
          <button
            onClick={() => { navigate('/'); setMobileOpen(false); }}
            className="flex items-center gap-3 w-full hover:opacity-80 transition-opacity cursor-pointer"
            aria-label="Go to homepage"
          >
            <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center border border-accent/40">
              <svg viewBox="0 0 24 24" fill="none" className="text-accent" width={16} height={16}>
                <path d="M12 2L2 7l10 5 10-5-10-5z" fill="currentColor" opacity="0.4" />
                <path d="M2 17l10 5 10-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 12l10 5 10-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div className="text-left">
              <div className="text-ink font-bold text-sm tracking-wide">MANAKSETU</div>
              <div className="text-[10px] text-muted tracking-widest uppercase">mānak setu</div>
            </div>
          </button>
        </div>

        {/* Nav items */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item, idx) => {
            const active = isActive(item.path);
            const Icon = item.icon;
            return (
              <button
                key={item.path}
                onClick={() => { navigate(item.path); setMobileOpen(false); }}
                className={`
                  w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                  transition-all duration-150 cursor-pointer text-left
                  ${active
                    ? 'bg-accent/15 text-accent border-l-2 border-accent'
                    : 'text-muted hover:text-ink hover:bg-bg-hover'
                  }
                `}
                aria-current={active ? 'page' : undefined}
              >
                <span className="text-[10px] font-mono opacity-40 w-4">{String(idx + 1).padStart(2, '0')}</span>
                <Icon size={15} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Footer info */}
        <div className="p-4 border-t border-border">
          <button
            onClick={() => { navigate('/'); setMobileOpen(false); }}
            className="w-full flex items-center gap-2 text-xs text-muted hover:text-ink transition-colors text-left cursor-pointer"
            aria-label="Back to home page"
          >
            <Home size={12} />
            Back to Home
          </button>
          <div className="flex items-center gap-2 text-xs text-muted mt-2">
            <span className="w-1.5 h-1.5 rounded-full bg-green flex-shrink-0" />
            Backend connected
          </div>
          <p className="text-[10px] text-muted/50 mt-1 font-mono">FastAPI · v2.0</p>
        </div>
      </aside>
    </>
  );
}
