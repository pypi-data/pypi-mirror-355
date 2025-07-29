import cyclopts
import httpx
import rich
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

from stadt_bonn_oparl.chromadb_utils import get_chromadb_manager
from stadt_bonn_oparl.reference_resolver import (
    ReferenceResolver,
    ResolverCantFindEntiry,
)

checker = cyclopts.App(name="check", help="check reference resolution status")


@checker.command
async def references(entity_type: str, entity_id: str):
    """Check the reference resolution status for an entity."""

    http_client = httpx.Client()
    chromadb_manager = get_chromadb_manager()
    resolver = ReferenceResolver(http_client, chromadb_manager.client)

    # Check status
    try:
        status = await resolver.check_references_resolved(entity_id, entity_type)
    except ResolverCantFindEntiry as exc:
        error_panel = Panel(
            f"[red]❌ Entity not found[/red]\n\n"
            f"[bold]Entity Type:[/bold] {entity_type}\n"
            f"[bold]Entity ID:[/bold] {entity_id}\n\n"
            f"[yellow]Possible reasons:[/yellow]\n"
            f"• Entity ID is incorrect\n"
            f"• Entity hasn't been indexed yet\n"
            f"• Wrong entity type specified",
            title="⚠️  Entity Not Found",
            border_style="red",
        )
        console.print(error_panel)
        return
    except Exception as e:
        error_panel = Panel(
            f"[red]❌ Error checking references[/red]\n\n"
            f"[yellow]Error details:[/yellow] {str(e)}",
            title="💥 Unexpected Error",
            border_style="red",
        )
        console.print(error_panel)
        return

    # Create a rich table for reference status
    table = Table(title=f"📊 Reference Status for {entity_type} {entity_id}")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("State", justify="center")

    for field, is_resolved in status.items():
        icon = "✅" if is_resolved else "⏳"
        status_text = (
            "[green]Resolved[/green]" if is_resolved else "[yellow]Pending[/yellow]"
        )
        table.add_row(field, status_text, icon)

    console.print(table)

    # Get the entity to show current state
    entity = await resolver.get_or_resolve_entity(entity_type, entity_id)
    if entity:
        # Create a panel for entity details
        details_content = []

        # Add general entity info
        details_content.append(f"[bold]Entity ID:[/bold] {entity.get('id', 'N/A')}")
        if entity.get("created"):
            details_content.append(f"[bold]Created:[/bold] {entity['created']}")

        # Show example fields based on type
        if entity_type.lower() == "consultation":
            if entity.get("paper"):
                details_content.append(
                    f"\n[green]📄 Paper:[/green] {entity['paper'].get('name', 'N/A')}"
                )
            else:
                details_content.append(
                    f"\n[yellow]📄 Paper Reference:[/yellow] {entity.get('paper_ref', 'N/A')}"
                )
                details_content.append(
                    "   [dim]⏳ Full paper data loading in background...[/dim]"
                )

            if entity.get("meeting"):
                details_content.append(
                    f"\n[green]📅 Meeting:[/green] {entity['meeting'].get('name', 'N/A')}"
                )
            else:
                details_content.append(
                    f"\n[yellow]📅 Meeting Reference:[/yellow] {entity.get('meeting_ref', 'N/A')}"
                )
                details_content.append(
                    "   [dim]⏳ Full meeting data loading in background...[/dim]"
                )

        elif entity_type.lower() == "meeting":
            if entity.get("organizations"):
                orgs = entity["organizations"]
                if isinstance(orgs, list):
                    details_content.append(
                        f"\n[green]🏢 Organizations:[/green] {len(orgs)} organizations resolved"
                    )
                    for org in orgs[:3]:  # Show first 3
                        details_content.append(f"   - {org.get('name', 'N/A')}")
                else:
                    details_content.append(
                        f"\n[green]🏢 Organization:[/green] {orgs.get('name', 'N/A')}"
                    )
            else:
                details_content.append(
                    f"\n[yellow]🏢 Organizations Reference:[/yellow] {entity.get('organizations_ref', 'N/A')}"
                )
                details_content.append(
                    "   [dim]⏳ Organization data loading in background...[/dim]"
                )

        elif entity_type.lower() == "paper":
            if entity.get("consultations"):
                consultations = entity["consultations"]
                if isinstance(consultations, list):
                    details_content.append(
                        f"\n[green]📋 Consultations:[/green] {len(consultations)} consultations resolved"
                    )
                else:
                    details_content.append(
                        f"\n[green]📋 Consultation:[/green] {consultations.get('role', 'N/A')}"
                    )
            else:
                details_content.append(
                    f"\n[yellow]📋 Consultations Reference:[/yellow] {entity.get('consultation_ref', 'N/A')}"
                )
                details_content.append(
                    "   [dim]⏳ Consultation data loading in background...[/dim]"
                )

        # Display the panel
        if details_content:
            details_panel = Panel(
                "\n".join(details_content),
                title="📄 Entity Details",
                border_style="blue",
            )
            console.print(details_panel)
