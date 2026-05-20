# Fix Schedule Duplication and Misalignment

The parser currently treats each `<td>` cell in the schedule table as a separate time slot (period). If a time slot (e.g., 15:50 - 17:10 or 8:00 - 9:20) is split into multiple columns in the HTML (using `colspan` in the header), the parser creates separate blocks for each column.

This causes two major issues:
1. **Duplicate subgroups**: If a subject is split into subgroups in different cells for the same time, they appear as two separate lessons in the UI.
2. **Incorrect lesson numbering**: If a time slot spans multiple columns and is empty, it produces multiple "Empty lesson" blocks, making subsequent lessons appear to start later than they actually do (e.g., a 3rd period lesson appearing as the 4th period).

## Proposed Changes

### Schedule Parser

#### [schedule_parser.py](file:///E:/IDE/APKLife/app/src/main/python/runtime_app/services/schedule_parser.py)

- Modify `parse_schedule_html` to group columns into logical "time slots" based on the `colspan` attributes in the `<thead>`.
- Instead of expanding headers and then iterating over cells, we will pre-calculate the boundaries of each time slot.
- For each day row, we will:
    - Iterate through the pre-calculated time slots.
    - Collect all `<td>` cells that fall within each slot's column range.
    - Parse each cell and merge the resulting lessons into a single list for that slot.
    - **Deduplication**: If multiple cells within a slot contain the same subject/teacher/room (unlikely but possible), they should be deduplicated.
    - **Empty Handling**: If a slot has multiple columns, but only some have lessons, we will ignore the empty ones. If all are empty, we keep one empty placeholder.
- This will ensure that a `colspan="2"` in the header results in exactly one block in the UI, regardless of how many `<td>` cells are used in the rows.

## Verification Plan

### Automated Tests
- Run `reproduce_issue.py` and verify:
    - **Thursday 21.05**: Slot 7 contains both "Иностранный язык" entries.
    - **Wednesday 20.05**: Slot 1 is "8:00-9:20" (one empty block), Slot 2 is "9:30-10:50" (one empty block), and Slot 3 is "11:20-12:40" (Physical Education).
- Run existing tests in `test_schedule_parser.py`.
