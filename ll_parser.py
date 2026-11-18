from grammar import EPSILON, END
from first_follow import first_of_sequence


def build_table(g, first, follow):
    # devuelve (table, ok). ok=False si no es LL(1) (choque en una celda)
    table = {nt: {} for nt in g.nonterminals}
    ok = True

    for head in g.nonterminals:
        for alt in g.productions[head]:
            symbols = g.symbols_of(alt)
            alt_first = first_of_sequence(first, symbols)

            for term in alt_first - {EPSILON}:
                if term in table[head]:
                    ok = False      # conflicto First/First
                table[head][term] = alt

            if EPSILON in alt_first:
                for term in follow[head]:
                    if term in table[head]:
                        ok = False
                    table[head][term] = alt

    return table, ok


def parse(g, table, tokens):
    # tokens = lista de terminales, sin el $
    stream = tokens + [END]
    stack = [END, g.start]
    pos = 0

    while stack:
        top = stack.pop()
        look = stream[pos]

        if top == END:
            return look == END

        if not g.is_nonterminal(top):
            if top == look:
                pos += 1
            else:
                return False
        else:
            alt = table[top].get(look)
            if alt is None:
                return False
            for sym in reversed(g.symbols_of(alt)):
                stack.append(sym)

    return stream[pos] == END
