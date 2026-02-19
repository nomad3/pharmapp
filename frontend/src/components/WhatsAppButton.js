import React from "react";

export default function WhatsAppButton({ onClick, disabled }) {
  return (
    <button className="whatsapp-button" onClick={onClick} disabled={disabled}>
      Comprar por WhatsApp
    </button>
  );
}
