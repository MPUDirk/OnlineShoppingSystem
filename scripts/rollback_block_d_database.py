"""
One-off rollback: reverse Block D schema (migrations 0008/0009) on MySQL.

Note: MySQL commits DDL implicitly; do not rely on a single DB transaction.

Run:  python scripts/rollback_block_d_database.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OnlineShoppingSys.settings")

import django

django.setup()

from collections import defaultdict
from django.db import connection
from django.db.utils import OperationalError


def _table_exists(cursor, name):
    cursor.execute(
        """
        SELECT 1 FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        """,
        [name],
    )
    return cursor.fetchone() is not None


def _column_exists(cursor, table, column):
    cursor.execute(
        """
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        [table, column],
    )
    return cursor.fetchone() is not None


def _drop_fk_matching(cursor, table, name_substr):
    cursor.execute(
        """
        SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        AND CONSTRAINT_TYPE = 'FOREIGN KEY' AND CONSTRAINT_NAME LIKE %s
        """,
        [table, f"%{name_substr}%"],
    )
    for (name,) in cursor.fetchall():
        cursor.execute(f"ALTER TABLE `{table}` DROP FOREIGN KEY `{name}`")


def _drop_indexes_matching(cursor, table, substr):
    cursor.execute(f"SHOW INDEX FROM `{table}`")
    seen = set()
    for row in cursor.fetchall():
        key_name = row[2]
        if key_name == "PRIMARY" or key_name in seen:
            continue
        if substr in key_name:
            seen.add(key_name)
            try:
                cursor.execute(f"ALTER TABLE `{table}` DROP INDEX `{key_name}`")
            except OperationalError:
                pass


def _constraint_exists(cursor, table, name):
    cursor.execute(
        """
        SELECT 1 FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND CONSTRAINT_NAME = %s
        """,
        [table, name],
    )
    return cursor.fetchone() is not None


def _build_cart_merge(cursor):
    merged = defaultdict(int)
    if _column_exists(cursor, "shopping_cartitem", "product_sku_id") and _table_exists(
        cursor, "shopping_productsku"
    ):
        cursor.execute(
            """
            SELECT ci.cart_id, ci.quantity, ps.product_id
            FROM shopping_cartitem ci
            INNER JOIN shopping_productsku ps ON ci.product_sku_id = ps.id
            """
        )
        for cart_id, qty, product_id in cursor.fetchall():
            merged[(cart_id, product_id)] += int(qty)
        return merged

    if _column_exists(cursor, "shopping_cartitem", "product_id"):
        cursor.execute(
            """
            SELECT cart_id, product_id, quantity FROM shopping_cartitem
            WHERE product_id IS NOT NULL
            """
        )
        for cart_id, product_id, qty in cursor.fetchall():
            merged[(cart_id, product_id)] += int(qty)
        return merged

    cursor.execute("SELECT COUNT(*) FROM shopping_cartitem")
    n = cursor.fetchone()[0]
    if n:
        print(
            f"WARNING: Clearing {n} cart row(s) with no product link "
            "(SKU column already removed; cannot restore line items)."
        )
    return merged


def main():
    with connection.cursor() as c:
        c.execute(
            """
            SELECT name FROM django_migrations
            WHERE app = 'shopping' AND name IN ('0008_block_d_sku', '0009_cartitem_product_sku_data')
            """
        )
        pending = [r[0] for r in c.fetchall()]

    if not pending:
        print("No Block D migrations in django_migrations; nothing to do.")
        return

    print("Rolling back:", pending)

    with connection.cursor() as c:
        merged = _build_cart_merge(c)

        _drop_fk_matching(c, "shopping_orderitem", "product_sku")
        for col in ("product_sku_id", "configuration_label", "sku_code"):
            if _column_exists(c, "shopping_orderitem", col):
                c.execute(f"ALTER TABLE shopping_orderitem DROP COLUMN `{col}`")

        _drop_fk_matching(c, "shopping_cartitem", "product_sku")
        _drop_indexes_matching(c, "shopping_cartitem", "product_sku")
        if _column_exists(c, "shopping_cartitem", "product_sku_id"):
            c.execute("ALTER TABLE shopping_cartitem DROP COLUMN product_sku_id")

        if _column_exists(c, "shopping_cartitem", "product_id"):
            _drop_fk_matching(c, "shopping_cartitem", "product_id")
            _drop_indexes_matching(c, "shopping_cartitem", "product_id")
            c.execute("ALTER TABLE shopping_cartitem DROP COLUMN product_id")

        if not _column_exists(c, "shopping_cartitem", "product_id"):
            c.execute("ALTER TABLE shopping_cartitem ADD COLUMN product_id BIGINT NULL")

        c.execute("DELETE FROM shopping_cartitem")
        for (cart_id, product_id), qty in merged.items():
            c.execute(
                """
                INSERT INTO shopping_cartitem
                (cart_id, product_id, quantity, added_at, updated_at)
                VALUES (%s, %s, %s, NOW(6), NOW(6))
                """,
                [cart_id, product_id, qty],
            )

        c.execute(
            "ALTER TABLE shopping_cartitem MODIFY COLUMN product_id BIGINT NOT NULL"
        )

        if not _constraint_exists(c, "shopping_cartitem", "shopping_cartitem_cart_id_product_id_uniq"):
            c.execute(
                """
                ALTER TABLE shopping_cartitem
                ADD CONSTRAINT shopping_cartitem_cart_id_product_id_uniq
                UNIQUE (cart_id, product_id)
                """
            )
        if not _constraint_exists(c, "shopping_cartitem", "shopping_cartitem_product_id_fk"):
            c.execute(
                """
                ALTER TABLE shopping_cartitem
                ADD CONSTRAINT shopping_cartitem_product_id_fk
                FOREIGN KEY (product_id) REFERENCES shopping_product (id)
                """
            )

        if _column_exists(c, "shopping_product", "is_configurable"):
            c.execute("ALTER TABLE shopping_product DROP COLUMN is_configurable")

        c.execute("SET FOREIGN_KEY_CHECKS = 0")
        for t in (
            "shopping_skuoptionvalue",
            "shopping_productsku",
            "shopping_productoptionvalue",
            "shopping_productoption",
        ):
            if _table_exists(c, t):
                c.execute(f"DROP TABLE `{t}`")
        c.execute("SET FOREIGN_KEY_CHECKS = 1")

        c.execute(
            """
            DELETE FROM django_migrations
            WHERE app = 'shopping' AND name IN ('0008_block_d_sku', '0009_cartitem_product_sku_data')
            """
        )

    print("Rollback finished. `python manage.py showmigrations shopping` should end at 0007.")


if __name__ == "__main__":
    main()
