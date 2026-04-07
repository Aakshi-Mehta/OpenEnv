from bs4 import BeautifulSoup


class Grader:
    def __init__(self, discovery_reward=0.2):
        self.DISCOVERY_REWARD = discovery_reward

    def _is_fix_applied(self, expected_fix, fixes_applied, dom):
        """Check if a specific fix has been applied."""
        fix_key = f"{expected_fix['element_id']}_{expected_fix['attribute']}"
        if fix_key not in fixes_applied:
            return False

        # If value is specified, verify it's stored correctly
        if "value" in expected_fix:
            el = dom.find(id=expected_fix["element_id"])
            if el:
                actual_value = el.get(expected_fix["attribute"], "")
                expected_value = expected_fix["value"]
                return expected_value.lower() == str(actual_value).lower()

        return True

    def _calculate_base_score(self, current_task_meta, fixes_applied, dom):
        """
        Calculate base score using grouping and weight logic:
        - Ungrouped fixes: each has a weight
        - Grouped fixes: completing ANY fix in a group counts as completing that group
        - total_weight = ungrouped_weight + sum(group_weights)
        - completed_weight = ungrouped_completed + sum(group_completed_weights)
        - base_score = completed_weight / total_weight
        """
        expected_fixes = current_task_meta.get("expected_fixes", [])

        if not expected_fixes:
            return 0.0

        # Build group->fixes map and collect all groups/ungrouped fixes
        groups = {}
        ungrouped_weight = 0.0

        for fix in expected_fixes:
            weight = fix.get("weight", 0.0)
            group_id = fix.get("group", None)

            if group_id:
                if group_id not in groups:
                    groups[group_id] = {"weight": weight, "fixes": []}
                groups[group_id]["fixes"].append(fix)
            else:
                ungrouped_weight += weight

        # Calculate total possible weight
        total_weight = ungrouped_weight + sum(g["weight"] for g in groups.values())

        if total_weight == 0:
            return 0.0

        # Calculate completed weight
        completed_weight = 0.0

        # Check ungrouped fixes
        for fix in expected_fixes:
            if fix.get("group") is None:
                if self._is_fix_applied(fix, fixes_applied, dom):
                    completed_weight += fix.get("weight", 1.0)

        # Check grouped fixes (need only one per group)
        for group_id, group_data in groups.items():
            for fix in group_data["fixes"]:
                if self._is_fix_applied(fix, fixes_applied, dom):
                    completed_weight += group_data["weight"]
                    break  # Only count once per group

        return completed_weight / total_weight

    def calculate_reward(self, current_task_meta, fixes_applied, discovered_issues, dom):
        """
        Calculate reward:
        - Base: using grouping and weight logic (see _calculate_base_score)
        - Bonus: +0.2 for discovering an issue ONLY if base_score is 0 (no fixes applied yet)

        Once any fix is applied, base_score becomes > 0 and discovery bonus is no longer available.
        """
        base_score = self._calculate_base_score(current_task_meta, fixes_applied, dom)

        # Add discovery bonus only if base_score is 0 (no fixes applied yet)
        if base_score == 0 and len(discovered_issues) > 0:
            discovery_bonus = self.DISCOVERY_REWARD
            return discovery_bonus

        return base_score

    def detect_discovered_issue(self, element_id, current_task_meta, fixes_applied, discovered_issues, dom):
        """
        Check if element has an undiscovered accessibility issue.
        Returns True if a new issue was freshly discovered.
        Discovery bonus (0.2) is only awarded if base_score is 0 (no fixes applied yet).
        Base score is calculated using grouping and weight logic.
        """
        expected_fixes = current_task_meta.get("expected_fixes", [])

        if not expected_fixes:
            return False

        # Calculate current base score using grouping/weight logic
        base_score = self._calculate_base_score(current_task_meta, fixes_applied, dom)

        # Only award discovery if base_score is 0 (no fixes applied yet)
        if base_score > 0:
            return False

        # Check if this element has an issue
        for fix in expected_fixes:
            if fix["element_id"] == element_id:
                fix_key = f"{element_id}_{fix['attribute']}"
                # If issue exists but not yet discovered
                if fix_key not in discovered_issues:
                    discovered_issues.add(fix_key)
                    return True

        return False
