def normalize_role_name(label: str) -> str:
    """
    Canonical role name rules:
    - lowercase
    - remove spaces
    - remove '/'
    - keep everything else (+, #, etc.)
    """
    return label.strip().lower().replace(" ", "").replace("/", "")


def normalize(value: str) -> str:
    return value.strip().lower().replace(" ", "").replace("/", "")
