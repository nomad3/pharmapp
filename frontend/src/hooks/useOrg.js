import { useState, useCallback, useEffect } from "react";
import client from "../api/client";

export default function useOrg(slug) {
  const [org, setOrg] = useState(null);
  const [members, setMembers] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadOrg = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    try {
      const { data } = await client.get(`/organizations/${slug}`);
      setOrg(data);
      localStorage.setItem("org_slug", slug);
      localStorage.setItem("org_id", data.id);
    } catch (e) {
      console.error("Failed to load org", e);
    }
    setLoading(false);
  }, [slug]);

  const loadMembers = useCallback(async () => {
    if (!slug) return;
    try {
      const { data } = await client.get(`/organizations/${slug}/members`);
      setMembers(data);
    } catch (e) {
      console.error("Failed to load members", e);
    }
  }, [slug]);

  useEffect(() => {
    loadOrg();
  }, [loadOrg]);

  const inviteMember = useCallback(async (phoneNumber, role) => {
    const { data } = await client.post(`/organizations/${slug}/members`, {
      phone_number: phoneNumber,
      role,
    });
    setMembers((prev) => [...prev, data]);
    return data;
  }, [slug]);

  const removeMember = useCallback(async (userId) => {
    await client.delete(`/organizations/${slug}/members/${userId}`);
    setMembers((prev) => prev.filter((m) => m.user_id !== userId));
  }, [slug]);

  return { org, members, subscription, loading, loadOrg, loadMembers, inviteMember, removeMember };
}
