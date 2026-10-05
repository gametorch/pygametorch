"""Lists the projects in the caller's scope.

Run with::

    export GAMETORCH_API_KEY=gt2_...
    python examples/list_projects.py
    # against a local deployment:
    GAMETORCH_BASE_URL=http://localhost:8300/api python examples/list_projects.py
"""

from gametorch import Client


def main() -> None:
    with Client.from_env() as client:
        for project in client.list_projects().projects:
            print(f"{project.id}  {project.name}  ({project.slug})")


if __name__ == "__main__":
    main()
