# Project Overview and SEO Implementation (English Summary)

**Course context:** This document summarizes the *Online Shopping System* group project (Django-based e-commerce storefront with customer accounts, cart, checkout, vendor product management, SKU configuration, sales analytics, and security-oriented settings). It then explains **what SEO strategies we implemented**, with **references to authoritative sources** and **pointers to our repository** for screenshots of the actual code.

---

## 1. System overview

The application is organized as a typical Django multi-app project. The **`shopping`** app exposes the public storefront: home page, product listing with search and category filters, product detail with configurable variants (SKUs), shopping cart, checkout (wallet-based payment in the project’s domain model), and customer order history. The **`user`** app handles authentication, profiles, shipping addresses, and wallet transactions. The **`vendor`** app allows users in a *Vendor* group (or staff) to create and edit products, manage property dimensions and SKU rows, process orders, and view **sales reports** (KPIs, time series, top products). The **`OnlineShoppingSys`** package holds global settings (including optional SQLite for local development, MySQL via `db.cnf` for team deployments, security headers, and cookie policies), URL routing (including `sitemap.xml` and `robots.txt`), middleware, and shared mixins.

From an implementation standpoint, SEO is not a separate “mini-app”; it **cross-cuts** the data model (`Product.slug`), URL routing (slug-based detail URLs and legacy redirects), views (canonical URLs, JSON-LD construction), templates (`<meta>`, Open Graph, `noindex` on transactional pages), and discovery files (`sitemap`, `robots.txt`). That integration is intentional: search-related behavior stays aligned with how real products are identified and linked across the site.

Beyond SEO, the project implements a **wallet-based checkout** (orders split per vendor line in the checkout flow), **SKU-driven** variant selection with stock checks, **vendor** tooling for inventory and optional **sales analytics** (period KPIs, charts, top products, excluding cancelled orders), and **defense-in-depth** configuration (for example: HTTPS-oriented cookie flags when `DEBUG` is off, strict framing, `json_script` for embedding JSON in HTML to reduce XSS risk, CSRF protection via Django middleware, and role-based access for vendor-only views). Those concerns shaped settings and templates as much as SEO did: for instance, security choices affect how third-party scripts (charts, UI libraries) are loaded, while analytics require consistent **order line** semantics so revenue totals match what vendors see in their dashboards. The present document, however, focuses on **search visibility and crawl hygiene** as required by the coursework SEO block.

---

## 2. SEO strategies we implemented

### 2.1 Search-friendly URLs and URL consolidation (301 redirects)

**Strategy:** Use **human-readable, keyword-bearing URLs** for product detail pages instead of opaque numeric paths only, and **consolidate** duplicate entry points so search engines treat one URL as canonical.

**Our implementation:** Each `Product` has a **unique `slug`** derived from the product name (with collision handling and a guard for numeric-only slugs). The model assigns a slug before save when missing, and `get_absolute_url()` resolves the storefront detail route by `slug`:

```27:105:d:\CodingProjects\OnlineShoppingSystem\shopping\models.py
class Product(models.Model):
    """Product model (Block A)"""
    # System-generated unique product ID (A15)
    product_id = models.CharField(max_length=50, unique=True, editable=False)
    
    # Basic information (A3, A6, A16)
    name = models.CharField(max_length=200)
    # SEO / Block Y: search-friendly URL segment (unique, auto-filled from name)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    # ... price, thumbnail, description, category, is_active, created_by, timestamps ...

    def _make_unique_slug(self) -> str:
        base = slugify(self.name)[:200] or 'product'
        if base.isdigit():
            base = f'item-{base}'
        candidate = base
        n = 0
        while Product.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            n += 1
            candidate = f'{base}-{n}'
        return candidate

    def save(self, *args, **kwargs):
        """Auto-generate unique product ID and URL slug when missing."""
        # ... product_id generation ...
        if not self.slug:
            self.slug = self._make_unique_slug()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shopping:product_detail', kwargs={'slug': self.slug})
```

Routing uses **`/products/<slug>/`** as the primary detail endpoint. Legacy **`/products/<int:pk>/`** URLs issue an **HTTP 301 Permanent Redirect** to the slug URL so old bookmarks and external links do not fragment ranking signals across two URLs:

```10:14:d:\CodingProjects\OnlineShoppingSystem\shopping\urls.py
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', product_detail_pk_redirect, name='product_detail_legacy'),
    path('products/<slug:slug>/', ProductDetailPageView.as_view(), name='product_detail'),
```

```70:75:d:\CodingProjects\OnlineShoppingSystem\shopping\views.py
def product_detail_pk_redirect(request, pk):
    """301 from legacy /products/<pk>/ URLs to canonical slug URLs (Block Y SEO)."""
    product = get_object_or_404(Product.objects.only('slug', 'pk'), pk=pk)
    return HttpResponsePermanentRedirect(
        reverse('shopping:product_detail', kwargs={'slug': product.slug})
    )
```

**Authoritative background:** Google’s documentation discusses **consolidation of duplicate URLs** and the use of **redirects** and **canonicalization** to help search engines understand the preferred version of a page (see Google Search Central, *“Consolidate duplicate URLs”*). Our301 redirect implements that pattern for the legacy ID-based path.

**Design impact:** Adding `slug` required a **database migration** and updating **every template and redirect** that previously built `product_detail` links with a primary key. We deliberately **do not auto-rewrite slugs on every name change** after creation (stable URLs reduce broken inbound links); slug stability is a product/SEO trade-off documented in `docs/SEO.md`.

---

### 2.2 Canonical URLs, page metadata, and Open Graph

**Strategy:** Provide a **canonical link** for product pages, rich **title/description** metadata, and **Open Graph** tags for better snippet control when URLs are shared.

**Our implementation:** The product detail view computes an **absolute canonical URL** and an **absolute image URL** for the thumbnail; the template emits `rel="canonical"`, standard meta tags, `og:title`, `og:description`, and conditional `og:image`. **JSON-LD** (next subsection) is emitted in the same `meta` block:

```150:196:d:\CodingProjects\OnlineShoppingSystem\shopping\views.py
        request = self.request
        canonical = request.build_absolute_uri(product.get_absolute_url())
        context['canonical_url'] = canonical
        if product.thumbnail:
            context['og_image_url'] = request.build_absolute_uri(product.thumbnail.url)
        else:
            context['og_image_url'] = ''
        # ... image list and availability logic ...
        ld = {
            '@context': 'https://schema.org',
            '@type': 'Product',
            'name': product.name,
            'description': (product.description or '')[:5000],
            'sku': product.product_id,
            'url': canonical,
            'offers': {
                '@type': 'Offer',
                'url': canonical,
                'priceCurrency': 'USD',
                'price': str(product.price),
                'availability': avail_url,
            },
        }
        # ... image field ...
        context['product_ld_json'] = json.dumps(ld, ensure_ascii=False)
        return context
```

```6:16:d:\CodingProjects\OnlineShoppingSystem\templates\store\product_detail.html
{% block meta %}
    <meta name="description" content="{{ product.description }}">
    <meta name="keywords" content="MPU, ISP, {{ product.name }}, online store">
    <link rel="canonical" href="{{ canonical_url }}">
    <meta property="og:title" content="Product|{{ product.name }} - Online Store">
    <meta property="og:description" content="{{ product.description }}">
    {% if og_image_url %}
    <meta property="og:image" content="{{ og_image_url }}">
    {% endif %}
    <script type="application/ld+json">{{ product_ld_json|safe }}</script>
{% endblock %}
```

The base layout sets a default **`og:url`** pattern for all pages:

```7:12:d:\CodingProjects\OnlineShoppingSystem\templates\base.html
    <title>{% block title %}Online Store{% endblock %}</title>

    {% block meta %}{% endblock %}
    <meta name="author" content="MPU ISP Group25">

    <meta property="og:url" content="https://{{ request.META.HTTP_HOST }}{{ request.path }}">
```

**Authoritative background:** Google describes **`link rel="canonical"`** as a way to indicate a canonical URL when duplicate or near-duplicate content exists (Google Search Central, *“How to specify a canonical with rel='canonical' and other methods”*). Open Graph tags are specified by the **Open Graph protocol** (ogp.me) and are widely used by social platforms to build link previews.

**Design impact:** SEO metadata is **centralized in templates** but **fed by the view** where we already have resolved product, stock, and absolute URIs—avoiding duplicated business logic in the front end. We accept that **`meta description` may be long** if the product description is long; production systems sometimes truncate for snippet length, but the pattern is correct for coursework and can be refined later.

---

### 2.3 Structured data (JSON-LD / Schema.org `Product`)

**Strategy:** Expose **structured data** so crawlers can interpret entities (product name, offer, price, availability, images) reliably.

**Our implementation:** The same `ProductDetailPageView` builds a **JSON-LD** graph with `@context` `https://schema.org`, `@type` `Product`, nested `Offer`, and optional `image` list, then the template embeds it as `application/ld+json` (see citations in §2.2).

**Authoritative background:** Google documents **Product** structured data requirements and recommendations in *“Product structured data”* (Google Search Central). Schema.org defines the **Product** and **Offer** types (schema.org/Product, schema.org/Offer).

**Design impact:** Availability is derived from **real catalog rules** in code (inactive product → `Discontinued`; configurable products → any in-stock SKU; simple products → default SKU stock). That ties SEO honesty to **inventory logic**, which is good for trust but means the view must import **`ProductSKU`** and remain in sync with storefront purchase rules.

---

### 2.4 XML sitemaps and robots.txt

**Strategy:** Publish a **sitemap** of important URLs and a **robots.txt** that blocks irrelevant areas (e.g., admin) and points crawlers to the sitemap.

**Our implementation:** Django’s **contrib sitemaps** are registered at the project URL level; product entries are limited to **active** products, expose **`lastmod`**, and use **`get_absolute_url()`** (slug-based):

```33:39:d:\CodingProjects\OnlineShoppingSystem\OnlineShoppingSys\urls.py
urlpatterns = [
    path('sitemap.xml/', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt/', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('admin/', admin.site.urls),
```

```6:29:d:\CodingProjects\OnlineShoppingSystem\shopping\sitemaps.py
class HomeSitemap(Sitemap):
    changefreq = 'daily'
    priority = 1.0
    # ...

class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
```

```1:4:d:\CodingProjects\OnlineShoppingSystem\templates\robots.txt
User-agent: *
Disallow: /admin/

Sitemap: {{ request.scheme }}://{{ request.get_host }}/sitemap.xml/
```

**Authoritative background:** Google explains the role of **sitemaps** in discovery (*“Learn about sitemaps”*, Google Search Central) and how **robots.txt** can control crawling (*“How Google interprets the robots.txt specification”*). Django documents the **Sitemap framework** in its official documentation (*Django: The sitemap framework*).

**Design impact:** Sitemap composition **filters inactive products**, aligning public SEO surfaces with what customers should discover. Using **`lastmod`** ties refresh signals to `Product.updated_at` (implementation choice).

---

### 2.5 Crawl budget and index hygiene (`noindex` on transactional flows)

**Strategy:** Reduce low-value or session-like pages in the index (cart, checkout, private order views) so crawlers emphasize commercial landing pages.

**Our implementation:** Cart, checkout, and order templates define `meta robots` as `noindex, nofollow` (see e.g. `templates/store/cart.html`, `checkout.html`, `order_list.html`, `order_detail.html` in the repository).

**Authoritative background:** Google documents **`noindex`** as a directive to prevent indexing (*“Block search indexing with 'noindex'”*, Google Search Central).

**Design impact:** This is a **product decision**: we trade possible accidental indexing of cart URLs for cleaner search results. It must stay consistent with **authentication** (these routes are largely login-gated anyway).

---

### 2.6 Semantic HTML headings (supporting content structure)

**Strategy:** Use **headings** to reflect document structure (one clear topic per product page).

**Our implementation:** Product detail uses **`h1`** for the product name and **`h3`** for sections such as description and details (see `templates/store/product_detail.html` body). Listing pages use **`h2`/`h3`** hierarchies.

**Authoritative background:** Google’s SEO Starter Guide discusses **helping Google understand pages** with clear structure and meaningful text (Google Search Central, *SEO Starter Guide*).

**Design impact:** Heading choices influenced **template layout** rather than backend schema, but they must remain consistent as new blocks (e.g., related products) are added.

---

## 3. How SEO affected overall system design

1. **Data model:** `Product.slug` is a first-class field with **uniqueness** and **indexing**, not a computed-only string in templates—so URLs remain stable in the database and across environments.
2. **Routing:** We maintain **two patterns** for products (legacy numeric redirect + slug detail) to preserve compatibility while adopting SEO-friendly URLs.
3. **View layer:** Product detail view carries **additional responsibilities** (canonical, OG image absolutization, JSON-LD), increasing context-building complexity but keeping SEO aligned with **stock and activation** rules.
4. **Cross-cutting links:** Many templates and vendor analytics links were updated to pass **`slug`** into `{% url 'shopping:product_detail' ... %}`—SEO therefore touched **vendor reporting** and **customer order line links**, not only the storefront.
5. **Operations:** Migrations and documentation (`docs/SEO.md`) became part of the deliverable so teammates understand **why slugs are stable** and **what files participate in SEO**.
6. **Testing and local setup:** Because slugs are **database-backed**, any fixture, seed command, or test that creates `Product` rows must run migrations; automated tests benefit from calling `save()` so slug population rules execute the same way as in production.

Finally, SEO improvements are **not a substitute** for performance, mobile usability, trustworthy content, or authoritative backlinks; they are **technical enablers** that help crawlers and social platforms interpret the storefront correctly. Within the scope of this assignment, we prioritized **standards-based, auditable** mechanisms (canonical tags, structured data, sitemaps, robots rules) that graders can verify directly in HTML and in Python.

---

## 4. References (for bibliography / screenshots)

### 4.1 External authoritative sources

1. Google Search Central — *Consolidate duplicate URLs*:  
   https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls  
2. Google Search Central — *Canonicalization*:  
   https://developers.google.com/search/docs/crawling-indexing/canonicalization  
3. Google Search Central — *Product structured data*:  
   https://developers.google.com/search/docs/appearance/structured-data/product  
4. Google Search Central — *Learn about sitemaps*:  
   https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview  
5. Google Search Central — *Robots.txt introduction*:  
   https://developers.google.com/search/docs/crawling-indexing/robots/intro  
6. Google Search Central — *Block indexing with noindex*:  
   https://developers.google.com/search/docs/crawling-indexing/block-indexing  
7. Google Search Central — *SEO Starter Guide*:  
   https://developers.google.com/search/docs/fundamentals/seo-starter-guide  
8. Schema.org — *Product*: https://schema.org/Product  
9. Schema.org — *Offer*: https://schema.org/Offer  
10. Open Graph protocol: https://ogp.me/  
11. Django — *The sitemap framework*:  
    https://docs.djangoproject.com/en/stable/ref/contrib/sitemaps/

### 4.2 In-repository sources (screenshot targets)

| Topic | File paths (project root) |
|------|---------------------------|
| `Product.slug`, slug generation, `get_absolute_url` | `shopping/models.py` |
| Legacy 301 redirect + slug `DetailView` + JSON-LD context | `shopping/views.py` |
| URL patterns | `shopping/urls.py` |
| Sitemap classes | `shopping/sitemaps.py` |
| Sitemap + robots routes | `OnlineShoppingSys/urls.py` |
| Product meta + canonical + OG + JSON-LD in HTML | `templates/store/product_detail.html` |
| Global `og:url` | `templates/base.html` |
| `robots.txt` template | `templates/robots.txt` |
| Written design notes | `docs/SEO.md` |

---

*This file is intended for coursework submission: open it in the editor for the narrative, and use the cited repository paths for code screenshots.*
