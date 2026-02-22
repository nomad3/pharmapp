import { useState, useCallback, useEffect } from "react";
import client from "../api/client";

export default function useGpo(slug) {
  const [group, setGroup] = useState(null);
  const [members, setMembers] = useState([]);
  const [intents, setIntents] = useState([]);
  const [demand, setDemand] = useState([]);
  const [orders, setOrders] = useState([]);
  const [savings, setSavings] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadGroup = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    try {
      const { data } = await client.get(`/gpo/groups/${slug}`);
      setGroup(data);
    } catch (e) {
      console.error("Failed to load GPO group", e);
    }
    setLoading(false);
  }, [slug]);

  const loadMembers = useCallback(async () => {
    if (!slug) return;
    try {
      const { data } = await client.get(`/gpo/groups/${slug}/members`);
      setMembers(data);
    } catch (e) {
      console.error("Failed to load members", e);
    }
  }, [slug]);

  const loadIntents = useCallback(async (month) => {
    if (!slug) return;
    try {
      const url = month
        ? `/gpo/groups/${slug}/intents?month=${month}`
        : `/gpo/groups/${slug}/intents`;
      const { data } = await client.get(url);
      setIntents(data);
    } catch (e) {
      console.error("Failed to load intents", e);
    }
  }, [slug]);

  const loadDemand = useCallback(async (month) => {
    if (!slug || !month) return;
    try {
      const { data } = await client.get(`/gpo/groups/${slug}/demand?month=${month}`);
      setDemand(data);
    } catch (e) {
      console.error("Failed to load demand", e);
    }
  }, [slug]);

  const loadOrders = useCallback(async () => {
    if (!slug) return;
    try {
      const { data } = await client.get(`/gpo/groups/${slug}/orders`);
      setOrders(data);
    } catch (e) {
      console.error("Failed to load orders", e);
    }
  }, [slug]);

  const loadSavings = useCallback(async () => {
    if (!slug) return;
    try {
      const { data } = await client.get(`/gpo/groups/${slug}/savings`);
      setSavings(data);
    } catch (e) {
      console.error("Failed to load savings", e);
    }
  }, [slug]);

  const submitIntent = useCallback(async (intentData) => {
    const { data } = await client.post(`/gpo/groups/${slug}/intents`, intentData);
    setIntents((prev) => [data, ...prev]);
    return data;
  }, [slug]);

  const cancelIntent = useCallback(async (intentId) => {
    await client.delete(`/gpo/groups/${slug}/intents/${intentId}`);
    setIntents((prev) => prev.filter((i) => i.id !== intentId));
  }, [slug]);

  useEffect(() => {
    loadGroup();
  }, [loadGroup]);

  return {
    group, members, intents, demand, orders, savings, loading,
    loadGroup, loadMembers, loadIntents, loadDemand, loadOrders, loadSavings,
    submitIntent, cancelIntent,
  };
}
