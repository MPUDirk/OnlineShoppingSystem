## 1. Requirement interpretation

The assignment asks for **sales reports** that support an **online business** mindset: not merely raw database dumps, but **aggregated metrics** that a vendor can interpret without writing SQL. The brief explicitly mentions **daily, weekly, monthly, and annual** perspectives, **growth** awareness, and metrics ranging from **weekly volume** to **top products**, and it requires the team to **test the design with sample data**.

Our implementation interprets these points as follows:

1. **Time windows** must be **selectable** and **consistent** with the store’s timezone (`Asia/Macau` in project settings), so “today” and “this month” mean what a merchant expects locally.
2. **Revenue** must align with how orders are actually recorded in this codebase: **per line item** (`OrderItem.subtotal`), because checkout creates **one `Order` per vendor line** in the existing flow—so “orders” in KPIs are **distinct parent orders** at the line level, which matches the vendor order list semantics.
3. **Cancelled** sales must not pollute analytics; only **non-cancelled** order lines count.
4. **Vendors** must see **only their products’ lines**; **staff** may see **all** lines for administration.

The following sections explain the architecture, algorithms, user interface, testing aids, and how each design choice follows from the domain model and the Block V brief.

---

## 2. Data foundation: `OrderItem` as the unit of analysis

The analytics layer treats each **`OrderItem`** as one economic event tied to a **product**, an **order**, and a **purchase timestamp** (via `order.purchase_date`). Aggregations use Django’s ORM: **`Sum('subtotal')`** for money, **`Count('order_id', distinct=True)`** for how many distinct checkout orders touch the vendor’s catalog in the window.

The queryset factory **`sales_orderitem_queryset(user)`** (in `vendor/analytics.py`) centralizes access rules:

- It **excludes** lines whose parent order has **`status='cancelled'`**.
- If the user is **staff or superuser**, it returns **all** qualifying lines.
- Otherwise it restricts to lines where **`product.created_by`** is the current user, i.e. the **vendor** who owns the SKU/product.

This single entry point keeps the **KPI block**, **chart series**, and **top-products table** **consistent** with each other and with the mental model of “my sales” on the vendor portal.

---

## 3. Period presets: daily, weekly, monthly, and yearly views

The view accepts a GET parameter **`period`**, validated against a whitelist: **`today`**, **`week`**, **`month`**, **`year`**. Invalid values fall back to **`month`**, which is also the default—reasonable for a dashboard opened without query strings.

The helper **`resolve_period(period)`** returns a **`PeriodBounds`** object: **`start`**, **`end`** (inclusive upper bound in the filter sense), and **`granularity`** for chart bucketing:

- **`today`**: from **midnight** local time through **now**.
- **`week`**: the **last seven calendar days** from the start of the day six days ago through **now** (a rolling week aligned to day boundaries).
- **`month`**: **last 12 calendar months** — from the first day of the month **11 months before** the current month through **now**; chart bars are **one month each**.
- **`year`**: **last 5 calendar years** — from **January 1** of **(current year − 4)** through **now**; chart bars are **one calendar year each** (e.g. 2022 … 2026).

**Chart bucket granularity (X-axis):** **`today`** = hourly; **`week`** = daily; **`month`** = monthly over that 12-month window; **`year`** = yearly over that 5-year window. The UI labels these presets **Month** and **Year** (not “this month / this year”).

These presets support multi-period business views (“近几个月 / 近五年”). If a rubric requires different window lengths (e.g. 6 months or 10 years), adjust **`resolve_period`** only.

---

## 4. KPIs: revenue, orders, and average order value

For any **`[start, end]`** window, **`kpi_for_range(qs, start, end)`** computes:

1. **Total revenue** — sum of **`subtotal`** on filtered lines.  
2. **Order count** — distinct **`order_id`** values (because one logical customer checkout may produce multiple `Order` rows in this system, counting lines would inflate “orders”).  
3. **Average revenue per order** — revenue divided by that distinct count, or zero if there are no orders.

These three numbers are shown as **cards** on the vendor sales report page. They give a **snapshot** answer to “how much did I sell, how many separate orders did that span, and what is a typical order size?”—a compact answer to the **performance metrics** part of Block V.

---

## 5. Growth and trends: time series without fragile SQL time zones

The brief asks vendors to understand **growth**. We address that with a **time-series chart**: for each bucket inside `[start, end]`, we plot **revenue** (bars) and **distinct order count** (line) so that **directional change** over the window is visible—e.g. **hour-of-day** patterns for “Today,” **day-of-week** patterns for “Last 7 days,” and **month-by-month** stacks for “This year.”

An important **implementation constraint** emerged during development: on **MySQL**, Django’s **`TruncDay` / `TruncMonth`** database functions can rely on **`CONVERT_TZ`**, which fails if **MySQL time zone tables** are not installed, producing **invalid datetime** errors at runtime. Rather than requiring every teammate to load zone tables, **`timeseries_for_range`** pulls **`values_list('order__purchase_date', 'order_id', 'subtotal')`** and **buckets in Python** using **`localtime`** rules with **`granularity`** **`hour`**, **`day`**, or **`month`** depending on the selected period.

This trades a bit of **application CPU** for **portability** and **predictable behavior** in student environments—an explicit **design trade-off** documented here because it affects **how** the chart is produced, not just what it displays.

---

## 6. Top-performing products

**`top_products(qs, start, end, limit=10)`** groups lines by **product**, ranks by **descending revenue**, and returns **name**, **slug** (for linking to the SEO-friendly storefront URL), **units sold**, **line count**, and **revenue**. This directly satisfies the **top-performing products** requirement and connects reporting back to **merchandising**: a vendor can see which SKUs drive revenue in the selected window.

---

## 7. Presentation layer: view, route, and template

**`VendorSalesReportView`** (`vendor/views.py`) is a **`TemplateView`** protected by **`VendorOrAdminRequiredMixin`**: only **Vendor** group members or **staff/superusers** may access it. It wires together **`resolve_period`**, **`kpi_for_range`**, **`timeseries_for_range`**, and **`top_products`**, and passes **Chart.js**-friendly **`chart_data`** (`labels`, `revenue`, `orders`) to the template, along with human-readable **period titles**, **start/end bounds** for transparency, and a **footnote** explaining **cancellation exclusion** and **subtotal** basis.

The URL **`/vendor/reports/`** (`vendor:sales_reports`) is linked from the **main navigation** (for authorized roles) and from the **vendor home** page. The template **`vendor/sales_reports.html`** provides a **period `<select>`**, KPI cards, a **combined bar/line chart**, and a **sortable-style table** for top products—enough for a coursework demo and usability review.

---

## 8. Sample data and reproducibility (`seed_sales_reports_demo`)

The assignment requires **testing with sample data**. The management command **`seed_sales_reports_demo`** creates or reuses **demo vendor and customer users**, a **category**, **product**, **SKU**, and then:

- **`--days N`** (default **14**): one delivered order per day for the last *N* days (good for **Today** / **Week**).  
- **`--months M`** (e.g. **12**): one order per calendar month for the last *M* months (good for the **Month** chart).  
- **`--years Y`** (e.g. **5**): one order per calendar year for the last *Y* years (good for the **Year** chart).

Example: `python manage.py seed_sales_reports_demo --days 14 --months 12 --years 5`

This command is the **primary** way for teammates to **populate** realistic series **without manual SQL**, which supports both **manual QA** and **demonstrations**.

### 8.1 Viewing the demo (runserver + login)

1. Start the app: `python manage.py runserver`  
2. (Optional) Load data: `python manage.py seed_sales_reports_demo --days 14 --months 12 --years 5`  
3. Open the login page (this project): **`http://127.0.0.1:8000/user/login/`**  
4. Sign in as the seeded vendor: username **`demo_vendor`**, password **`demo123456`** (defaults; override with `--vendor-username` / `--password` when seeding).  
5. Open sales reports: **`http://127.0.0.1:8000/vendor/reports/`** (or use the **Sales reports** link in the header after login).

**If login fails:** run the seed command again. It **always resets** the password and sets **`is_active=True`** for `demo_vendor` and `demo_customer`, so credentials match the last `--password` you passed (default `demo123456`).

---

## 9. Automated tests (`vendor/tests.py`)

**`VendorSalesReportViewTests`** exercises critical **correctness** properties:

- A **vendor** only sees **their** lines; a **cancelled** order does not contribute to KPIs.  
- **Staff** sees **aggregated** lines across vendors.  
- An invalid **`period`** query falls back to **`month`**.

Tests construct **`Order`** / **`OrderItem`** rows programmatically and adjust **`purchase_date`** via **`QuerySet.update`** to simulate historical activity—mirroring how demo data is produced. These tests give **regression safety** when analytics helpers change.

---

## 10. How Block V shaped the wider system design

Block V did not add a separate microservice; it **reused** existing models and permissions. Consequences include:

- **Consistency with checkout**: because revenue is **line subtotal**, reports **match** what vendors already see in order lists.  
- **Security**: reusing **`VendorOrAdminRequiredMixin`** keeps **authorization** aligned with other vendor pages.  
- **Performance**: for large catalogs, future work could add **database indexes** on **`order.purchase_date`** or **materialized summaries**; the coursework scope keeps queries **readable** first.  
- **Documentation**: this file and inline docstrings explain **definitions** so graders and teammates know what “order count” means in a **multi-order checkout** design.

---

## 11. Conclusion

Block V is implemented as a **cohesive vendor analytics page**: **selectable periods**, **KPI cards**, **time-series chart**, **top products table**, **footnote** on data rules, **seed command** for sample data, and **unit tests** for core behaviors. The design consciously balances **business clarity**, **alignment with existing order data**, **multi-tenant vendor isolation**, and **portability** across database setups—fulfilling the coursework ask to **design suitable sales reports** and **test them with sample data**.

