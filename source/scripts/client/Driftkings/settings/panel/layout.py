"""Balance unpaired controls while preserving explicitly paired left/right columns."""
def balance_columns(controls):
    groups = {}
    section = 0
    for control in controls:
        if not control.visible:
            continue
        if control.type in ('section', 'separator'):
            control.column = -1
            section += 1
            continue
        groups.setdefault((section, str(control.tab)), []).append(control)
    for items in groups.values():
        # Keep deliberately paired columns (for example ally/enemy settings).
        left = [c for c in items if c.column == 0]
        right = [c for c in items if c.column == 1]
        if left and right:
            for control in items:
                if control.column not in (0, 1):
                    control.column = 0 if len(left) <= len(right) else 1
                    (left if control.column == 0 else right).append(control)
            continue
        total = sum(3 if c.preview else 1 for c in items)
        weight = 0
        for index, control in enumerate(items):
            control.column = 0 if index == 0 or weight < total / 2.0 else 1
            weight += 3 if control.preview else 1
