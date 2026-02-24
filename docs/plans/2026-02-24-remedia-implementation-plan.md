# Remedia Rebrand & Marketplace V2 — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebrand PharmApp → Remedia with new visual identity, build admin dashboard, improve search & discovery with cart, add user profile, and harden for production.

**Architecture:** 5 sequential feature areas. Rebrand first (touches CSS/text everywhere), then admin dashboard (new backend router + 4 frontend pages), search & discovery (filters + cart context + autocomplete), user profile (new page + backend prefs), production hardening (JWT refresh + health + logging).

**Tech Stack:** React 18, FastAPI, SQLAlchemy, PostgreSQL/PostGIS, CSS custom properties, Axios

---

## Task 1: Rebrand — Update CSS Variables & Color Palette

**Files:**
- Modify: `frontend/src/index.css` (lines 3-25)

**Step 1: Replace the CSS custom properties in `:root`**

Replace lines 3-25 of `index.css` with the new Remedia palette:

```css
:root {
  --primary: #0D9488;
  --primary-dark: #134E4A;
  --primary-light: #F0FDFA;
  --secondary: #14B8A6;
  --accent: #D97706;

  --bg: #F8FAFA;
  --bg-white: #FFFFFF;
  --bg-dark: #134E4A;

  --text: #1F2937;
  --text-secondary: #6B7280;
  --text-light: #9CA3AF;
  --text-inverse: #FFFFFF;

  --border: #D1D5DB;
  --border-light: #E5E7EB;

  --success: #10B981;
  --warning: #D97706;
  --error: #EF4444;
  --info: #0EA5E9;
```

**Step 2: Verify the app still renders**

Run: `open http://localhost:3002` — entire app should use new teal/amber palette via CSS variables.

**Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "style: update color palette to Remedia teal + amber"
```

---

## Task 2: Rebrand — Update Hardcoded Colors in App.css

**Files:**
- Modify: `frontend/src/App.css`

**Step 1: Replace hardcoded `#059669` / `#00875A` / `#006644` with CSS variables**

Search App.css for these hardcoded hex values and replace:
- `#059669` → `var(--primary)` (used in ~30 places: order totals, timeline, success states)
- `#00875A` → `var(--primary)` (referenced via var already, but check inline)
- `#006644` → `var(--primary-dark)` (hover states, dark accents)
- `#E3FCEF` → `var(--primary-light)` (light backgrounds)
- `#047857` → `var(--primary)` (alternate green)
- `#065f46` → `var(--primary-dark)` (dark green)
- `#16a34a` → `var(--primary)` (medium green)
- `#ecfdf5` → `var(--primary-light)` (very light green backgrounds)
- `#d97706` → `var(--accent)` (amber/warning — keep as-is, this is already the accent)

Also update the "Mejor precio" badge if it uses green to use `var(--accent)` instead (amber for deals).

**Step 2: Verify visually**

Reload the app, navigate through: homepage, search, medication detail, checkout, orders. All colors should be consistent teal/amber.

**Step 3: Commit**

```bash
git add frontend/src/App.css
git commit -m "style: replace hardcoded colors with CSS variables"
```

---

## Task 3: Rebrand — Update Brand Name & Text

**Files:**
- Modify: `frontend/src/components/Layout.js` (lines 17-18, 84-85)
- Modify: `backend/app/main.py` (line 12)
- Modify: `backend/app/services/whatsapp.py` (all message templates)
- Modify: `frontend/src/pages/HomePage.js`
- Modify: `frontend/src/pages/LoginPage.js`

**Step 1: Update Layout.js brand name**

In `Layout.js`:
- Line 18: `<span className="logo-text">PharmApp</span>` → `<span className="logo-text">Remedia</span>`
- Line 84-85: Update footer brand text similarly
- Also update the logo icon from `+` to `💊` or keep `+` (keep `+` for simplicity)

**Step 2: Update FastAPI title**

In `backend/app/main.py` line 12:
```python
app = FastAPI(title="Remedia API")
```

**Step 3: Update WhatsApp message templates**

In `backend/app/services/whatsapp.py`, replace all `*PharmApp` with `*Remedia`:
- Line 18: `"🔐 *Remedia — Código de verificación*\n\n"`
- Line 29: `"🛒 *Remedia — Pedido #{short_id}*\n\n"`
- Line 41: `"✅ *Remedia — Pago confirmado*\n\n"`
- Line 56: `"🚴 *Remedia — En camino*\n\n"`
- Line 61: `"📦 *Remedia — Entregado*\n\n"`
- Line 67: `"📋 *Remedia — Actualización*\n\n"`
- Line 77: `"💊 *Remedia — Alerta de precio*\n\n"`
- Line 87: `"🤝 *Remedia GPO — Umbral alcanzado*\n\n"`
- Line 98: `"📦 *Remedia GPO — Actualización de orden*\n\n"`
- Line 106: `"✅ *Remedia GPO — Asignación lista*\n\n"`
- Line 117: `"💊 *Remedia — Recordatorio de recarga*\n\n"`
- Line 127: `"✅ *Remedia — Recarga completada*\n\n"`
- Line 137: `"⚠️ *Remedia — Racha interrumpida*\n\n"`
- Line 147: `"🎉 *Remedia — Nuevo nivel de descuento*\n\n"`
- Lines 171, 195, 293-297: Update fallback messages

Also update references in `_handle_medication_search` and `handle_incoming_message`:
- Line 195: `pharmapp.cl` → `remedia.cl`
- Line 297: `pharmapp.cl` → `remedia.cl`

**Step 4: Update page titles in frontend**

Search all Helmet `<title>` tags in frontend pages:
- Any reference to "PharmApp" → "Remedia"
- Update HomePage hero text, LoginPage branding

**Step 5: Update CLAUDE.md and README.md references**

- `CLAUDE.md`: Update project overview "PharmApp" → "Remedia"
- `README.md`: Already updated (check and fix any remaining references)

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: rebrand PharmApp to Remedia across frontend and backend"
```

---

## Task 4: Admin — Backend User Model + Admin Dependency

**Files:**
- Modify: `backend/app/models/user.py` (add is_admin field)
- Modify: `backend/app/core/deps.py` (add require_admin dependency)

**Step 1: Add is_admin to User model**

In `backend/app/models/user.py`, add after line 10:
```python
is_admin = Column(Boolean, default=False, server_default="false")
notification_prefs = Column(JSON, nullable=True)  # for Task 10
```

**Step 2: Add require_admin dependency**

In `backend/app/core/deps.py`, add after `require_premium_user`:
```python
def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

**Step 3: Commit**

```bash
git add backend/app/models/user.py backend/app/core/deps.py
git commit -m "feat: add is_admin to User model and require_admin dependency"
```

---

## Task 5: Admin — Backend Stats & User Endpoints

**Files:**
- Create: `backend/app/api/v1/admin.py`
- Modify: `backend/app/api/v1/routes.py` (add admin router)

**Step 1: Create admin router**

Create `backend/app/api/v1/admin.py`:
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.deps import get_db, require_admin
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.models.price import Price
from app.models.scrape_run import ScrapeRun

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Aggregate dashboard stats."""
    total_users = db.query(func.count(User.id)).scalar()
    total_orders = db.query(func.count(Order.id)).scalar()
    total_revenue = db.query(func.coalesce(func.sum(Order.total), 0)).scalar()
    total_medications = db.query(func.count(Medication.id)).scalar()
    total_pharmacies = db.query(func.count(Pharmacy.id)).scalar()
    total_prices = db.query(func.count(Price.id)).scalar()

    # Orders today
    from datetime import datetime, timezone, timedelta
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    orders_today = db.query(func.count(Order.id)).filter(Order.created_at >= today_start).scalar()

    # Payment success rate
    total_paid = db.query(func.count(Order.id)).filter(
        Order.status.in_(["confirmed", "delivering", "completed"])
    ).scalar()

    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "orders_today": orders_today,
        "total_revenue": float(total_revenue),
        "payment_success_rate": round(total_paid / max(total_orders, 1) * 100, 1),
        "total_medications": total_medications,
        "total_pharmacies": total_pharmacies,
        "total_prices": total_prices,
    }


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List users with order counts."""
    q = db.query(
        User,
        func.count(Order.id).label("order_count"),
        func.coalesce(func.sum(Order.total), 0).label("total_spent"),
    ).outerjoin(Order, Order.user_id == User.id).group_by(User.id)

    if search:
        q = q.filter(User.phone_number.ilike(f"%{search}%") | User.name.ilike(f"%{search}%"))

    results = q.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": str(u.id),
            "phone_number": u.phone_number,
            "name": u.name,
            "created_at": str(u.created_at),
            "order_count": count,
            "total_spent": float(spent),
            "is_admin": u.is_admin,
        }
        for u, count, spent in results
    ]


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Get user detail with recent orders."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(404, "User not found")

    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "id": str(user.id),
        "phone_number": user.phone_number,
        "name": user.name,
        "created_at": str(user.created_at),
        "is_admin": user.is_admin,
        "orders": [
            {
                "id": str(o.id),
                "status": o.status.value if hasattr(o.status, 'value') else o.status,
                "total": float(o.total),
                "created_at": str(o.created_at),
            }
            for o in orders
        ],
    }
```

**Step 2: Register admin router in routes.py**

In `backend/app/api/v1/routes.py`, add import and include:
```python
from app.api.v1 import admin
api_router.include_router(admin.router)
```

**Step 3: Commit**

```bash
git add backend/app/api/v1/admin.py backend/app/api/v1/routes.py
git commit -m "feat: add admin API endpoints for stats and user management"
```

---

## Task 6: Admin — Frontend Dashboard & Orders Pages

**Files:**
- Create: `frontend/src/pages/admin/AdminDashboardPage.js`
- Create: `frontend/src/pages/admin/AdminOrdersPage.js`
- Modify: `frontend/src/App.js` (add admin routes)
- Modify: `frontend/src/App.css` (add admin styles)

**Step 1: Create AdminDashboardPage**

Create `frontend/src/pages/admin/AdminDashboardPage.js`:
- Fetch `GET /admin/stats` on mount
- Display summary cards: total users, total orders (today), revenue, medications, pharmacies, prices, payment success rate
- Show recent orders list (reuse existing `GET /orders/admin/all?limit=10`)
- Show scraping status (reuse `GET /scraping/runs?limit=5`)

Layout: 2-column grid of stat cards on top, recent orders table below, scraping status sidebar.

**Step 2: Create AdminOrdersPage**

Create `frontend/src/pages/admin/AdminOrdersPage.js`:
- Fetch `GET /orders/admin/all` with status filter and limit
- Table: order ID (first 8 chars), user phone, status badge, total, payment provider, date
- Status filter dropdown: All, Pending, Payment Sent, Confirmed, Delivering, Completed, Cancelled
- Click row → expand/modal showing order items
- Status update buttons per order (call `PATCH /orders/{id}/status`)

**Step 3: Add routes in App.js**

Add to App.js route definitions:
```javascript
import AdminDashboardPage from './pages/admin/AdminDashboardPage';
import AdminOrdersPage from './pages/admin/AdminOrdersPage';

// Inside <Routes>:
<Route path="/admin" element={<AdminDashboardPage />} />
<Route path="/admin/orders" element={<AdminOrdersPage />} />
<Route path="/admin/users" element={<AdminUsersPage />} />
<Route path="/admin/scraping" element={<AdminScrapingPage />} />
```

**Step 4: Add admin link to Layout.js**

In `Layout.js`, add admin nav link (conditionally shown — for now show to all users, restrict later):
```javascript
<Link to="/admin" className="nav-link">
  <span className="nav-icon">⚙️</span>
  <span>Admin</span>
</Link>
```

**Step 5: Add admin styles to App.css**

Add styles for:
- `.admin-grid` — CSS grid for stat cards (2-col on mobile, 4-col on desktop)
- `.stat-card` — card with label, value, trend
- `.admin-table` — full-width table with hover rows
- `.status-filter` — dropdown select styling

**Step 6: Commit**

```bash
git add frontend/src/pages/admin/ frontend/src/App.js frontend/src/App.css frontend/src/components/Layout.js
git commit -m "feat: add admin dashboard and orders management pages"
```

---

## Task 7: Admin — Frontend Users & Scraping Pages

**Files:**
- Create: `frontend/src/pages/admin/AdminUsersPage.js`
- Create: `frontend/src/pages/admin/AdminScrapingPage.js`

**Step 1: Create AdminUsersPage**

Create `frontend/src/pages/admin/AdminUsersPage.js`:
- Fetch `GET /admin/users` with search param
- Search input (debounced) for phone number
- Table: phone, name, orders, total spent, joined date
- Click row → fetch `GET /admin/users/{id}` and show detail panel with order history

**Step 2: Create AdminScrapingPage**

Create `frontend/src/pages/admin/AdminScrapingPage.js`:
- Fetch `GET /scraping/runs?limit=20` for run history
- Fetch `GET /scraping/schedule` for schedule info
- Per-chain cards showing last run status (group runs by chain)
- "Run Now" buttons that call:
  - `POST /scraping/catalog?chains=cruz_verde` (per chain)
  - `POST /scraping/catalog` (all chains)
- Run history table: chain, status, products found, prices upserted, errors, duration

**Step 3: Commit**

```bash
git add frontend/src/pages/admin/
git commit -m "feat: add admin users and scraping management pages"
```

---

## Task 8: Search — Backend Filters & Autocomplete

**Files:**
- Modify: `backend/app/api/v1/medications.py` (add filter params, autocomplete endpoint)

**Step 1: Add filter parameters to search endpoint**

In `backend/app/api/v1/medications.py`, update the search endpoint:
```python
@router.get("/search", response_model=list[MedicationOut])
def search_medications(
    q: str = Query(..., min_length=2),
    form: str | None = Query(None),
    requires_prescription: bool | None = Query(None),
    price_min: float | None = Query(None, ge=0),
    price_max: float | None = Query(None, ge=0),
    chain: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    # Clean Cenabast-style prefixes from search query
    clean_q = q.strip()
    # Also clean active_ingredient prefixes like "1-aciclovir"
    import re
    clean_pattern = re.sub(r'^\d+-', '', clean_q)

    query = db.query(Medication).filter(
        Medication.name.ilike(f"%{clean_q}%")
        | Medication.active_ingredient.ilike(f"%{clean_q}%")
        | Medication.active_ingredient.ilike(f"%{clean_pattern}%")
    )

    if form:
        query = query.filter(Medication.form.ilike(f"%{form}%"))
    if requires_prescription is not None:
        query = query.filter(Medication.requires_prescription == requires_prescription)

    # Price/chain filters require joining Price + Pharmacy
    if price_min is not None or price_max is not None or chain:
        from app.models.price import Price
        from app.models.pharmacy import Pharmacy
        query = query.join(Price, Price.medication_id == Medication.id)
        if chain:
            query = query.join(Pharmacy, Price.pharmacy_id == Pharmacy.id)
            query = query.filter(Pharmacy.chain.ilike(f"%{chain}%"))
        if price_min is not None:
            query = query.filter(Price.price >= price_min)
        if price_max is not None:
            query = query.filter(Price.price <= price_max)
        query = query.distinct()

    return query.offset(offset).limit(limit).all()
```

**Step 2: Add autocomplete endpoint**

Add to `medications.py`:
```python
@router.get("/autocomplete")
def autocomplete_medications(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Return top 8 medication name matches for search-as-you-type."""
    results = (
        db.query(Medication.name, Medication.slug, Medication.id)
        .filter(Medication.name.ilike(f"%{q}%"))
        .limit(8)
        .all()
    )
    return [
        {"name": r.name, "slug": r.slug, "id": str(r.id)}
        for r in results
    ]
```

**Step 3: Commit**

```bash
git add backend/app/api/v1/medications.py
git commit -m "feat: add search filters and autocomplete endpoint"
```

---

## Task 9: Search — Frontend Filters & Autocomplete

**Files:**
- Create: `frontend/src/components/SearchFilters.js`
- Create: `frontend/src/components/Autocomplete.js`
- Modify: `frontend/src/pages/SearchResultsPage.js`
- Modify: `frontend/src/components/Layout.js` (replace search input with autocomplete)
- Modify: `frontend/src/App.css` (filter & autocomplete styles)

**Step 1: Create SearchFilters component**

Create `frontend/src/components/SearchFilters.js`:
- Collapsible panel (collapsed by default on mobile)
- Filters:
  - Form: select dropdown (Comprimido, Cápsula, Líquido, Crema, Inyectable, Otro)
  - Requires prescription: Yes/No/All radio
  - Chain: checkboxes (Cruz Verde, Salcobrand, Ahumada, Dr. Simi)
  - Price range: min/max number inputs
- On change, update URL search params and trigger re-fetch
- "Clear filters" button

**Step 2: Create Autocomplete component**

Create `frontend/src/components/Autocomplete.js`:
- Debounced input (300ms) that calls `GET /medications/autocomplete?q={value}`
- Dropdown below input showing up to 8 suggestions
- Click suggestion → `navigate(/medicamento/${slug || id})`
- Enter key → `navigate(/search?q=${value})`
- Close dropdown on blur (with small delay for click handling)

**Step 3: Update SearchResultsPage**

Modify `frontend/src/pages/SearchResultsPage.js`:
- Add SearchFilters component in sidebar/top
- Read filter params from URL: `form`, `requires_prescription`, `chain`, `price_min`, `price_max`
- Pass all params to API call: `GET /medications/search?q=...&form=...&chain=...`
- Add result count display: "28 resultados para 'losartan'"
- Add pagination: offset + limit controls

**Step 4: Replace search input in Layout.js with Autocomplete**

In `Layout.js`, replace the search form with the Autocomplete component.

**Step 5: Add styles**

Add CSS for:
- `.search-filters` — sidebar panel, collapsible on mobile
- `.filter-group` — labeled filter section
- `.autocomplete-dropdown` — positioned below search input, shadow, z-index
- `.autocomplete-item` — hover highlight, click target

**Step 6: Commit**

```bash
git add frontend/src/components/SearchFilters.js frontend/src/components/Autocomplete.js frontend/src/pages/SearchResultsPage.js frontend/src/components/Layout.js frontend/src/App.css
git commit -m "feat: add search filters, autocomplete, and pagination"
```

---

## Task 10: Search — Shopping Cart

**Files:**
- Create: `frontend/src/context/CartContext.js`
- Create: `frontend/src/pages/CartPage.js`
- Modify: `frontend/src/App.js` (wrap with CartProvider, add /cart route)
- Modify: `frontend/src/components/Layout.js` (cart icon in navbar)
- Modify: `frontend/src/pages/MedicationDetailPage.js` (add to cart button)
- Modify: `frontend/src/pages/CheckoutPage.js` (support multi-item from cart)
- Modify: `frontend/src/App.css` (cart styles)

**Step 1: Create CartContext**

Create `frontend/src/context/CartContext.js`:
```javascript
import { createContext, useContext, useState, useEffect } from 'react';

const CartContext = createContext();

export function CartProvider({ children }) {
  const [items, setItems] = useState(() => {
    const saved = localStorage.getItem('remedia_cart');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem('remedia_cart', JSON.stringify(items));
  }, [items]);

  const addItem = (item) => {
    setItems(prev => {
      const existing = prev.find(i => i.price_id === item.price_id);
      if (existing) {
        return prev.map(i =>
          i.price_id === item.price_id ? { ...i, quantity: i.quantity + 1 } : i
        );
      }
      return [...prev, { ...item, quantity: 1 }];
    });
  };

  const removeItem = (priceId) => {
    setItems(prev => prev.filter(i => i.price_id !== priceId));
  };

  const updateQuantity = (priceId, quantity) => {
    if (quantity < 1) return removeItem(priceId);
    setItems(prev => prev.map(i =>
      i.price_id === priceId ? { ...i, quantity } : i
    ));
  };

  const clearCart = () => setItems([]);

  const total = items.reduce((sum, i) => sum + i.price * i.quantity, 0);
  const itemCount = items.reduce((sum, i) => sum + i.quantity, 0);

  return (
    <CartContext.Provider value={{ items, addItem, removeItem, updateQuantity, clearCart, total, itemCount }}>
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
```

**Step 2: Create CartPage**

Create `frontend/src/pages/CartPage.js`:
- List all cart items with quantity controls (+/-)
- Remove button per item
- Total at bottom
- "Proceder al pago" button → navigate to `/checkout?from=cart`
- Empty state: "Tu carrito está vacío" with link to search

**Step 3: Wrap App with CartProvider**

In `App.js`, wrap the BrowserRouter content with `<CartProvider>`.

Add route: `<Route path="/cart" element={<CartPage />} />`

**Step 4: Add cart icon to Layout.js**

In `Layout.js` nav, add cart link with badge:
```javascript
<Link to="/cart" className="nav-link cart-link">
  <span className="nav-icon">🛒</span>
  <span>Carrito</span>
  {itemCount > 0 && <span className="cart-badge">{itemCount}</span>}
</Link>
```

**Step 5: Add "Agregar al carrito" button in MedicationDetailPage**

In `MedicationDetailPage.js`, next to the "Comprar" button, add:
```javascript
<button onClick={() => addToCart({
  medication_id: medId,
  pharmacy_id: priceItem.pharmacy.id,
  price_id: priceItem.price_id,
  price: priceItem.price,
  medication_name: medication.name,
  pharmacy_name: priceItem.pharmacy.name,
  is_online: priceItem.is_online,
})}>
  Agregar al carrito
</button>
```

**Step 6: Update CheckoutPage to support cart items**

In `CheckoutPage.js`, detect `from=cart` param:
- If from cart: read items from CartContext instead of URL params
- Order creation body sends all items: `items: cartItems.map(i => ({medication_id, price_id, quantity}))`
- Show all items in order summary
- Clear cart after successful order creation

**Step 7: Add cart styles**

Add CSS for `.cart-page`, `.cart-item`, `.cart-badge`, `.cart-total`, `.cart-empty`.

**Step 8: Commit**

```bash
git add frontend/src/context/CartContext.js frontend/src/pages/CartPage.js frontend/src/pages/MedicationDetailPage.js frontend/src/pages/CheckoutPage.js frontend/src/App.js frontend/src/components/Layout.js frontend/src/App.css
git commit -m "feat: add shopping cart with multi-item checkout"
```

---

## Task 11: User Profile — Backend Endpoints

**Files:**
- Modify: `backend/app/api/v1/auth.py` (add profile endpoints)

**Step 1: Add profile endpoints to auth router**

In `backend/app/api/v1/auth.py`, add:

```python
@router.get("/profile")
def get_profile(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "phone_number": user.phone_number,
        "name": user.name,
        "comuna": user.comuna,
        "notification_prefs": user.notification_prefs or {
            "order_updates": True,
            "price_alerts": True,
            "refill_reminders": True,
            "promotions": False,
        },
        "created_at": str(user.created_at),
    }


@router.put("/profile")
def update_profile(
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if "name" in body:
        user.name = body["name"]
    if "comuna" in body:
        user.comuna = body["comuna"]
    if "notification_prefs" in body:
        user.notification_prefs = body["notification_prefs"]
    db.commit()
    return {"status": "updated"}
```

**Step 2: Commit**

```bash
git add backend/app/api/v1/auth.py
git commit -m "feat: add user profile get/update endpoints"
```

---

## Task 12: User Profile — Frontend Page

**Files:**
- Create: `frontend/src/pages/ProfilePage.js`
- Modify: `frontend/src/App.js` (add /profile route)
- Modify: `frontend/src/App.css` (profile styles)

**Step 1: Create ProfilePage**

Create `frontend/src/pages/ProfilePage.js`:
- Sections:
  1. **Personal info**: phone (read-only), name (editable), comuna (editable)
  2. **Delivery addresses**: list from `GET /addresses/`, add/edit/delete, set default
  3. **Notification preferences**: toggles for order_updates, price_alerts, refill_reminders, promotions
  4. **Account**: logout button, app version
- Save button calls `PUT /auth/profile`
- Success toast on save

**Step 2: Add route and nav link**

In `App.js`: `<Route path="/profile" element={<ProfilePage />} />`

In `Layout.js`, add profile link near the logout/login area.

**Step 3: Add styles**

Profile form styling: `.profile-section`, `.profile-field`, `.toggle-switch`, `.address-card`.

**Step 4: Commit**

```bash
git add frontend/src/pages/ProfilePage.js frontend/src/App.js frontend/src/components/Layout.js frontend/src/App.css
git commit -m "feat: add user profile page with notifications and addresses"
```

---

## Task 13: Production — JWT Token Refresh

**Files:**
- Modify: `backend/app/core/security.py` (add refresh logic)
- Modify: `backend/app/api/v1/auth.py` (add refresh endpoint)
- Modify: `frontend/src/api/client.js` (add 401 interceptor with refresh)

**Step 1: Add refresh token endpoint**

In `backend/app/api/v1/auth.py`, add:
```python
@router.post("/refresh")
def refresh_token(user: User = Depends(get_current_user)):
    """Issue a new JWT if the current one is still valid."""
    new_token = create_access_token(str(user.id))
    return {"access_token": new_token}
```

**Step 2: Add Axios response interceptor for auto-refresh**

In `frontend/src/api/client.js`, add response interceptor:
```javascript
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const { data } = await client.post("/auth/refresh");
        localStorage.setItem("token", data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return client(originalRequest);
      } catch {
        localStorage.removeItem("token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
```

**Step 3: Commit**

```bash
git add backend/app/api/v1/auth.py frontend/src/api/client.js
git commit -m "feat: add JWT token refresh with auto-retry on 401"
```

---

## Task 14: Production — Health Check & Request ID Middleware

**Files:**
- Modify: `backend/app/main.py` (add health endpoint)
- Create: `backend/app/middleware/request_id.py`
- Modify: `backend/app/main.py` (add request_id middleware)

**Step 1: Add health check endpoint**

In `backend/app/main.py`, add before the startup event:
```python
@app.get("/health")
def health_check():
    """Health check for monitoring and Docker."""
    from app.core.database import SessionLocal
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False

    from app.models.scrape_run import ScrapeRun
    try:
        db = SessionLocal()
        last_scrape = db.query(ScrapeRun).order_by(ScrapeRun.finished_at.desc()).first()
        db.close()
        scrape_age_hours = None
        if last_scrape and last_scrape.finished_at:
            from datetime import datetime, timezone
            scrape_age_hours = round(
                (datetime.now(timezone.utc) - last_scrape.finished_at).total_seconds() / 3600, 1
            )
    except Exception:
        scrape_age_hours = None

    status = "healthy" if db_ok else "unhealthy"
    return {
        "status": status,
        "database": "ok" if db_ok else "error",
        "last_scrape_hours_ago": scrape_age_hours,
    }
```

**Step 2: Create request ID middleware**

Create `backend/app/middleware/request_id.py`:
```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

**Step 3: Add middleware to app**

In `backend/app/main.py`, add after CORS middleware:
```python
from app.middleware.request_id import RequestIdMiddleware
app.add_middleware(RequestIdMiddleware)
```

**Step 4: Update docker-compose healthcheck**

In `docker-compose.yml`, add healthcheck to backend service:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

**Step 5: Commit**

```bash
git add backend/app/main.py backend/app/middleware/request_id.py docker-compose.yml
git commit -m "feat: add health check endpoint and request ID middleware"
```

---

## Task 15: Final — Update Documentation & Verify

**Files:**
- Modify: `README.md` (update brand name references if any remain)
- Modify: `CLAUDE.md` (update to Remedia)

**Step 1: Search for remaining "PharmApp" references**

```bash
grep -ri "pharmapp" --include="*.js" --include="*.py" --include="*.md" --include="*.yml" --include="*.json" frontend/ backend/ *.md
```

Replace any remaining references with "Remedia".

**Step 2: Rebuild and verify**

```bash
DB_PORT=5435 WEB_PORT=3002 docker-compose up --build -d
```

Verify:
- Homepage shows "Remedia" brand with teal/amber colors
- Search works with filters
- Cart adds items, checkout processes multi-item order
- Admin dashboard loads at /admin
- Profile page loads at /profile
- `/health` returns healthy status
- JWT refresh works (check network tab after 401)

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: final Remedia rebrand cleanup and documentation update"
```

---

## Summary

| Task | Area | Estimate |
|------|------|----------|
| 1 | Rebrand — CSS variables | Quick |
| 2 | Rebrand — Hardcoded colors | Medium |
| 3 | Rebrand — Brand name & text | Medium |
| 4 | Admin — User model + dependency | Quick |
| 5 | Admin — Backend stats/users API | Medium |
| 6 | Admin — Frontend dashboard + orders | Large |
| 7 | Admin — Frontend users + scraping | Large |
| 8 | Search — Backend filters + autocomplete | Medium |
| 9 | Search — Frontend filters + autocomplete | Large |
| 10 | Search — Shopping cart | Large |
| 11 | Profile — Backend endpoints | Quick |
| 12 | Profile — Frontend page | Medium |
| 13 | Production — JWT refresh | Medium |
| 14 | Production — Health + request ID | Medium |
| 15 | Final — Docs + verify | Quick |
