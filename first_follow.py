from grammar import EPSILON, END


def first_sets(g):
    first = {nt: set() for nt in g.nonterminals}

    changed = True
    while changed:
        changed = False
        for head in g.nonterminals:
            for alt in g.productions[head]:
                symbols = g.symbols_of(alt)
                before = len(first[head])

                if not symbols: # head -> e (vacio)
                    first[head].add(EPSILON)
                else:
                    nullable_prefix = True
                    for sym in symbols:
                        if g.is_nonterminal(sym):
                            first[head] |= (first[sym] - {EPSILON})
                            if EPSILON not in first[sym]:
                                nullable_prefix = False
                                break
                        else: # terminal
                            first[head].add(sym)
                            nullable_prefix = False
                            break
                    if nullable_prefix:
                        first[head].add(EPSILON)

                if len(first[head]) != before:
                    changed = True

    return first


def first_of_sequence(first, symbols):
    # FIRST de una cadena de simbolos (incluye 'e' si toda la cadena es nullable)
    result = set()
    for sym in symbols:
        sym_first = first.get(sym, {sym})
        result |= (sym_first - {EPSILON})
        if EPSILON not in sym_first:
            return result
    result.add(EPSILON)
    return result


def follow_sets(g, first):
    follow = {nt: set() for nt in g.nonterminals}
    follow[g.start].add(END)

    changed = True
    while changed:
        changed = False
        for head in g.nonterminals:
            for alt in g.productions[head]:
                symbols = g.symbols_of(alt)
                for i, sym in enumerate(symbols):
                    if not g.is_nonterminal(sym):
                        continue
                    before = len(follow[sym])
                    rest = symbols[i + 1:]
                    rest_first = first_of_sequence(first, rest)
                    follow[sym] |= (rest_first - {EPSILON})
                    if EPSILON in rest_first:
                        follow[sym] |= follow[head]
                    if len(follow[sym]) != before:
                        changed = True

    return follow


def format_set(symbols):
    # terminales en orden ASCII, luego 'e', luego '$'
    terminals = sorted(s for s in symbols if s not in (EPSILON, END))
    ordered = list(terminals)
    if EPSILON in symbols:
        ordered.append(EPSILON)
    if END in symbols:
        ordered.append(END)
    return '{' + ', '.join(ordered) + '}'


def print_sets(g, first, follow):
    for nt in sorted(g.nonterminals):
        print(f"First({nt}) = {format_set(first[nt])}")
    for nt in sorted(g.nonterminals):
        print(f"Follow({nt}) = {format_set(follow[nt])}")
