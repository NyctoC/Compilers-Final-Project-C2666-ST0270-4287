from grammar import read_grammar
from first_follow import first_sets, follow_sets
import slr_parser


# gramatica del Item 3 (binario -> decimal). Se parsea con el parser del Item 2.
#   S -> N ; N -> BN | B ; B -> 0 | 1
# 'pos' es heredado (peso del bit), 'dec' sintetizado (valor)
GRAMMAR_TEXT = """3
S -> N
N -> BN B
B -> 0 1
"""


# SDD como data. Por cada produccion (head, body), sus reglas.
# defines=(idx, nombre), idx 0 = head y 1..k = cuerpo. uses igual. fn calcula.
# el evaluador no sabe nada de esta SDD: para cambiarla solo tocas esta tabla
def _rule(defines, uses, fn):
    return {'defines': defines, 'uses': uses, 'fn': fn}


SDD = {
    ('S', ('N',)): [
        _rule((1, 'pos'), [(1, 'len')], lambda n_len: n_len - 1),
        _rule((0, 'dec'), [(1, 'dec')], lambda n_dec: n_dec),
    ],
    ('N', ('B', 'N')): [
        _rule((0, 'len'), [(2, 'len')], lambda n2_len: n2_len + 1),
        _rule((2, 'pos'), [(0, 'pos')], lambda n1_pos: n1_pos - 1),
        _rule((0, 'dec'), [(1, 'val'), (0, 'pos'), (2, 'dec')],
              lambda b_val, n1_pos, n2_dec: b_val * (2 ** n1_pos) + n2_dec),
    ],
    ('N', ('B',)): [
        _rule((0, 'len'), [], lambda: 1),
        _rule((0, 'dec'), [(1, 'val'), (0, 'pos')],
              lambda b_val, n_pos: b_val * (2 ** n_pos)),
    ],
    ('B', ('0',)): [
        _rule((0, 'val'), [], lambda: 0),
    ],
    ('B', ('1',)): [
        _rule((0, 'val'), [], lambda: 1),
    ],
}

# atributo del resultado final, se lee del start
MAIN_ATTRIBUTE = 'dec'


# evaluador generico: arbol -> grafo de deps -> orden topologico -> evaluar
# sirve para cualquier SDD no circular

class CircularSDD(Exception):
    pass


def _number_nodes(root):
    # id a cada nodo pa' imprimir bonito
    order = []

    def walk(node):
        node.nid = len(order)
        order.append(node)
        for child in node.children:
            walk(child)

    walk(root)
    return order


def _leaf_lexval(node):
    # lexval del terminal = el char mismo
    node.attrs['lexval'] = node.symbol


def build_dependency_graph(root):
    # vertice = (nodo, atributo). arista va del usado al definido
    edges = {}          # vertice -> set de los que dependen de el
    indeg = {}          # vertice -> grado de entrada
    rules = []          # (target, [sources], fn)

    def vertex(node, name):
        v = (node, name)
        if v not in indeg:
            indeg[v] = 0
            edges[v] = set()
        return v

    def walk(node):
        if node.is_leaf():
            _leaf_lexval(node)
            vertex(node, 'lexval')
            return

        for child in node.children:
            walk(child)

        key = (node.symbol, tuple(node.body))
        symbols = [node] + node.children
        for r in SDD.get(key, []):
            di, dname = r['defines']
            target = vertex(symbols[di], dname)
            sources = [vertex(symbols[ui], uname) for ui, uname in r['uses']]
            rules.append((target, sources, r['fn']))
            for s in sources:
                if target not in edges[s]:
                    edges[s].add(target)
                    indeg[target] += 1

    walk(root)
    return edges, indeg, rules


def topological_order(edges, indeg):
    # algoritmo de Kahn. si queda ciclo -> CircularSDD
    indeg = dict(indeg)
    ready = [v for v, d in indeg.items() if d == 0]
    order = []
    while ready:
        v = ready.pop()
        order.append(v)
        for w in edges[v]:
            indeg[w] -= 1
            if indeg[w] == 0:
                ready.append(w)
    if len(order) != len(indeg):
        raise CircularSDD()
    return order


def evaluate(root):
    edges, indeg, rules = build_dependency_graph(root)
    order = topological_order(edges, indeg)

    by_target = {}
    for target, sources, fn in rules:
        by_target[target] = (sources, fn)

    for vertex in order:
        node, name = vertex
        if name == 'lexval':
            continue
        if vertex in by_target:
            sources, fn = by_target[vertex]
            args = [sn.attrs[aname] for sn, aname in sources]
            node.attrs[name] = fn(*args)

    return order


# salida
def _attrs_text(node):
    if not node.attrs:
        return ''
    items = ', '.join(f"{k}={node.attrs[k]}" for k in sorted(node.attrs))
    return ' {' + items + '}'


def print_tree(node, depth=0):
    print('  ' * depth + node.symbol + _attrs_text(node))
    for child in node.children:
        print_tree(child, depth + 1)


def print_order(order):
    names = [f"{node.symbol}{node.nid}.{name}" for (node, name) in order]
    print('Evaluation order: ' + ' -> '.join(names))


def load_grammar():
    lines = iter(GRAMMAR_TEXT.splitlines())
    g = read_grammar(lines)
    first = first_sets(g)
    follow = follow_sets(g, first)
    action, goto_table, _ = slr_parser.build_tables(g, follow)
    return g, action, goto_table


def run():
    import sys
    g, action, goto_table = load_grammar()

    for raw in sys.stdin:
        line = raw.rstrip('\n')
        if line == '':
            break
        tokens = [] if line == 'e' else list(line)
        root = slr_parser.parse_tree(g, action, goto_table, tokens)
        if root is None:
            print('no')
            continue
        _number_nodes(root)
        try:
            order = evaluate(root)
        except CircularSDD:
            print('The SDD is circular.')
            continue
        print_tree(root)
        print_order(order)
        print(f"{MAIN_ATTRIBUTE}({g.start}) = {root.attrs.get(MAIN_ATTRIBUTE)}")


if __name__ == '__main__':
    run()
