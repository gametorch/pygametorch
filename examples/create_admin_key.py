"""Creates an **admin** API key using an existing admin key, setting its name,
spend limit, reset cadence and expiry date.

This must be run with an **admin** API key (``GAMETORCH_API_KEY``). It does not
spend credits. It revokes the key it creates at the end unless
``GAMETORCH_KEEP_KEYS=1`` is set.

Run with::

    GAMETORCH_API_KEY=gt2_admin_... python examples/create_admin_key.py
"""

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from gametorch import Client, CreateApiKeyRequest, SpendResetCadence, UpdateApiKeyRequest


def main() -> None:
    with Client.from_env() as client:
        created = client.create_key(
            CreateApiKeyRequest.admin()
            .name("Admin CI key")
            .max_spend_limit(Decimal(5000))
            .spend_reset_cadence(SpendResetCadence.MONTHLY)
            .expires_at(datetime.now(UTC) + timedelta(days=90))
        )
        print(
            f"created admin key: name={created.key.name!r} scope={created.key.key_scope} "
            f"limit={created.key.max_spend_limit} cadence={created.key.spend_reset_cadence} "
            f"expires_at={created.key.expires_at}"
        )
        # Shown only once, at creation time. Treat it like a password.
        print(f"key_full (store securely, shown once): {created.key_full}")

        updated = client.update_key(
            created.key.id,
            UpdateApiKeyRequest.new()
            .name("Admin CI key (renamed)")
            .max_spend_limit(Decimal(7500))
            .expires_at(datetime.now(UTC) + timedelta(days=180)),
        )
        print(
            f"updated: name={updated.name!r} limit={updated.max_spend_limit} "
            f"expires_at={updated.expires_at}"
        )

        if os.environ.get("GAMETORCH_KEEP_KEYS") == "1":
            print(f"keeping key (GAMETORCH_KEEP_KEYS=1): {created.key_full}")
        else:
            client.delete_key(created.key.id)
            print("revoked admin key")


if __name__ == "__main__":
    main()
