import { useState, useCallback, useEffect } from "react";
import client from "../api/client";

export default function useAdherence() {
  const [programs, setPrograms] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadPrograms = useCallback(async () => {
    try {
      const { data } = await client.get("/adherence/programs");
      setPrograms(data);
    } catch (e) {
      console.error("Failed to load programs", e);
    }
  }, []);

  const loadEnrollments = useCallback(async () => {
    try {
      const { data } = await client.get("/adherence/enrollments");
      setEnrollments(data);
    } catch (e) {
      console.error("Failed to load enrollments", e);
    }
  }, []);

  const loadDashboard = useCallback(async () => {
    try {
      const { data } = await client.get("/adherence/dashboard");
      setDashboard(data);
    } catch (e) {
      console.error("Failed to load dashboard", e);
    }
    setLoading(false);
  }, []);

  const enroll = useCallback(async (programId, pharmacyPartnerId = null) => {
    const { data } = await client.post("/adherence/enroll", {
      program_id: programId,
      pharmacy_partner_id: pharmacyPartnerId,
      whatsapp_consent: true,
    });
    setEnrollments((prev) => [data, ...prev]);
    return data;
  }, []);

  const loadRefills = useCallback(async (enrollmentId) => {
    const { data } = await client.get(`/adherence/enrollment/${enrollmentId}/refills`);
    return data;
  }, []);

  useEffect(() => {
    loadPrograms();
  }, [loadPrograms]);

  return {
    programs, enrollments, dashboard, loading,
    loadPrograms, loadEnrollments, loadDashboard,
    enroll, loadRefills,
  };
}
