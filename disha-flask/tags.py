"""
Issue › Subject › Sub-subject tags.

The Admin keeps the list as plain text on the Settings page:

    Fishing Rights & Access
    - Net ban / fishing ban period
    -- Compensation during ban
    PMMSY

A report stores the paths that were ticked, e.g.
"Fishing Rights & Access › Net ban / fishing ban period", and, for filters
and charts, the top-level issues in `tags`.
"""
SEP = " › "


def parse(text):
    """Text → [{"name", "subjects": [{"name", "subs": [str]}]}]. Bad lines are skipped."""
    tree = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("--"):
            name = line[2:].strip()
            if name and tree and tree[-1]["subjects"]:
                subs = tree[-1]["subjects"][-1]["subs"]
                if name not in subs:
                    subs.append(name)
        elif line.startswith("-"):
            name = line[1:].strip()
            if name and tree and name not in [s["name"] for s in tree[-1]["subjects"]]:
                tree[-1]["subjects"].append({"name": name, "subs": []})
        elif line not in [t["name"] for t in tree]:
            tree.append({"name": line, "subjects": []})
    return tree


def to_text(tree):
    lines = []
    for issue in tree:
        lines.append(issue["name"])
        for s in issue["subjects"]:
            lines.append("- " + s["name"])
            lines.extend("-- " + sub for sub in s["subs"])
    return "\n".join(lines) + "\n"


def issues(tree):
    return [t["name"] for t in tree]


def all_paths(tree):
    out = []
    for issue in tree:
        out.append(issue["name"])
        for s in issue["subjects"]:
            out.append(issue["name"] + SEP + s["name"])
            out.extend(issue["name"] + SEP + s["name"] + SEP + sub for sub in s["subs"])
    return out


def issue_of(path):
    return path.split(SEP)[0]


def clean_paths(selected, tree, keep=()):
    """Valid ticked paths, in list order, keeping a ticked subject's issue too.
    `keep`: paths already on the report that the Admin has since removed
    from the list; they stay so old reports are not changed by accident."""
    valid = set(all_paths(tree)) | set(keep)
    chosen = [p for p in dict.fromkeys(selected) if p in valid]
    for p in list(chosen):
        parts = p.split(SEP)
        for i in range(1, len(parts)):
            parent = SEP.join(parts[:i])
            if parent not in chosen:
                chosen.append(parent)
    order = {p: i for i, p in enumerate(all_paths(tree))}
    return sorted(chosen, key=lambda p: (order.get(p, len(order)), p))


def issues_from_paths(paths):
    return list(dict.fromkeys(issue_of(p) for p in paths))


def leaf_paths(paths):
    """Only the most specific paths, for display: "A › B" hides "A"."""
    return [p for p in paths if not any(o != p and o.startswith(p + SEP) for o in paths)]
