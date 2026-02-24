import React from "react";
import { Helmet } from "react-helmet-async";
import { Link, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";

export default function CartPage() {
  const { items, removeItem, updateQuantity, total, itemCount, clearCart } = useCart();
  const navigate = useNavigate();

  if (items.length === 0) {
    return (
      <div className="cart-page">
        <Helmet>
          <title>Carrito | Remedia</title>
          <meta name="robots" content="noindex" />
        </Helmet>
        <div className="cart-empty">
          <div className="cart-empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
              <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
            </svg>
          </div>
          <h2>Tu carrito esta vacio</h2>
          <p>Agrega medicamentos para compararlos y comprar.</p>
          <Link to="/search" className="btn btn--primary">Buscar medicamentos</Link>
        </div>
      </div>
    );
  }

  const handleCheckout = () => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }
    navigate("/checkout?from=cart");
  };

  return (
    <div className="cart-page">
      <Helmet>
        <title>Carrito ({itemCount}) | Remedia</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <h1 className="page-title">Carrito ({itemCount})</h1>

      <div className="cart-items">
        {items.map(item => (
          <div key={item.price_id} className="cart-item">
            <div className="cart-item-info">
              <div className="cart-item-name">{item.medication_name}</div>
              <div className="cart-item-pharmacy">{item.pharmacy_name}</div>
              <div className="cart-item-price">${Math.round(item.price).toLocaleString("es-CL")} CLP c/u</div>
            </div>
            <div className="cart-item-controls">
              <button
                className="cart-qty-btn"
                onClick={() => updateQuantity(item.price_id, item.quantity - 1)}
              >
                -
              </button>
              <span className="cart-qty">{item.quantity}</span>
              <button
                className="cart-qty-btn"
                onClick={() => updateQuantity(item.price_id, item.quantity + 1)}
              >
                +
              </button>
            </div>
            <div className="cart-item-subtotal">
              ${Math.round(item.price * item.quantity).toLocaleString("es-CL")} CLP
            </div>
            <button className="cart-remove" onClick={() => removeItem(item.price_id)} title="Eliminar">
              &times;
            </button>
          </div>
        ))}
      </div>

      <div className="cart-total-section">
        <span className="cart-total-label">Total</span>
        <span className="cart-total-amount">${Math.round(total).toLocaleString("es-CL")} CLP</span>
      </div>

      <button className="cart-checkout-btn" onClick={handleCheckout}>
        Proceder al pago
      </button>
    </div>
  );
}
