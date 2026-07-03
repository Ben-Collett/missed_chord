def captlized_and_uncaptlized(word: str):
    assert word != "", "why are you trying captlized an empty word dummy"
    start, *rest = word
    rest = "".join(rest)
    return start.upper() + rest, start.lower() + rest


def append_captlized_and_uncaptlized(ls: list[str], word: str):
    cap, uncap = captlized_and_uncaptlized(word)
    ls.append(cap)
    ls.append(uncap)
