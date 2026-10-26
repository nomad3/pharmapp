"""Offline regression coverage for payment callbacks during fulfillment.

Execute the real handler bodies and order enum extracted from source, replacing
only their external dependencies. This avoids importing application settings,
reading .env, or requiring payment SDKs and database packages in a test runner.
It exercises state transitions, not FastAPI routing or database integration.
"""

import ast
import enum
import logging
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch


APP = Path(__file__).resolve().parents[1] / "app"


def module(name, **attributes):
    result = ModuleType(name)
    result.__path__ = []
    result.__dict__.update(attributes)
    return result


def load_definitions(relative_path, names, namespace):
    """Keep the production bodies intact; omit imports and route decorators."""
    tree = ast.parse((APP / relative_path).read_text())
    definitions = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef)) and node.name in names]
    if {node.name for node in definitions} != set(names):
        raise AssertionError("Expected production definitions were not found")
    for definition in definitions:
        definition.decorator_list = []
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    selected = ast.fix_missing_locations(ast.Module(body=[future, *definitions], type_ignores=[]))
    exec(compile(selected, str(APP / relative_path), "exec"), namespace)


class PaymentFulfillmentTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.notify = AsyncMock()
        self.commission = Mock()
        self.refill = Mock()
        self.transaction = Mock()
        self.transaction_class = Mock(return_value=self.transaction)
        stubs = {name: module(name) for name in (
            "transbank", "transbank.webpay", "transbank.webpay.webpay_plus",
        )}
        stubs.update({
            "transbank.webpay.webpay_plus.transaction": module(
                "transbank.webpay.webpay_plus.transaction", Transaction=self.transaction_class,
            ),
        })
        imports = patch.dict(sys.modules, stubs)
        imports.start()
        self.addCleanup(imports.stop)
        self.order_model = module("synthetic_order", enum=enum, Order=type("Order", (), {"id": "order-id-column"}))
        load_definitions("models/order.py", ["OrderStatus"], self.order_model.__dict__)
        self.status = self.order_model.OrderStatus
        self.handlers = module(
            "synthetic_webhooks", OrderStatus=self.status, Order=self.order_model.Order,
            User=type("User", (), {"id": "user-id-column"}),
            settings=SimpleNamespace(FRONTEND_URL="https://frontend.invalid"),
            Depends=lambda dependency: None,
            get_db=Mock(side_effect=AssertionError("Database dependency must not run")),
            _fetch_mp_payment=Mock(side_effect=AssertionError("Payment fetch must be mocked")),
            whatsapp=SimpleNamespace(send_payment_confirmed=self.notify),
            record_commission=self.commission, record_refill_from_order=self.refill,
            logger=logging.getLogger(__name__),
            RedirectResponse=lambda url, status_code: SimpleNamespace(
                status_code=status_code, headers={"location": url},
            ),
        )
        load_definitions("api/v1/webhooks.py", ["mercadopago_webhook", "transbank_webhook"], self.handlers.__dict__)
        self.order = SimpleNamespace(
            id="synthetic-order", user_id="synthetic-user", status=self.status.pending,
            payment_status="pending",
        )
        self.user = SimpleNamespace(phone_number="synthetic-phone")
        self.db = Mock()
        order_query = Mock()
        order_query.filter.return_value.first.return_value = self.order
        user_query = Mock()
        user_query.filter.return_value.first.return_value = self.user
        self.db.query.side_effect = lambda model: order_query if model is self.order_model.Order else user_query

    async def approve(self, provider):
        if provider == "mercadopago":
            request = SimpleNamespace(json=AsyncMock(return_value={"type": "payment", "data": {"id": "synthetic-payment"}}))
            with patch.object(self.handlers, "_fetch_mp_payment", return_value={
                "status": "approved", "external_reference": self.order.id,
            }):
                response = await self.handlers.mercadopago_webhook(request, self.db)
            self.assertEqual(response, {"status": "ok"})
            self.assertEqual(self.order.payment_status, "approved")
        else:
            request = SimpleNamespace(form=AsyncMock(return_value={"token_ws": "synthetic-token"}))
            self.transaction.commit.return_value = {"status": "AUTHORIZED", "buy_order": self.order.id}
            response = await self.handlers.transbank_webhook(request, self.db)
            self.transaction.commit.assert_called_with("synthetic-token")
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], f"https://frontend.invalid/orders/{self.order.id}?status=success")
            self.assertEqual(self.order.payment_status, "authorized")

    async def check_fulfillment_preserved(self, provider):
        for status in (self.status.delivering, self.status.completed):
            with self.subTest(provider=provider, status=status):
                self.order.status = status
                self.order.payment_status = "pending"
                # Both the late notification and its replay must preserve progress.
                await self.approve(provider)
                self.assertEqual(self.order.status, status)
                await self.approve(provider)
                self.assertEqual(self.order.status, status)
        # This repair changes fulfillment state only, not existing callback effects.
        self.assertEqual(self.db.commit.call_count, 4)
        self.assertEqual(self.commission.call_count, 4)
        self.assertEqual(self.refill.call_count, 4)
        self.assertEqual(self.notify.await_count, 4)

    async def test_mercadopago_preserves_delivery_and_completion(self):
        await self.check_fulfillment_preserved("mercadopago")

    async def test_transbank_preserves_delivery_and_completion(self):
        await self.check_fulfillment_preserved("transbank")

    async def check_normal_confirmation(self, provider):
        for status in (self.status.pending, self.status.payment_sent, self.status.confirmed):
            with self.subTest(provider=provider, status=status):
                self.order.status = status
                self.order.payment_status = "pending"
                await self.approve(provider)
                self.assertEqual(self.order.status, self.status.confirmed)
        self.assertEqual(self.db.commit.call_count, 3)
        self.assertEqual(self.commission.call_count, 3)
        self.assertEqual(self.refill.call_count, 3)
        self.assertEqual(self.notify.await_count, 3)
        self.commission.assert_called_with(self.db, self.order)
        self.refill.assert_called_with(self.db, self.order)
        self.notify.assert_awaited_with(self.user.phone_number, self.order.id)

    async def test_mercadopago_still_confirms_and_records_payment(self):
        await self.check_normal_confirmation("mercadopago")

    async def test_transbank_still_confirms_and_records_payment(self):
        await self.check_normal_confirmation("transbank")


if __name__ == "__main__":
    unittest.main()
