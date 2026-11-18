import sys

from grammar import read_grammar, EPSILON
from first_follow import first_sets, follow_sets, print_sets
import ll_parser
import slr_parser


def to_tokens(line):
    # linea con solo 'e' = string vacio
    if line == EPSILON:
        return []
    return list(line)


def read_lines():
    for line in sys.stdin:
        yield line


def run():
    show_sets = '--sets' in sys.argv[1:]

    lines = read_lines()
    g = read_grammar(lines)

    first = first_sets(g)
    follow = follow_sets(g, first)

    if show_sets:
        print_sets(g, first, follow)

    ll_table, is_ll1 = ll_parser.build_table(g, first, follow)
    slr_action, slr_goto, is_slr1 = slr_parser.build_tables(g, follow)

    def read_string():
        line = next(lines, None)
        if line is None:
            return None
        return line.rstrip('\n')

    def parse_with(parser):
        while True:
            s = read_string()
            if s is None or s == '':
                break
            tokens = to_tokens(s)
            print('yes' if parser(tokens) else 'no')

    if is_ll1 and is_slr1:
        prompt = "Select a parser (T: for LL(1), B: for SLR(1), Q: quit):"
        print(prompt)
        while True:
            choice = read_string()
            if choice is None or choice == 'Q':
                break
            if choice == 'T':
                parse_with(lambda t: ll_parser.parse(g, ll_table, t))
            elif choice == 'B':
                parse_with(lambda t: slr_parser.parse(g, slr_action, slr_goto, t))
            print(prompt)
    elif is_ll1:
        print("Grammar is LL(1).")
        parse_with(lambda t: ll_parser.parse(g, ll_table, t))
    elif is_slr1:
        print("Grammar is SLR(1).")
        parse_with(lambda t: slr_parser.parse(g, slr_action, slr_goto, t))
    else:
        print("Grammar is neither LL(1) nor SLR(1).")


if __name__ == '__main__':
    run()
