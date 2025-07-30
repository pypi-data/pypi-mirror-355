def union(dicts: list[dict]) -> dict:
    """
    Note: the ordering of the given dictionaries matters.

    :param dicts: List of dictionaries
    :return: Union over all dictionaries.
    """
    # source: https://peps.python.org/pep-0584/#dict-union-will-be-inefficient
    new = {}
    for d in dicts:
        new |= d
    return new
