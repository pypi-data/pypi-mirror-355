def infer_type(column_name):
    name = column_name.lower()
    if "id" in name or name.endswith("_no") or name == "roll_no":
        return int
    elif "date" in name:
        return str  # or datetime
    elif "is_" in name or name.startswith("has_"):
        return bool
    elif any(kw in name for kw in ["age", "count", "num", "marks", "salary", "average"]):
        return int
    else:
        return str
