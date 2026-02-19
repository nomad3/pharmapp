import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import useAuth from "../hooks/useAuth";

export default function LoginPage() {
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [error, setError] = useState(null);
  const { requestOtp, verifyOtp } = useAuth();
  const navigate = useNavigate();

  const handleRequestOtp = async (e) => {
    e.preventDefault();
    try {
      await requestOtp(phone);
      setOtpSent(true);
    } catch { setError("Error enviando código"); }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    try {
      await verifyOtp(phone, code);
      navigate("/");
    } catch { setError("Código inválido o expirado"); }
  };

  return (
    <div className="login-page">
      <h2>Iniciar sesión</h2>
      {error && <p className="error">{error}</p>}
      {!otpSent ? (
        <form onSubmit={handleRequestOtp}>
          <input type="tel" placeholder="+56 9 1234 5678" value={phone} onChange={(e) => setPhone(e.target.value)} />
          <button type="submit">Enviar código por WhatsApp</button>
        </form>
      ) : (
        <form onSubmit={handleVerify}>
          <p>Código enviado a {phone}</p>
          <input type="text" placeholder="123456" maxLength={6} value={code} onChange={(e) => setCode(e.target.value)} />
          <button type="submit">Verificar</button>
        </form>
      )}
    </div>
  );
}
