from grammar import EPSILON, END

# item = tupla (head, body, dot). body es tuple de simbolos, dot es int


def augmented(g):
    # agrega S' -> S como nuevo start
    start_prime = g.start + "'"
    bodies = {start_prime: [(g.start,)]}
    for nt in g.nonterminals:
        bodies[nt] = [tuple(g.symbols_of(alt)) for alt in g.productions[nt]]
    return start_prime, bodies


def closure(items, bodies, nonterminals):
    result = set(items)
    pending = list(items)
    while pending:
        head, body, dot = pending.pop()
        if dot < len(body):
            nxt = body[dot]
            if nxt in nonterminals:
                for b in bodies[nxt]:
                    item = (nxt, b, 0)
                    if item not in result:
                        result.add(item)
                        pending.append(item)
    return frozenset(result)


def goto(items, symbol, bodies, nonterminals):
    moved = set()
    for head, body, dot in items:
        if dot < len(body) and body[dot] == symbol:
            moved.add((head, body, dot + 1))
    if not moved:
        return None
    return closure(moved, bodies, nonterminals)


def canonical_collection(g):
    start_prime, bodies = augmented(g)
    nonterminals = set(bodies.keys())
    symbols = sorted(g.terminals) + sorted(nonterminals)

    start_item = (start_prime, (g.start,), 0)
    start_state = closure({start_item}, bodies, nonterminals)

    states = [start_state]
    index = {start_state: 0}
    transitions = {}

    i = 0
    while i < len(states):
        state = states[i]
        for sym in symbols:
            target = goto(state, sym, bodies, nonterminals)
            if target is None:
                continue
            if target not in index:
                index[target] = len(states)
                states.append(target)
            transitions[(i, sym)] = index[target]
        i += 1

    return states, transitions, start_prime, nonterminals


def build_tables(g, follow):
    states, transitions, start_prime, nonterminals = canonical_collection(g)

    action = [{} for _ in states]
    goto_table = [{} for _ in states]
    ok = True

    def set_action(state, term, value):
        nonlocal ok
        if term in action[state] and action[state][term] != value:
            ok = False
        action[state][term] = value

    for (state, sym), target in transitions.items():
        if sym in nonterminals:
            goto_table[state][sym] = target
        else:
            set_action(state, sym, ('shift', target))

    for s, state in enumerate(states):
        for head, body, dot in state:
            if dot < len(body):
                continue
            if head == start_prime:
                set_action(s, END, ('accept', None))
            else:
                for term in follow[head]:
                    set_action(s, term, ('reduce', head, body))

    return action, goto_table, ok


def parse(g, action, goto_table, tokens):
    # tokens = lista de terminales, sin el $
    stream = tokens + [END]
    stack = [0]
    pos = 0

    while True:
        state = stack[-1]
        look = stream[pos]
        entry = action[state].get(look)
        if entry is None:
            return False

        kind = entry[0]
        if kind == 'shift':
            stack.append(entry[1])
            pos += 1
        elif kind == 'reduce':
            _, head, body = entry
            for _ in range(len(body)):
                stack.pop()
            stack.append(goto_table[stack[-1]][head])
        elif kind == 'accept':
            return True
        else:
            return False


class Node:
    def __init__(self, symbol, children=None, body=None):
        self.symbol = symbol
        self.children = children or [] # de izq a der
        self.body = body # produccion usada, None si es hoja
        self.attrs = {} # nombre atributo -> valor

    def is_leaf(self):
        return not self.children


def parse_tree(g, action, goto_table, tokens):
    # igual que parse pero arma el arbol. None si rechaza
    stream = tokens + [END]
    stack = [0]
    nodes = []
    pos = 0

    while True:
        state = stack[-1]
        look = stream[pos]
        entry = action[state].get(look)
        if entry is None:
            return None

        kind = entry[0]
        if kind == 'shift':
            stack.append(entry[1])
            nodes.append(Node(look))
            pos += 1
        elif kind == 'reduce':
            _, head, body = entry
            children = []
            for _ in range(len(body)):
                stack.pop()
                children.insert(0, nodes.pop())
            stack.append(goto_table[stack[-1]][head])
            nodes.append(Node(head, children, body))
        elif kind == 'accept':
            return nodes[-1]
        else:
            return None
