import { useState, useCallback } from "react";
import client from "../api/client";

export default function useAuth() {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem("token");
    return token ? { token } : null;
  });

  const requestOtp = useCallback(async (phoneNumber) => {
    await client.post("/auth/otp/request", { phone_number: phoneNumber });
  }, []);

  const verifyOtp = useCallback(async (phoneNumber, code) => {
    const { data } = await client.post("/auth/otp/verify", {
      phone_number: phoneNumber,
      code,
    });
    localStorage.setItem("token", data.access_token);
    setUser({ token: data.access_token });
    return data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setUser(null);
  }, []);

  return { user, requestOtp, verifyOtp, logout };
}
