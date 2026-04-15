import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import FunnelAnalysis from './pages/FunnelAnalysis';
import ProductAnalytics from './pages/ProductAnalytics';
import LiveMonitor from './pages/LiveMonitor';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/funnel" element={<FunnelAnalysis />} />
          <Route path="/products" element={<ProductAnalytics />} />
          <Route path="/live" element={<LiveMonitor />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
