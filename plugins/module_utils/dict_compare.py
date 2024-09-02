def dict_issubset(a: dict, b: dict) -> bool:
    """
    Given a pair of dictionaries, test to see whether dict a contains a subset
    of the keys and values of dict b.
    
    Dict a is a subset of b if every key in a has a corresponding key in b the
    same value. Where the value is a dictionary, the dictionary subset test is
    performed recursively, rather than comparing the dictionaries as-is.
    """
    for key in a:
        if key not in b:
            return False
        
        if isinstance(a[key], dict) and isinstance(b[key], dict):
            if not dict_issubset(a[key], b[key]):
                return False
        elif a[key] != b[key]:
            return False
    
    return True

