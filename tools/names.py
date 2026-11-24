"""Name and item-number matching, as the ballot check uses it."""
import re

_PUNCT = re.compile(r"[“”‘’\"'.,]")


def norm_name(s):
    s = re.sub(r"^(elect|election of director[s]?:?|election of)\s+", "", str(s or "").strip(), flags=re.I)
    s = re.sub(r"^(dr|mr|mrs|ms|sir)\.?\s+", "", s, flags=re.I)
    s = re.sub(r"\([^)]*\)|\*|\d+$", "", s)
    s = re.sub(r",\s*(executive chairman|chairman|chair|lead independent director|chief executive officer)[^,]*$", "", s, flags=re.I)
    s = _PUNCT.sub("", s); s = re.sub(r"\s+", " ", s).strip().lower()
    return s

def last_token(s):
    parts = [p for p in norm_name(s).split(" ") if p and not re.fullmatch(r"(jr|sr|ii|iii|iv|md|phd|dvm)", p)]
    return parts[-1] if parts else ""

def same_first_name(fa, fb):
    # an initial, or a short form the full name begins with (Tim, Timothy), names the same person
    fa, fb = sorted((fa, fb), key=len)
    return fa == fb or fa[:1] == fb[:1] and len(fa) <= 2 or len(fa) >= 3 and fb.startswith(fa)

def same_person(a, b):
    a, b = norm_name(a), norm_name(b)
    if not a or not b or last_token(a) != last_token(b): return False
    if len(a.split(" ")) == 1 or len(b.split(" ")) == 1: return True
    return same_first_name(a.split(" ")[0], b.split(" ")[0])


class checklist:
    """The strict reading of one person's name, kept under the name the looser reading calls it by."""
    norm_name = staticmethod(norm_name)
    same_person = staticmethod(same_person)


_HONOURS = re.compile(r",?\s+(?!(?:II|III|IV|VI|VII|VIII|JR|SR)$)[A-Z]{2,5}$")
_NICK = {"rick": "richard", "dick": "richard", "bob": "robert", "bill": "william", "jim": "james", "joe": "joseph",
         "mike": "michael", "tom": "thomas", "tony": "anthony", "andy": "andrew", "ed": "edward", "chuck": "charles",
         "dave": "david", "steve": "stephen", "pat": "patricia", "liz": "elizabeth", "kate": "katherine"}
_SUFFIX = re.compile(r"(?i),?\s+(esq\.?|m\.?d\.?|ph\.?d\.?|jr\.?|sr\.?|ii|iii|iv|cpa)\b")


def nominee_name(title):
    """The nominee in a printed election title ('Election of Directors: A. B. Name', '... — 1a. Name'), with any
    parenthetical (a quoted notice, a nickname) and trailing honours dropped."""
    s = str(title or "")
    while re.search(r"\([^()]*\)", s):
        s = re.sub(r"\([^()]*\)", "", s)
    s = re.split(r"[:—–]", s)[-1]
    s = re.sub(r"^\s*\d+[a-z]?\.\s*", "", s, flags=re.I).strip()
    # An all-capitals name, or a capitalised surname left alone after a first name, is a name, not honours.
    while re.search(r"[a-z]", s):
        t = _HONOURS.sub("", s).strip()
        if t == s or len(t.split()) < 2:
            break
        s = t
    return s

def _given_names(n):
    toks = [x for x in re.sub(r"[^a-z ]", " ", _SUFFIX.sub("", n).lower()).split() if len(x) > 1]
    return [_NICK.get(x, x) for x in toks]

def same_person(a, b):
    """The loose reading of one person: checklist.same_person (surname, then a first name, an initial or a short
    form), or one name's first given name among the other's given names, read through common nicknames, which is
    how a filing and a board record differ when one leads with a middle name."""
    if checklist.same_person(a, b):
        return True
    ta, tb = _given_names(a), _given_names(b)
    if not ta or not tb or ta[-1] != tb[-1]:
        return False
    return ta[0] in tb[:-1] or tb[0] in ta[:-1]

def join_names(gold_names, engine_names):
    """{gold index: engine index}. An exact normalized name joins first: two nominees can share a first and last name
    and differ only by a middle initial, which the loose reading ignores. The loose reading joins only when it finds
    exactly one engine name not already joined, so an ambiguous name stays unjoined and shows as a D1 miss instead
    of borrowing another nominee's row."""
    keys = [checklist.norm_name(n) for n in engine_names]
    taken, out = set(), {}
    for g, name in enumerate(gold_names):
        hit = next((i for i, k in enumerate(keys) if i not in taken and k and k == checklist.norm_name(name)), None)
        if hit is not None:
            taken.add(hit); out[g] = hit
    for g, name in enumerate(gold_names):
        if g in out:
            continue
        loose = [i for i, n in enumerate(engine_names) if i not in taken and same_person(n, name)]
        if len(loose) == 1:
            taken.add(loose[0]); out[g] = loose[0]
    return out

def _item_key(no):
    """A printed item number as the engine and the gold both write it: case, punctuation and a 'Proposal'/'Item'
    prefix dropped. A builder numbers repeated printed numbers apart (1.01, 1.02), so that suffix is dropped too."""
    s = str(no or "").strip().lower()
    s = re.sub(r"\.\d{2}$", "", s)
    s = re.sub(r"^(proposal|item|no)\.?\s*", "", s)
    return re.sub(r"[^0-9a-z]", "", s).lstrip("0")
