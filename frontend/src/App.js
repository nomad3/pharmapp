import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import SearchResultsPage from "./pages/SearchResultsPage";
import MedicationDetailPage from "./pages/MedicationDetailPage";
import LoginPage from "./pages/LoginPage";
import OrderHistoryPage from "./pages/OrderHistoryPage";
import FavoritesPage from "./pages/FavoritesPage";
import PharmacyMapPage from "./pages/PharmacyMapPage";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchResultsPage />} />
        <Route path="/medication/:id" element={<MedicationDetailPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/orders" element={<OrderHistoryPage />} />
        <Route path="/favorites" element={<FavoritesPage />} />
        <Route path="/map" element={<PharmacyMapPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
