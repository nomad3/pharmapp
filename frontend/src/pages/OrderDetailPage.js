import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import OrderStatusBadge from "../components/OrderStatusBadge";

const PROVIDER_LABELS = {
  mercadopago: "Mercado Pago",
  transbank: "Transbank Webpay",
  cash_on_delivery: "Pago en Efectivo",
  bank_transfer: "Transferencia Bancaria",
};

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
        {paymentStatus === "transfer" && (
          <div className="payment-banner payment-banner--pending">
            <span className="payment-banner__icon">&#127974;</span>
            <div>
              <div className="payment-banner__title">Transferencia pendiente</div>
              <div className="payment-banner__desc">
                Realiza la transferencia y tu pedido sera confirmado al verificar el pago.
              </div>
            </div>
          </div>
        )}
        {paymentStatus === "cash" && (
          <div className="payment-banner payment-banner--success">
            <span className="payment-banner__icon">&#128176;</span>
            <div>
              <div className="payment-banner__title">Pedido confirmado</div>
              <div className="payment-banner__desc">
                Paga ${`$`}{order.total?.toLocaleString("es-CL")} CLP en efectivo al momento de la entrega.
              </div>
            </div>
          </div>
        )}

        <h1>Orden #{order.id.slice(0, 8)}</h1>
        <OrderStatusBadge status={order.status} />

        {/* Status Timeline */}
        {order.status !== "cancelled" && (() => {
          let steps;
          if (order.payment_provider === "cash_on_delivery") {
            steps = ["confirmed", "delivering", "awaiting_delivery_payment", "completed"];
          } else if (order.payment_provider === "bank_transfer") {
            steps = ["pending_transfer", "confirmed", "delivering", "completed"];
          } else {
            steps = ["pending", "payment_sent", "confirmed", "delivering", "completed"];
          }
          const stepLabels = {
            pending: "Pendiente",
            payment_sent: "Pago enviado",
            pending_transfer: "Esperando transferencia",
            confirmed: "Confirmado",
            delivering: "En camino",
            awaiting_delivery_payment: "Pago pendiente",
            completed: "Entregado",
          };
          const currentIdx = steps.indexOf(order.status);
          return (
            <div className="order-timeline">
              {steps.map((step, i) => (
                <div key={step} className={`timeline-step ${i <= currentIdx ? "timeline-step--active" : ""}`}>
                  <div className="timeline-step__dot" />
                  {i < steps.length - 1 && <div className="timeline-step__line" />}
                  <div className="timeline-step__label">{stepLabels[step]}</div>
                </div>
              ))}
            </div>
          );
        })()}
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
            <div>Medio: {PROVIDER_LABELS[order.payment_provider] || order.payment_provider}</div>
            {order.payment_status && <div>Estado: {order.payment_status}</div>}
            {order.payment_url && order.status === "payment_sent" && (
              <a href={order.payment_url} className="btn btn--primary btn--sm" style={{ marginTop: 8 }}>
                Completar pago
              </a>
            )}
          </div>
        </div>

        {/* Bank details for transfer payments */}
        {order.payment_provider === "bank_transfer" && order.status === "pending_transfer" && (
          <BankDetailsCard />
        )}

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

function BankDetailsCard() {
  const [details, setDetails] = useState(null);
  useEffect(() => {
    client.get("/settings/bank-details")
      .then(({ data }) => setDetails(data))
      .catch(() => {});
  }, []);
  if (!details || Object.keys(details).length === 0) return null;

  const copy = (text) => { navigator.clipboard.writeText(text); };
  const fields = [
    { label: "Banco", key: "bank_name" },
    { label: "Tipo de cuenta", key: "bank_account_type" },
    { label: "N\u00b0 de cuenta", key: "bank_account_number" },
    { label: "RUT", key: "bank_rut" },
    { label: "Titular", key: "bank_holder_name" },
    { label: "Email", key: "bank_email" },
  ];
  return (
    <div className="bank-details-card">
      <h3>Datos para transferencia</h3>
      {fields.map(f => details[f.key] ? (
        <div key={f.key} className="bank-detail-row">
          <span className="bank-detail-label">{f.label}</span>
          <span className="bank-detail-value">{details[f.key]}</span>
          <button className="bank-detail-copy" onClick={() => copy(details[f.key])} title="Copiar">
            &#128203;
          </button>
        </div>
      ) : null)}
    </div>
  );
}
