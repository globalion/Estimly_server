def normalize(value: str) -> str:
    """
    Canonical role name rules:
    - lowercase
    - remove spaces
    - remove '/'
    - keep everything else (+, #, etc.)
    """

    return value.strip().lower().replace(" ", "").replace("/", "")
