from copy import deepcopy
from itertools import product
from numbers import Number
from operator import Sigma, Delta, Operator, Tensor, permute

class TermMap(object):

    class AbIdx(object):
        def __init__(self, idx, ts, os, summed):
            self.idx = idx
            self.ts = ts
            self.os = os
            self.summed = summed

        def __eq__(self, other):
            first = self.idx.space == other.idx.space and self.summed == other.summed
            if not first: return False
            if not self.os == other.os: return False
            for t,i in self.ts:
                found = False
                for s,j in other.ts:
                    if t.name == s.name and i == j:
                        found = True
                        break
                if not found: return False
            return True

    def __init__(self, sums, tensors, operators, deltas):
        assert(len(deltas) == 0)
        sidx = [s.idx for s in sums]
        oidx = [o.idx for o in operators]
        tidx = []
        for t in tensors:
            tidx += t.indices
        self.uidx = set(sidx + oidx + tidx)
        self.Is = []
        for idx in self.uidx:
            summed = True if idx in sidx else False
            os = []
            ts = []
            for i,oi in enumerate(oidx):
                if oi == idx:
                    os.append(i)
            for j,t in enumerate(tensors):
                for i,ti in enumerate(t.indices):
                    if ti == idx:
                        ts.append((t,i))
            self.Is.append(TermMap.AbIdx(idx, ts, os, summed))

    def __eq__(self, other):
        if len(self.Is) != len(other.Is): return False
        # loop over unique indices
        oidxs = []
        for I in self.Is:
            # find equivalent index if it exists
            found = False
            for i,J in enumerate(other.Is):
                if I == J:
                    found = True
                    if i in oidxs:
                        return False
                    else:
                        oidxs.append(i)
                    break
            if not found: return False
        return True

class Term(object):
    def __init__(self, scalar, sums, tensors, operators, deltas):
        self.scalar = scalar
        self.sums = sums
        self.tensors = tensors
        self.operators = operators
        self.deltas = deltas

    def resolve(self):
        dnew = []

        # get unique deltas
        self.deltas = list(set(self.deltas))
        
        # loop over deltas
        for dd in self.deltas:
            i2 = dd.i2
            i1 = dd.i1
            assert(i1.space == i2.space)

            ## Cases ##
            # 0 sums over neither index
            # 1 sums over 1st index
            # 2 sums over 2nd index
            # 3 sums over both indices
            case = 0

            dindx = []
            for i in range(len(self.sums)):
                idx = self.sums[i].idx
                if i2 == idx:
                    dindx.append(i)
                    case = 3 if case == 1 else 2
                    break
                elif i1 == idx:
                    dindx.append(i)
                    case = 3 if case == 2 else 1
                    break;

            if len(dindx) > 0:
                dindx.sort()
                dindx = dindx[::-1]
                for j in dindx:
                    del self.sums[j]

            for tt in self.tensors:
                for k in range(len(tt.indices)):
                    if case == 1:
                        if tt.indices[k] == i1:
                            tt.indices[k] = i2
                    else:
                        if tt.indices[k] == i2:
                            tt.indices[k] = i1

            for oo in self.operators:
                if case == 1:
                    if oo.index == i1:
                        oo.index = i2
                else:
                    if oo.index == i2:
                        oo.index = i1


            if case == 0 and i1 != i2:
                dnew.append(dd)

        self.deltas = dnew

    def __repr__(self):
        s = str(self.scalar)
        for ss in self.sums:
            s = s + str(ss)
        for dd in self.deltas:
            s = s + str(dd)
        for tt in self.tensors:
            s = s + str(tt)
        for oo in self.operators:
            s = s + str(oo)
        return s


    def __mul__(self, other):
        if isinstance(other, Number):
            new = deepcopy(self)
            new.scalar *= other
            return new
        elif isinstance(other, Term):
            scalar = self.scalar*other.scalar
            sums = self.sums + other.sums
            tensors = self.tensors + other.tensors
            operators = self.operators + other.operators
            deltas = self.deltas + other.deltas
            return Term(scalar, sums, tensors, operators, deltas)
        else:
            return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, Number):
            new = deepcopy(self)
            new.scalar *= other
            return new
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, Term):
            return self.scalar == other.scalar \
                    and set(self.sums) == set(other.sums) \
                    and set(self.tensors) == set(other.tensors) \
                    and self.operators == other.operators \
                    and set(self.deltas) == set(other.deltas)
        else:
            return NotImplemented

    def __neq__(self, other):
        return not self.__eq__(other)

    def match(self, other):
        if isinstance(other, Term):
            if len(self.deltas) > 0 or len(other.deltas) > 0:
                raise Exception("Cannot match terms with unresolved deltas!")
            TM1 = TermMap(self.sums, self.tensors, self.operators, self.deltas)
            TM2 = TermMap(other.sums, other.tensors, other.operators, other.deltas)
            return TM1 == TM2
        else:
            return NotImplemented

    def pmatch(self, other):
        if isinstance(other, Term):
            tlists = [t.sym.tlist for t in other.tensors]
            TM1 = TermMap(self.sums, self.tensors, self.operators, self.deltas)
            for xs in product(*tlists):
                sign = 1.0
                for x in xs: sign *= x[1]
                newtensors = [permute(t,x[0]) for t,x in zip(other.tensors, xs)]
                TM2 = TermMap(other.sums, newtensors, other.operators, other.deltas)
                if TM1 == TM2: return sign
            return None
        else: return NotImplemented

class Expression(object):
    def __init__(self, terms):
        self.terms = terms
        self.tthresh = 1e-15

    def resolve(self):
        for i in range(len(self.terms)):
            self.terms[i].resolve()

        # get rid of terms that are zero
        self.terms = filter(lambda x: abs(x.scalar) > self.tthresh, self.terms)

        # compress all symmetry-related terms
        newterms = []
        while self.terms:
            t1 = self.terms[0]
            tm = filter(lambda x: x[1] is not None,[(t,t1.pmatch(t)) for t in self.terms[1:]])
            s = t1.scalar
            for t in tm: s += t[1]*t[0].scalar
            t1.scalar = s
            newterms.append(deepcopy(t1))
            tm = [t[0] for t in tm]
            self.terms = filter(lambda x: x not in tm, self.terms[1:])
        self.terms = newterms

    def __repr__(self):
        s = str()
        for t in self.terms:
           s = s + str(t)
           s = s + " + "

        return s[:-2]

    def __mul__(self, other):
        pass
