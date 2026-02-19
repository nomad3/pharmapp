import React, { useEffect, useState } from "react";
import client from "../api/client";
import OrderStatusBadge from "../components/OrderStatusBadge";

export default function OrderHistoryPage() {
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    client.get("/orders").then(({ data }) => setOrders(data)).catch(console.error);
  }, []);

  return (
    <div className="order-history">
      <h2>Mis pedidos</h2>
      {orders.map((order) => (
        <div key={order.id} className="order-card">
          <p>Pedido #{order.id.slice(0, 8)}</p>
          <p>Total: ${order.total.toLocaleString("es-CL")}</p>
          <OrderStatusBadge status={order.status} />
        </div>
      ))}
    </div>
  );
}
