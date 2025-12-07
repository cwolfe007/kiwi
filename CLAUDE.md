# Kiwi Project Context & Tool Configuration

**Note**: This project uses [bd (beads)](https://github.com/steveyegge/beads) for issue tracking. Use `bd` commands instead of markdown TODOs. See AGENTS.md for workflow details.

## ⚠️ CRITICAL: Always Read the Plan and BD Issue First

**BEFORE starting any work, ALWAYS:**

1. **Read the detailed plan file:**

   ```bash
   cat /home/cwolfe/.claude/plans/adaptive-hatching-pine.md
   ```

2. **Check the active bd issue for current status:**

   ```bash
   bd show kiwi-qfn
   ```

**Why this matters:**

- The plan file contains complete implementation details, architecture decisions, and all constraints
- The bd issue tracks current status, what's complete, what's pending, and any blockers
- This prevents duplicate work and ensures consistency across implementation sessions
- Critical constraints and backwards compatibility requirements are documented there

---

## Primary Tool: bd (Beads Issue Tracker)

Use the bd tool instead of markdown for all new work. All plans, tasks, and context should be tracked in bd to prevent context loss during long-running implementation.

### BD Issue Management for Context Compaction

When working on large tasks that may require context compaction:

**Creating Issues:**

```bash
# Create a new issue with description
bd create "Title of work item" --description="Description of what needs to be done"

# Create issue with multiline description from file
bd create "Title" << 'EOF'
- Point 1
- Point 2
EOF
```

**Adding Comments (Detailed Context):**

```bash
# Add a comment to an issue (pass text as second argument)
bd comment ISSUE_ID "Your comment text here"

# For multiline comments, use quotes with newlines
bd comment ISSUE_ID "Implementation notes:
- Point 1
- Point 2"

# Or read from a file
bd comment ISSUE_ID -f comment.txt
```

**Retrieving Full Context When Compacting:**

```bash
# Show full issue with all comments
bd show ISSUE_ID

# Export as JSON for reference
bd export --format=jsonl > backup.jsonl

# Prime context (optimized for AI usage)
bd prime ISSUE_ID
```

**Example BD Workflow:**

1. **Create issue for feature:**

   ```bash
   bd create "Custom Partition Control Feature" --description="Enable custom partition ordering and numbering"
   ```

2. **Add detailed implementation plan:**

   ```bash
   bd comment ISSUE_ID << 'EOF'
   ## Implementation Steps
   1. Modify XML Schema...
   2. Update Data Structures...
   EOF
   ```

3. **Track progress:**

   ```bash
   bd update ISSUE_ID --status in-progress
   ```

4. **When context needs compaction, retrieve full issue:**

   ```bash
   bd show kiwi-qfn  # Shows issue with all context
   ```

### Current Active Issues

- **kiwi-qfn**: Custom Partition Control Feature - Implementation Plan
  - **STATUS**: Code implementation complete ✅, pending integration testing
  - **PLAN FILE**: `/home/cwolfe/.claude/plans/adaptive-hatching-pine.md`
  - **REMAINING WORK**: `make check` with 100% coverage, QEMU integration test, chroot verification
  - Use `bd show kiwi-qfn` to retrieve full plan and context
  - Use `bd comment kiwi-qfn` to add implementation notes
  - Use `bd prime kiwi-qfn` to get AI-optimized context

### Key BD Commands Reference

```bash
bd list                    # List all issues
bd show ISSUE_ID          # Show full issue with comments
bd create TITLE           # Create new issue
bd comment ISSUE_ID       # Add comment to issue
bd update ISSUE_ID        # Update issue fields
bd close ISSUE_ID         # Mark issue as complete
bd delete ISSUE_ID        # Delete issue
bd export                 # Export all issues as JSONL
bd import FILE.jsonl      # Import issues from JSONL
bd prime ISSUE_ID         # Get AI-optimized issue context
```

### Context Preservation Strategy

When implementation requires context compaction:

1. **Before compacting**: Export current state

   ```bash
   bd export > kiwi_backup_$(date +%s).jsonl
   ```

2. **Retrieve full issue context from bd**:

   ```bash
   bd show kiwi-qfn     # Full issue with all comments
   ```

3. **Use bd prime for optimized AI context**:

   ```bash
   bd prime kiwi-qfn    # Returns formatted context optimized for AI
   ```

4. **All task progress tracked in bd**, not in local files

---

## Implementation Notes for Kiwi Custom Partition Control

### CRITICAL CONSTRAINT

When `custom_part_control="true"` is set on `<type>` element:

- Legacy partition control attributes become **ERRORS** (not just redundant)
- Affected attributes: `bootpartition`, `bootpartsize`, `efipartsize`, `swappartsize`, `spare`, `readonly`
- Error message must be meaningful: "custom_part_control=true requires all partition control via <partition> elements. Found legacy attribute: {attribute}. Move this control to explicit <partition> definitions."
- All partition control must move to individual `<partition>` elements with explicit `partition_order` and `partition_number`

### Files Modified

Core files (6):

- `kiwi/schema/kiwi.rng` - Add partition_order, partition_number, boot_flag attributes
- `kiwi/storage/disk.py` - Update ptable_entry_type, add firmware config methods
- `kiwi/xml_state.py` - Extract new attributes, validate uniqueness
- `kiwi/builder/disk.py` - Add custom control flow, refactor partition creation
- `kiwi/partitioner/base.py` - Accept optional partition_id parameter
- `test/data/example_custom_part_control.xml` - Example configurations

Test files (2):

- `tests/unit/storage/test_disk_custom_control.py` - Storage layer tests
- `tests/unit/builder/test_disk_builder_custom_control.py` - Builder layer tests

### Full Plan Location

`/home/cwolfe/.claude/plans/adaptive-hatching-pine.md` - Complete implementation plan with all details
