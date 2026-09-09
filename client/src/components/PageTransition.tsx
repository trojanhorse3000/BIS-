import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';

type PageTransitionProps = {
  children: React.ReactNode;
  className?: string;
};

export default function PageTransition({ children, className = '' }: PageTransitionProps) {
  const location = useLocation();
  const [anim, setAnim] = useState<'enter' | 'exit' | 'none'>('none');
  const prevKeyRef = useRef(0);

  useEffect(() => {
    // Detect route change by hash-busting the key counter
    prevKeyRef.current += 1;
    setAnim('enter');
  }, [location.pathname, location.key]); // pathname+key = stable unique identifier per navigation

  // Play exit animation, then swap to enter
  useEffect(() => {
    if (anim !== 'enter') return;
    const id = setTimeout(() => setAnim('exit'), 50);
    return () => clearTimeout(id);
  }, [anim]);

  // After exit completes, trigger enter
  useEffect(() => {
    if (anim !== 'exit') return;
    const id = setTimeout(() => setAnim('enter'), 350); // matches anim-page-exit duration
    return () => clearTimeout(id);
  }, [anim]);

  return (
    <div
      className={`page-content ${className}`}
      data-anim={anim}
      style={{ animation: 'none' }}
    >
      {children}
    </div>
  );
}
