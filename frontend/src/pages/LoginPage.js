import React, { useState } from "react";
import { Helmet } from "react-helmet-async";
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
    setError(null);
    try {
      await requestOtp(phone);
      setOtpSent(true);
    } catch { setError("Error enviando código. Verifica tu número."); }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await verifyOtp(phone, code);
      navigate("/");
    } catch { setError("Código inválido o expirado. Intenta de nuevo."); }
  };

  return (
    <div className="login-page">
      <Helmet>
        <title>Iniciar sesion | PharmApp</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <div className="login-card">
        <div className="login-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
        </div>

        <h2>Iniciar sesión</h2>
        <p className="login-subtitle">
          {!otpSent
            ? "Ingresa tu número de teléfono y te enviaremos un código por WhatsApp"
            : "Ingresa el código de 6 dígitos que recibiste"
          }
        </p>

        {error && <div className="error-msg">{error}</div>}

        {!otpSent ? (
          <form onSubmit={handleRequestOtp}>
            <input
              type="tel"
              placeholder="+56 9 1234 5678"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              autoFocus
            />
            <button type="submit">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492a.5.5 0 00.612.638l4.704-1.376A11.95 11.95 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-2.24 0-4.317-.724-6.004-1.95a.5.5 0 00-.424-.067l-3.032.887.96-3.234a.5.5 0 00-.058-.408A9.953 9.953 0 012 12C2 6.486 6.486 2 12 2s10 4.486 10 10-4.486 10-10 10z"/></svg>
              Enviar código por WhatsApp
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerify}>
            <div className="otp-sent-msg">
              Código enviado a <strong>{phone}</strong>
            </div>
            <input
              className="otp-input"
              type="text"
              placeholder="000000"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              autoFocus
            />
            <button type="submit">Verificar código</button>
          </form>
        )}
      </div>
    </div>
  );
}
