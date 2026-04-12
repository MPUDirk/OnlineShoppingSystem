# Block Y — Search engine optimization (implementation notes)

This document describes what we implemented and how it fits the storefront design.

## Search-friendly URLs

- Public product pages use **`/products/<slug>/`**, where `slug` is derived from the product name (`django.utils.text.slugify`), made unique with numeric suffixes when needed.
- **Legacy `/products/<id>/` URLs return HTTP 301** to the canonical slug URL so bookmarks and old links keep working and search engines consolidate signals on one URL.

## Meta tags and social previews

- **`<title>`** and **`meta description` / `keywords`** on the home page, product list, product detail, login, signup, and cart/checkout/order flows.
- **Open Graph** (`og:title`, `og:description`, `og:url` in `base.html`; **`og:image`** on product detail when a thumbnail exists).
- **`<link rel="canonical">`** on product detail pointing to the slug URL (avoids duplicate-content issues when parameters are added).
- **Cart, checkout, and order pages** use **`noindex, nofollow`** so transactional/private flows are less prominent in search results.

## Heading structure

- Home: banner **`h1`**; sections use **`h2`/`h3`** as before.
- Product list: **`h2`** for major sections, **`h3`** for card titles.
- Product detail: product name is **`h1`**; sections use **`h3`**.

## Structured data (JSON-LD)

- Product pages include **`application/ld+json`** with **Schema.org `Product`** and nested**`Offer`** (price, `USD`, availability from stock / active state, URL, SKU, images).
- Built server-side in `ProductDetailPageView` and embedded safely in the template with `|safe` after `json.dumps` (content is JSON-encoded, not raw HTML).

## Crawlability

- **`/sitemap.xml/`** lists the home route, login/signup (user sitemap), and **active products only**, with **`lastmod`** from `Product.updated_at`, **`changefreq`**, and **`priority`** hints.
- **`robots.txt`** disallows `/admin/` and advertises the **Sitemap** URL with the current host.

## Design trade-offs

- **Stable slugs:** Changing the product name does not automatically change the slug (after first save), to avoid breaking external links; new products get slugs from the current name.
- **Database:** MySQL/SQLite both supported; slug is indexed and unique at the DB level.
