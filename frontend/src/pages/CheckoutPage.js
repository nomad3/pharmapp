import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { useSearchParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import { useCart } from "../context/CartContext";

export default function CheckoutPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { items: cartItems, total: cartTotal, clearCart } = useCart();

  const fromCart = searchParams.get("from") === "cart";

  // Single-item params (legacy flow)
  const pharmacyId = fromCart ? (cartItems[0]?.pharmacy_id || null) : searchParams.get("pharmacy_id");
  const medicationId = fromCart ? (cartItems[0]?.medication_id || null) : searchParams.get("medication_id");
  const priceId = fromCart ? null : searchParams.get("price_id");
  const priceAmount = fromCart ? 0 : parseFloat(searchParams.get("price") || "0");
  const pharmacyName = fromCart ? "" : (searchParams.get("pharmacy_name") || "");
  const medicationName = fromCart ? "" : (searchParams.get("medication_name") || "");
  const isOnline = fromCart
    ? cartItems.some(i => i.is_online)
    : searchParams.get("is_online") === "true";

  const [quantity, setQuantity] = useState(1);
  const [paymentProvider, setPaymentProvider] = useState("mercadopago");
  const [addresses, setAddresses] = useState([]);
  const [selectedAddress, setSelectedAddress] = useState(null);
  const [showNewAddress, setShowNewAddress] = useState(false);
  const [newAddress, setNewAddress] = useState({ address: "", comuna: "", instructions: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const total = fromCart ? cartTotal : priceAmount * quantity;

  useEffect(() => {
    if (fromCart && cartItems.length === 0) {
      navigate("/cart");
      return;
    }
    if (!fromCart && (!pharmacyId || !medicationId)) {
      navigate("/");
      return;
    }
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }
    client.get("/addresses/")
      .then(({ data }) => {
        setAddresses(data);
        if (data.length > 0) setSelectedAddress(data[0].id);
      })
      .catch(() => {});
  }, [fromCart, pharmacyId, medicationId, cartItems.length, navigate]);

  const handleAddAddress = async () => {
    if (!newAddress.address || !newAddress.comuna) return;
    try {
      const { data } = await client.post("/addresses/", newAddress);
      setAddresses(prev => [...prev, data]);
      setSelectedAddress(data.id);
      setShowNewAddress(false);
      setNewAddress({ address: "", comuna: "", instructions: "" });
    } catch (err) {
      setError("Error al guardar la direccion");
    }
  };

  const handleConfirm = async () => {
    setLoading(true);
    setError("");
    try {
      const orderItems = fromCart
        ? cartItems.map(i => ({ medication_id: i.medication_id, price_id: i.price_id, quantity: i.quantity }))
        : [{ medication_id: medicationId, price_id: priceId, quantity }];
      const orderPharmacyId = fromCart ? cartItems[0]?.pharmacy_id : pharmacyId;

      const { data } = await client.post("/orders/", {
        pharmacy_id: orderPharmacyId,
        items: orderItems,
        payment_provider: paymentProvider,
        delivery_address_id: selectedAddress,
      });
      if (fromCart) clearCart();
      if (data.payment_url) {
        window.location.href = data.payment_url;
      } else {
        navigate(`/orders/${data.id}?status=pending`);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Error al crear la orden");
      setLoading(false);
    }
  };

  return (
    <div className="checkout-page">
      <Helmet>
        <title>Confirmar compra | Remedia</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <div className="container">
        <h1>Confirmar compra</h1>

        {/* Order Summary */}
        <div className="checkout-section">
          <h2>Resumen del pedido</h2>
          <div className="checkout-card">
            {fromCart ? (
              <>
                {cartItems.map(item => (
                  <div key={item.price_id} className="checkout-item" style={{ marginBottom: 12 }}>
                    <div className="checkout-item__name">{item.medication_name}</div>
                    <div className="checkout-item__pharmacy">
                      {item.pharmacy_name}
                      {item.is_online && <span className="online-tag">Online</span>}
                    </div>
                    <div className="checkout-item__price">
                      ${Math.round(item.price).toLocaleString("es-CL")} CLP x {item.quantity} = ${Math.round(item.price * item.quantity).toLocaleString("es-CL")} CLP
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <>
                <div className="checkout-item">
                  <div className="checkout-item__name">{medicationName}</div>
                  <div className="checkout-item__pharmacy">
                    {pharmacyName}
                    {isOnline && <span className="online-tag">Online</span>}
                  </div>
                  <div className="checkout-item__price">
                    ${priceAmount.toLocaleString("es-CL")} CLP c/u
                  </div>
                </div>
                <div className="checkout-quantity">
                  <label>Cantidad:</label>
                  <div className="quantity-controls">
                    <button onClick={() => setQuantity(q => Math.max(1, q - 1))} className="btn btn--sm">-</button>
                    <span className="quantity-value">{quantity}</span>
                    <button onClick={() => setQuantity(q => Math.min(10, q + 1))} className="btn btn--sm">+</button>
                  </div>
                </div>
              </>
            )}
            <div className="checkout-total">
              <span>Total:</span>
              <span className="checkout-total__amount">${Math.round(total).toLocaleString("es-CL")} CLP</span>
            </div>
          </div>
        </div>

        {/* Delivery Address */}
        {isOnline && (
          <div className="checkout-section">
            <h2>Direccion de entrega</h2>
            {addresses.length > 0 && (
              <div className="address-list">
                {addresses.map(addr => (
                  <label key={addr.id} className={`address-option ${selectedAddress === addr.id ? "selected" : ""}`}>
                    <input
                      type="radio"
                      name="address"
                      checked={selectedAddress === addr.id}
                      onChange={() => setSelectedAddress(addr.id)}
                    />
                    <div>
                      <div className="address-option__label">{addr.label}</div>
                      <div className="address-option__detail">{addr.address}, {addr.comuna}</div>
                      {addr.instructions && <div className="address-option__instructions">{addr.instructions}</div>}
                    </div>
                  </label>
                ))}
              </div>
            )}
            {showNewAddress ? (
              <div className="new-address-form">
                <input
                  type="text"
                  placeholder="Direccion (ej: Av. Providencia 1234)"
                  value={newAddress.address}
                  onChange={e => setNewAddress(prev => ({ ...prev, address: e.target.value }))}
                  className="input"
                />
                <input
                  type="text"
                  placeholder="Comuna"
                  value={newAddress.comuna}
                  onChange={e => setNewAddress(prev => ({ ...prev, comuna: e.target.value }))}
                  className="input"
                />
                <input
                  type="text"
                  placeholder="Instrucciones (opcional)"
                  value={newAddress.instructions}
                  onChange={e => setNewAddress(prev => ({ ...prev, instructions: e.target.value }))}
                  className="input"
                />
                <div className="new-address-actions">
                  <button onClick={handleAddAddress} className="btn btn--primary btn--sm">Guardar</button>
                  <button onClick={() => setShowNewAddress(false)} className="btn btn--sm">Cancelar</button>
                </div>
              </div>
            ) : (
              <button onClick={() => setShowNewAddress(true)} className="btn btn--outline btn--sm">
                + Agregar nueva direccion
              </button>
            )}
          </div>
        )}

        {/* Payment Method */}
        <div className="checkout-section">
          <h2>Medio de pago</h2>
          <div className="payment-options">
            <label className={`payment-option ${paymentProvider === "mercadopago" ? "selected" : ""}`}>
              <input
                type="radio"
                name="payment"
                value="mercadopago"
                checked={paymentProvider === "mercadopago"}
                onChange={e => setPaymentProvider(e.target.value)}
              />
              <div className="payment-option__content">
                <div className="payment-option__name">Mercado Pago</div>
                <div className="payment-option__desc">Tarjetas de credito/debito, transferencia</div>
              </div>
            </label>
            <label className={`payment-option ${paymentProvider === "transbank" ? "selected" : ""}`}>
              <input
                type="radio"
                name="payment"
                value="transbank"
                checked={paymentProvider === "transbank"}
                onChange={e => setPaymentProvider(e.target.value)}
              />
              <div className="payment-option__content">
                <div className="payment-option__name">Transbank Webpay</div>
                <div className="payment-option__desc">Tarjetas de credito/debito</div>
              </div>
            </label>
          </div>
        </div>

        {/* Confirm */}
        {error && <div className="checkout-error">{error}</div>}
        <button
          onClick={handleConfirm}
          disabled={loading}
          className="btn btn--primary btn--lg checkout-confirm"
        >
          {loading ? "Procesando..." : `Pagar $${total.toLocaleString("es-CL")} CLP`}
        </button>
      </div>
    </div>
  );
}
