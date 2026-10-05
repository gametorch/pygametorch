"""Creates a project-scoped **read-only** key and a project-scoped **write**
key using an admin API key, setting each key's name, spend limit, reset cadence
and expiry date.

This must be run with an **admin** API key (``GAMETORCH_API_KEY``). It does not
spend credits. It cleans up after itself by revoking the keys and deleting the
temporary project unless ``GAMETORCH_KEEP_KEYS=1`` is set.

Run with::

    GAMETORCH_API_KEY=gt2_admin_... python examples/create_project_keys.py
"""

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from gametorch import Client, CreateApiKeyRequest, SpendResetCadence, UpdateApiKeyRequest


def print_key(kind: str, created) -> None:
    key = created.key
    print(
        f"created {kind} key: scope={key.key_scope} project={key.project_id} "
        f"limit={key.max_spend_limit} cadence={key.spend_reset_cadence} "
        f"expires_at={key.expires_at}"
    )
    print(f"  key_full (store securely, shown once): {created.key_full}")


def main() -> None:
    with Client.from_env() as client:
        project = client.create_project(f"SDK Keys Example {uuid4().hex[:8]}")
        print(f"created project '{project.name}' ({project.slug})")

        expires_at = datetime.now(UTC) + timedelta(days=30)

        read = client.create_key(
            CreateApiKeyRequest.project_read(project.id)
            .name("Read-only CI key")
            .max_spend_limit(Decimal(0))
            .spend_reset_cadence(SpendResetCadence.MONTHLY)
            .expires_at(expires_at)
        )
        print_key("read-only", read)

        write = client.create_key(
            CreateApiKeyRequest.project_write(project.id)
            .name("Write CI key")
            .max_spend_limit(Decimal(500))
            .spend_reset_cadence(SpendResetCadence.WEEKLY)
            .expires_at(expires_at)
        )
        print_key("write", write)

        updated = client.update_key(
            write.key.id,
            UpdateApiKeyRequest.new()
            .name("Write CI key (renamed)")
            .max_spend_limit(Decimal(750))
            .spend_reset_cadence(SpendResetCadence.MONTHLY)
            .expires_at(expires_at + timedelta(days=30)),
        )
        print(
            f"updated write key: name={updated.name!r} limit={updated.max_spend_limit} "
            f"cadence={updated.spend_reset_cadence} expires_at={updated.expires_at}"
        )

        print("\nall keys:")
        for key in client.list_keys().keys:
            print(
                f"  {key.name or '<unnamed>':<24} scope={key.key_scope} "
                f"project={key.project_id} limit={key.max_spend_limit} "
                f"cadence={key.spend_reset_cadence} prefix={key.key_prefix}"
            )

        if os.environ.get("GAMETORCH_KEEP_KEYS") == "1":
            print("\nkeeping keys and project (GAMETORCH_KEEP_KEYS=1)")
            print(f"  read key:  {read.key_full}")
            print(f"  write key: {write.key_full}")
        else:
            client.delete_key(read.key.id)
            client.delete_key(write.key.id)
            client.delete_project(project.slug)
            print("\nrevoked keys and deleted project")


if __name__ == "__main__":
    main()
