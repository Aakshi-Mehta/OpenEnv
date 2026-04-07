# Custom Weighting for Expected Fixes

## Overview
The environment now supports customizable weighting for expected fixes, allowing you to:
1. Assign different importance levels to fixes (via `weight` parameter)
2. Group fixes as alternatives - completing ANY fix in a group counts as completing that group (via `group` parameter)

## Usage

### Basic Structure
Each fix in `expected_fixes` can now have optional fields:

```python
{
    "element_id": "element_id",
    "attribute": "aria-label",
    "weight": 1.0,           # Optional: importance (default 1.0)
    "group": "group_name",   # Optional: alternative group
    "value": "expected_value" # Optional: specific value required
}
```

### Example 1: Grouped Alternatives (easy_1_checkout)
For the checkout button, EITHER adding `aria-label` to the button OR adding `alt` to the icon makes it accessible. Only one is needed:

```python
"expected_fixes": [
    {
        "element_id": "checkout-btn",
        "attribute": "aria-label",
        "group": "checkout_label",
        "weight": 1.0
    },
    {
        "element_id": "cart-icon",
        "attribute": "alt",
        "group": "checkout_label",
        "weight": 1.0
    }
]
```

**Result**: Agent gets reward of 1.0 by completing EITHER fix ✓

### Example 2: Mixed Weighted Fixes
Different fixes with different weights:

```python
"expected_fixes": [
    {
        "element_id": "form",
        "attribute": "role",
        "value": "form",
        "weight": 0.5  # Less important
    },
    {
        "element_id": "input",
        "attribute": "aria-label",
        "weight": 1.5  # More important
    }
]
```

**Result**: 
- Total weight = 2.0
- Completing only aria-label = 1.5/2.0 = 0.75 reward
- Completing both = 2.0/2.0 = 1.0 reward

### Example 3: Multiple Groups
Different groups for different aspects:

```python
"expected_fixes": [
    {
        "element_id": "modal",
        "attribute": "role",
        "value": "dialog",
        "group": "modal_semantics",
        "weight": 1.0
    },
    {
        "element_id": "modal",
        "attribute": "aria-modal",
        "value": "true",
        "group": "modal_semantics",
        "weight": 1.0
    },
    {
        "element_id": "background",
        "attribute": "aria-hidden",
        "value": "true",
        "group": "inert_background",
        "weight": 1.0
    }
]
```

**Result**:
- Total weight = 2.0 (one unit per group)
- Completing modal_semantics (either one) + inert_background = 1.0 reward
- Completing only modal_semantics (either one) = 0.5 reward

## How Scoring Works

### Without Groups (Ungrouped fixes)
- Each fix contributes its weight to the total
- Total reward = sum of applied weights / sum of all weights

### With Groups (Grouped fixes)
- Each group acts as a single unit with the group's weight
- **Only ONE fix per group needs to be completed** to "complete" that group
- If any fix in a group is applied, that group's entire weight is counted
- Total reward = sum of completed group weights + ungrouped applied weights / total weight

## Real-World Example

For `easy_1_checkout` (Checkout button & cart icon):

**Old System (Equal Weight)**:
- Both fixes required for 1.0 score
- Agent must add BOTH aria-label AND alt

**New System (Grouped)**:
- Both fixes in same group "checkout_label"
- Agent gets 1.0 score by adding EITHER aria-label OR alt ✓

## Tips

1. **Use groups for semantic alternatives**: If multiple different fixes achieve the same accessibility goal, put them in a group
2. **Use weights for importance**: Heavier weights force agents to prioritize critical fixes
3. **Default weight is 1.0**: Omit `weight` if not needed
4. **Each group is independent**: Fixes in different groups are unrelated
5. **Test with your agent**: Run tasks to verify scoring matches your expectations

## Modifying Existing Tasks

To add weighting to existing tasks, just add the `weight` and/or `group` fields to the fix dictionaries:

```python
# Before
"expected_fixes": [{"element_id": "btn", "attribute": "aria-label"}]

# After
"expected_fixes": [{"element_id": "btn", "attribute": "aria-label", "weight": 1.0}]
```

Backward compatible - tasks without weights still work with default 1.0 weight!
