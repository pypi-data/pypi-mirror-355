from typing import Optional

import httpx
import rich



def get_organization_personnel(
    organization_id: str, base_url: str = "http://localhost:8000"
) -> Optional[dict]:
    """Get organization data with focus on personnel/memberships via REST API.

    Args:
        organization_id: The organization ID to fetch
        base_url: Base URL of the local API server

    Returns:
        Combined organization and membership data or None if request fails
    """
    with httpx.Client(follow_redirects=True) as client:
        try:
            # Fetch organization details
            org_response = client.get(
                f"{base_url}/organizations/",
                params={"id": organization_id},
                timeout=30,
                follow_redirects=True,
            )
            org_response.raise_for_status()
            org_data = org_response.json()

            # Fetch memberships for this organization by traversing through membership_ref[]
            memberships = []
            for membership_ref in org_data.get("membership_ref", []):
                # extract membership id from the reference
                membership_id = httpx.URL(membership_ref).params.get("id")
                if membership_id:
                    membership_response = client.get(
                        f"{base_url}/memberships",
                        params={"id": membership_id},
                        timeout=30,
                        follow_redirects=True,
                    )
                    membership_response.raise_for_status()
                    membership = membership_response.json()
                    memberships.append(membership)

            # Combine the data with focus on personnel
            result = {
                "organization": org_data,
                "personnel": {
                    "total_members": len(memberships),
                    "memberships": memberships,
                },
            }

            return result

        except httpx.RequestError as e:
            rich.print(f"[red]Failed to fetch data from API: {e}[/red]")
            return None
        except Exception as e:
            rich.print(f"[red]Error processing data: {e}[/red]")
            return None


def main():
    """Get and print organization data with personnel focus from the local OParl API."""
    # Example organization ID - in practice this would be passed as argument
    organization_id = "20"  # Example ID

    # Fetch organization with personnel data
    # display a progress bar
    rich.print(
        "[bold blue]Fetching organization data with personnel focus...[/bold blue]"
    )
    rich.print(f"[bold]Organization ID:[/bold] {organization_id}")
    # use rich's track to show progress
    data = get_organization_personnel(organization_id)

    if data:
        rich.print("[bold green]Organization Summary with Personnel Focus[/bold green]")
        rich.print(
            f"[bold]Organization:[/bold] {data['organization'].get('name', 'Unknown')}"
        )
        rich.print(f"[bold]Total Members:[/bold] {data['personnel']['total_members']}")
        rich.print("\n[bold]Personnel Details:[/bold]")

        for i, membership in enumerate(
            data["personnel"]["memberships"][:5], 1
        ):  # Show first 5
            rich.print(f"  {i}. Membership ID: {membership.get('id', 'Unknown')}")
            if membership.get("person_ref"):
                rich.print(f"     Person Reference: {membership['person_ref']}")
            if membership.get("role"):
                rich.print(f"     Role: {membership['role']}")
            if membership.get("start_date"):
                rich.print(f"     Start Date: {membership['start_date']}")
            if membership.get("end_date"):
                rich.print(f"     End Date: {membership['end_date']}")
            rich.print("")  # Empty line for readability
    else:
        rich.print("[red]Failed to fetch organization data[/red]")


if __name__ == "__main__":

    main()
