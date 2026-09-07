import { Sidebar } from '@/components/Sidebar';
import { ChatProvider } from '@/context/ChatContext';
import ChatView from '@/pages/ChatView';
import StandardsView from '@/pages/StandardsView';
import CrosswalkView from '@/pages/CrosswalkView';
import HuidView from '@/pages/HuidView';
import DashboardView from '@/pages/DashboardView';
import LandingView from '@/pages/LandingView';
import PageTransition from '@/components/PageTransition';
import { BrowserRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom';

function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const isLanding = location.pathname === '/';

  return (
    <div className="flex h-dvh bg-surface">
      {!isLanding && <Sidebar />}
      <main className={`flex-1 overflow-hidden ${isLanding ? '' : 'overflow-y-auto'}`}>
        <PageTransition>{children}</PageTransition>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <a href="#main-content" className="skip-link">Skip to main content</a>
      <ChatProvider>
        <Routes>
          <Route path="/" element={<LandingView />} />
          <Route path="/chat" element={
            <Layout>
              <ChatView />
            </Layout>
          } />
          <Route path="/standards" element={
            <Layout>
              <main id="main-content">
                <StandardsView />
              </main>
            </Layout>
          } />
          <Route path="/crosswalk" element={
            <Layout>
              <main id="main-content">
                <CrosswalkView />
              </main>
            </Layout>
          } />
          <Route path="/huid" element={
            <Layout>
              <main id="main-content">
                <HuidView />
              </main>
            </Layout>
          } />
          <Route path="/dashboard" element={
            <Layout>
              <main id="main-content">
                <DashboardView />
              </main>
            </Layout>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ChatProvider>
    </BrowserRouter>
  );
}
