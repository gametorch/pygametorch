"""Streams every generation in a project, page by page.

Run with::

    GAMETORCH_API_KEY=gt2_... GAMETORCH_PROJECT=<project-uuid> \
        python examples/stream_generations.py
"""

import os
from uuid import UUID

from gametorch import Client


def main() -> None:
    project = UUID(os.environ["GAMETORCH_PROJECT"])

    with Client.from_env() as client:
        stream = client.stream_generations(project)
        count = 0
        for generation in stream:
            count += 1
            print(f"{generation.id}  {generation.status}  {len(generation.assets)} asset(s)")
        print(f"streamed {count} generation(s), total={stream.total}")


if __name__ == "__main__":
    main()
