import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import OrderStatusBadge from "../components/OrderStatusBadge";

export default function OrderDetailPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  const paymentStatus = searchParams.get("status");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { navigate("/login"); return; }

    client.get(`/orders/${id}`)
      .then(({ data }) => { setOrder(data); setLoading(false); })
      .catch(() => { setLoading(false); });
  }, [id, navigate]);

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Cargando orden...</p>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="container">
        <h1>Orden no encontrada</h1>
        <button onClick={() => navigate("/orders")} className="btn btn--primary">
          Ver mis ordenes
        </button>
      </div>
    );
  }

  return (
    <div className="order-detail-page">
      <Helmet>
        <title>{`Orden #${id?.slice(0, 8)} | Remedia`}</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <div className="container">
        {/* Payment result banner */}
        {paymentStatus === "success" && (
          <div className="payment-banner payment-banner--success">
            <span className="payment-banner__icon">&#10003;</span>
            <div>
              <div className="payment-banner__title">Pago exitoso</div>
              <div className="payment-banner__desc">Tu pago fue procesado correctamente.</div>
            </div>
          </div>
        )}
        {paymentStatus === "failure" && (
          <div className="payment-banner payment-banner--failure">
            <span className="payment-banner__icon">&#10007;</span>
            <div>
              <div className="payment-banner__title">Pago no completado</div>
              <div className="payment-banner__desc">
                Hubo un problema con tu pago.
                {order.payment_url && (
                  <> <a href={order.payment_url}>Intentar de nuevo</a></>
                )}
              </div>
            </div>
          </div>
        )}
        {paymentStatus === "pending" && (
          <div className="payment-banner payment-banner--pending">
            <span className="payment-banner__icon">&#8987;</span>
            <div>
              <div className="payment-banner__title">Pago pendiente</div>
              <div className="payment-banner__desc">Tu pago esta siendo procesado.</div>
            </div>
          </div>
        )}

        <h1>Orden #{order.id.slice(0, 8)}</h1>
        <OrderStatusBadge status={order.status} />

        {/* Status Timeline */}
        {order.status !== "cancelled" && (
          <div className="order-timeline">
            {["pending", "payment_sent", "confirmed", "delivering", "completed"].map((step, i, arr) => {
              const currentIdx = arr.indexOf(order.status);
              const isActive = i <= currentIdx;
              const stepLabels = {
                pending: "Pendiente",
                payment_sent: "Pago enviado",
                confirmed: "Confirmado",
                delivering: "En camino",
                completed: "Entregado",
              };
              return (
                <div key={step} className={`timeline-step ${isActive ? "timeline-step--active" : ""}`}>
                  <div className="timeline-step__dot" />
                  {i < arr.length - 1 && <div className="timeline-step__line" />}
                  <div className="timeline-step__label">{stepLabels[step]}</div>
                </div>
              );
            })}
          </div>
        )}
        {order.status === "cancelled" && (
          <div className="payment-banner payment-banner--failure" style={{ marginTop: 16 }}>
            <span className="payment-banner__icon">&#10007;</span>
            <div>
              <div className="payment-banner__title">Orden cancelada</div>
            </div>
          </div>
        )}

        {/* Pharmacy */}
        {order.pharmacy && (
          <div className="order-section">
            <h2>Farmacia</h2>
            <div className="order-card">
              <div className="order-card__name">{order.pharmacy.name}</div>
              <div className="order-card__detail">{order.pharmacy.address}</div>
            </div>
          </div>
        )}

        {/* Items */}
        <div className="order-section">
          <h2>Productos</h2>
          {order.items?.map((item, i) => (
            <div key={i} className="order-item">
              <div className="order-item__name">{item.medication_name}</div>
              <div className="order-item__meta">
                <span>Cantidad: {item.quantity}</span>
                <span className="order-item__price">${item.subtotal?.toLocaleString("es-CL")} CLP</span>
              </div>
            </div>
          ))}
        </div>

        {/* Total */}
        <div className="order-section">
          <div className="order-total">
            <span>Total</span>
            <span className="order-total__amount">${order.total?.toLocaleString("es-CL")} CLP</span>
          </div>
        </div>

        {/* Payment info */}
        <div className="order-section">
          <h2>Pago</h2>
          <div className="order-card">
            <div>Medio: {order.payment_provider === "mercadopago" ? "Mercado Pago" : "Transbank Webpay"}</div>
            {order.payment_status && <div>Estado: {order.payment_status}</div>}
            {order.payment_url && order.status === "payment_sent" && (
              <a href={order.payment_url} className="btn btn--primary btn--sm" style={{ marginTop: 8 }}>
                Completar pago
              </a>
            )}
          </div>
        </div>

        <div className="order-actions">
          <button onClick={() => navigate("/orders")} className="btn btn--outline">
            Ver mis ordenes
          </button>
          <button onClick={() => navigate("/")} className="btn btn--primary">
            Seguir comprando
          </button>
        </div>
      </div>
    </div>
  );
}
