import React from "react";
import { BrowserRouter, Routes, Route, Navigate, useParams } from "react-router-dom";
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
// Layer 1: Transparency
import TransparencyPage from "./pages/TransparencyPage";
// Layer 2: Intelligence
import IntelligenceDashboardPage from "./pages/IntelligenceDashboardPage";
// Layer 3: GPO
import GpoDashboardPage from "./pages/GpoDashboardPage";
import GpoPurchaseIntentPage from "./pages/GpoPurchaseIntentPage";
import GpoGroupOrderPage from "./pages/GpoGroupOrderPage";
import GpoSavingsPage from "./pages/GpoSavingsPage";
// Layer 4: Adherence
import AdherenceProgramsPage from "./pages/AdherenceProgramsPage";
import AdherenceDashboardPage from "./pages/AdherenceDashboardPage";
import AdherenceEnrollmentDetailPage from "./pages/AdherenceEnrollmentDetailPage";
import AdherenceSponsorPage from "./pages/AdherenceSponsorPage";
// Checkout flow
import CheckoutPage from "./pages/CheckoutPage";
import OrderDetailPage from "./pages/OrderDetailPage";
import "./App.css";

function MedicationRedirect() {
  const { id } = useParams();
  return <Navigate to={`/medicamento/${id}`} replace />;
}

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchResultsPage />} />
          <Route path="/medicamento/:slug" element={<MedicationDetailPage />} />
          <Route path="/medication/:id" element={<MedicationRedirect />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/orders" element={<OrderHistoryPage />} />
          <Route path="/orders/:id" element={<OrderDetailPage />} />
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
          {/* Layer 1: Transparency */}
          <Route path="/transparency" element={<TransparencyPage />} />
          {/* Layer 2: Intelligence */}
          <Route path="/intelligence" element={<IntelligenceDashboardPage />} />
          <Route path="/org/:slug/intelligence" element={<IntelligenceDashboardPage />} />
          {/* Layer 3: GPO */}
          <Route path="/gpo/:slug" element={<GpoDashboardPage />} />
          <Route path="/gpo/:slug/intents" element={<GpoPurchaseIntentPage />} />
          <Route path="/gpo/:slug/orders/:orderId" element={<GpoGroupOrderPage />} />
          <Route path="/gpo/:slug/savings" element={<GpoSavingsPage />} />
          {/* Layer 4: Adherence */}
          <Route path="/adherence" element={<AdherenceProgramsPage />} />
          <Route path="/adherence/dashboard" element={<AdherenceDashboardPage />} />
          <Route path="/adherence/enrollment/:id" element={<AdherenceEnrollmentDetailPage />} />
          <Route path="/adherence/sponsor/:slug" element={<AdherenceSponsorPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
