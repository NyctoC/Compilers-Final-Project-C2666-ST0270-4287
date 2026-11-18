EPSILON = 'e'
END = '$'


class Grammar:
    def __init__(self):
        self.start = 'S'
        self.nonterminals = [] # orden en que se leen
        self.productions = {} # NT -> lista de lados derechos
        self.terminals = set()

    def add_rule(self, head, alternatives):
        if head not in self.productions:
            self.productions[head] = []
            self.nonterminals.append(head)
        for alt in alternatives:
            self.productions[head].append(alt)

    def is_nonterminal(self, symbol):
        return symbol in self.productions

    def is_terminal(self, symbol):
        return symbol not in self.productions and symbol != EPSILON

    def symbols_of(self, rhs):
        # rhs es string de simbolos de 1 char, 'e' = vacio
        if rhs == EPSILON:
            return []
        return list(rhs)

    def finish(self):
        # todo char que no sea NT ni 'e' es terminal
        self.terminals = set()
        for head in self.nonterminals:
            for alt in self.productions[head]:
                for sym in self.symbols_of(alt):
                    if sym not in self.productions:
                        self.terminals.add(sym)


def read_grammar(line_source):
    g = Grammar()
    n = int(next(line_source).strip())
    for _ in range(n):
        line = next(line_source).rstrip('\n')
        head, rest = line.split('->')
        head = head.strip()
        alternatives = rest.split()
        g.add_rule(head, alternatives)
    g.finish()
    return g
