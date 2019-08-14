from wick.index import Idx
from wick.expression import *
from wick.hamiltonian import one_e, two_e, get_sym
from wick.wick import apply_wick

H1 = one_e("f",["occ","vir"], norder=True)
H2 = two_e("I",["occ","vir"], norder=True)

H = H1 + H2
i = Idx(0,"occ")
j = Idx(1,"occ")
a = Idx(0,"vir")
b = Idx(1,"vir")

sym = get_sym(True)
C0 = Expression([Term(1.0,[], [Tensor([], "c")], [], [])])
C1 = Expression(
    [Term(1.0,
        [Sigma(i), Sigma(a)],
        [Tensor([a, i], "c")],
        [Operator(a, True), Operator(i, False)],
        [])])
C2 = Expression(
    [Term(0.25,
        [Sigma(i), Sigma(a), Sigma(j), Sigma(b)],
        [Tensor([a, b, i, j], "c", sym=sym)],
        [Operator(a, True), Operator(i, False), Operator(b, True), Operator(j, False)],
        [])])

ket = C0 + C1 + C2
HC = H*ket

operators = [Operator(i,True), Operator(a,False), Operator(j,True), Operator(b,False)]
bra = Expression([Term(1.0, [], [Tensor([i, j, a, b], "")], operators, [])])
S = bra*HC
out = apply_wick(S)
out.resolve()
final = AExpression(Ex=out)
final.simplify()
final.sort()
print("Sigma2")
print(final._print_str())

operators = [Operator(i,True), Operator(a,False)]
bra = Expression([Term(1.0, [], [Tensor([i, a], "")], operators, [])])
S = bra*HC
out = apply_wick(S)
out.resolve()
final = AExpression(Ex=out)
final.simplify()
final.sort()
print("Sigma1")
print(final._print_str())


bra = Expression([Term(1.0, [], [Tensor([], "")], [], [])])
S = bra*HC
out = apply_wick(S)
out.resolve()
final = AExpression(Ex=out)
final.simplify()
final.sort()
print("Sigma0")
print(final._print_str())
