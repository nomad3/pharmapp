import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import SearchResultsPage from "./pages/SearchResultsPage";
import MedicationDetailPage from "./pages/MedicationDetailPage";
import LoginPage from "./pages/LoginPage";
import OrderHistoryPage from "./pages/OrderHistoryPage";
import FavoritesPage from "./pages/FavoritesPage";
import PharmacyMapPage from "./pages/PharmacyMapPage";
import AnalyticsDashboardPage from "./pages/AnalyticsDashboardPage";
import PricingPage from "./pages/PricingPage";
import PremiumPage from "./pages/PremiumPage";
import PharmacyPartnerPage from "./pages/PharmacyPartnerPage";
import OrgDashboardPage from "./pages/OrgDashboardPage";
import OrgSettingsPage from "./pages/OrgSettingsPage";
import ApiKeysPage from "./pages/ApiKeysPage";
import BillingPage from "./pages/BillingPage";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchResultsPage />} />
          <Route path="/medication/:id" element={<MedicationDetailPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/orders" element={<OrderHistoryPage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
          <Route path="/map" element={<PharmacyMapPage />} />
          <Route path="/analytics" element={<AnalyticsDashboardPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/premium" element={<PremiumPage />} />
          <Route path="/partners" element={<PharmacyPartnerPage />} />
          <Route path="/org/:slug" element={<OrgDashboardPage />} />
          <Route path="/org/:slug/settings" element={<OrgSettingsPage />} />
          <Route path="/org/:slug/keys" element={<ApiKeysPage />} />
          <Route path="/org/:slug/billing" element={<BillingPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
