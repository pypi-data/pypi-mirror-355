# Check References CLI Command

## Overview

The `check references` command allows you to inspect the reference resolution status for entities stored in ChromaDB. This is useful for debugging and monitoring the reference population system.

## Usage

```bash
# Check reference status for a consultation
uv run oparl check check-references Consultation <entity-id>

# Check reference status for a meeting
uv run oparl check check-references Meeting <entity-id>

# Check reference status for a paper
uv run oparl check check-references Paper <entity-id>
```

## Command Structure

The command follows the pattern:
```
oparl check check-references <ENTITY_TYPE> <ENTITY_ID>
```

Where:
- `ENTITY_TYPE`: The type of entity (Consultation, Meeting, Paper, Person, Organization)
- `ENTITY_ID`: The unique identifier of the entity in ChromaDB

## Output Format

The command provides two types of information:

### 1. Reference Resolution Status
Shows which reference fields have been resolved:

```
📊 Reference Status for Consultation abc-123:
--------------------------------------------------
✅ paper: Resolved
⏳ meeting: Pending
✅ organizations: Resolved
```

### 2. Entity Details
Shows current state of the entity with resolved/unresolved references:

```
📄 Entity Details:
  Paper: Beschlussvorlage zum Klimaschutz
  Meeting Reference: https://www.bonn.sitzung-online.de/public/oparl/meetings?id=2004507
  ⏳ Full meeting data loading in background...
```

## Examples

### Check a Consultation
```bash
uv run oparl check check-references Consultation "550e8400-e29b-41d4-a716-446655440000"
```

### Check a Meeting
```bash
uv run oparl check check-references Meeting "550e8400-e29b-41d4-a716-446655440001"
```

## Interpreting Results

### Status Icons
- ✅ **Resolved**: The reference has been successfully populated with the full object
- ⏳ **Pending**: The reference exists but hasn't been resolved yet (background task may be running)

### Entity Details
- **Resolved references**: Show actual object data (names, dates, etc.)
- **Unresolved references**: Show the reference URL and indicate background loading

## Troubleshooting

### Command Not Found
If you get "command not found", ensure you're in the project directory and using `uv run`.

### Entity Not Found
If the entity ID doesn't exist, you'll get an empty status. Check that:
1. The entity ID is correct
2. The entity type matches the actual entity
3. The entity exists in ChromaDB

### No Reference Data
If all references show as "Pending":
1. Check if the reference resolution system is running
2. Verify Celery workers are active
3. Check if there are any errors in the logs

## Integration with Reference Resolution System

This command is part of the larger reference resolution architecture:

1. **Background Tasks**: Celery tasks automatically resolve references
2. **ChromaDB Storage**: Resolved references are stored alongside entities
3. **CLI Monitoring**: This command provides visibility into the process

## Related Commands

- `oparl meeting get <id>`: Get meeting details with resolved references
- `oparl consultation get <id>`: Get consultation details (when implemented)
- Celery monitoring commands for checking task status

## Technical Details

The command uses:
- `ReferenceResolver.check_references_resolved()`: To check resolution status
- `ReferenceResolver.get_or_resolve_entity()`: To get current entity state
- ChromaDB multi-collection architecture for entity storage