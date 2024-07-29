from difflib import ndiff


def ndiff_filter(a: list[str], b: list[str]) -> list[str]:
    """
    Given a pair of lists of strings (e.g. representing lines of files), return
    a full diff (one line at a time).
    """
    return list(ndiff(a, b))


class FilterModule(object):
    def filters(self):
        return {
            'ndiff': ndiff_filter,
        }
