import collections as C

# from numpy import exp
# from numpy.random import choice, binomial
# from itertools import repeat, izip
# from scipy.misc import logsumexp
# from scipy.stats import geom
# from copy import copy

# from TeRF.Miscellaneous import log, log1of, gift, list_possible_gifts
# import TeRF.Types.Application as A
# import TeRF.Types.Operator as O
# import TeRF.Types.Variable as V
# import TeRF.Types.Rule as R


class SignatureError(Exception):
    pass


class Signature(C.MutableSet):
    def __init__(self, elements=None, parent=None):
        self.parent = parent
        self._elements = set(([] if elements is None else elements))

    @property
    def variables(self):
        return {v for v in self._elements if not hasattr(v, 'arity')}

    @property
    def operators(self):
        return {o for o in self._elements if hasattr(o, 'arity')}

    @property
    def terminals(self):
        return {s for s in self._elements if s.terminal}

    def __contains__(self, item):
        return (item in self._elements)

    def __len__(self):
        return len(self._elements)

    def __iter__(self):
        for x in self._elements:
            yield x

    def add(self, item):
        self._elements.add(item)

    def discard(self, item):
        self._elements.discard(item)
        if self.parent is not None:
            for rule in self.parent:
                if item in rule.signature:
                    del self.parent[rule]

    def replace_vars(self, new_vars):
        self._elements = self.operators | new_vars
        return self

#     def possible_roots(self, must_haves):
#         if len(must_haves) == 0:
#             return list(self)
#         if len(must_haves) == 1:
#             return [s for s in self
#                     if s in must_haves or getattr(s, 'arity', 0) > 0]
#         return [s for s in self if getattr(s, 'arity', 0) > 1]
# 
#     def sample_head(self, invent=True):
#         head = choice(list(self) + (['new var'] if invent else []))
#         if head == 'new var':
#             head = V.Var()
#         return head
# 
#     def log_p_head(self, head, invent=True):
#         if head in self or (invent and hasattr(head, 'identity')):
#             return -log(len(self) + (1 if invent else 0))
#         return log(0)
# 
#     def sample_term(self, invent=True):
#         """
#         sample a TRS term given a TRS signature
# 
#         Args:
#           signature: an iterable containing TRS Operators and Variables
#           invent: a boolean marking whether to invent variables
#         Returns:
#           a TRS term sampled from the grammar defined by signature
#         """
#         if self.leaves() == [] and not invent:
#             raise SignatureError('sample_term: no terminals!')
#         sig = copy(self)
#         head = sig.sample_head(invent)
#         sig |= {head}
#         try:
#             body = []
#             for _ in repeat(None, head.arity):
#                 t = sig.sample_term(invent)
#                 body.append(t)
#                 sig |= t.variables()
#             return A.App(head, body)
#         except AttributeError:
#             return head
# 
#     def log_p(self, term, invent=True):
#         """
#         compute the probability of sampling a term given a signature
# 
#         Args:
#           term: a TRS term
#           signature: an iterable containing TRS Operators and Variables
#           invent: a boolean marking whether to invent variables
#         Returns:
#           a float representing log(p(term | signature))
#         """
#         sig = copy(self)
#         p = sig.log_p_head(term.give_head(), invent)
#         sig |= ({term.give_head()} if invent else set())
#         try:
#             for t in term.body:
#                 p += sig.log_p(t, invent)
#                 sig |= (t.variables() if invent else set())
#         except AttributeError:
#             pass
#         return p
# 
#     def sample_term_t(self, term, p_r, invent=True):
#         """
#         generate a term conditioned on an existing term
# 
#         Args:
#           signature: an iterable of TRS Operators and Variables
#           term: a TRS term
#           p_r: a float giving the node-wise probability of regeneration
#         Returns:
#           a TRS term
#         """
#         sig = copy(self)
#         if binomial(1, p_r):
#             return sig.sample_term(invent)
#         try:
#             body = []
#             for t in term.body:
#                 new_t = sig.sample_term_t(t, p_r, invent)
#                 body.append(new_t)
#                 sig |= new_t.variables()
#                 return A.App(term.head, body)
#         except AttributeError:
#             return copy(term)
# 
#     def log_p_t(self, new, old, p_r, invent=True):
#         """
#         compute the probability of sampling a term given a signature and term
# 
#         Args:
#           new: a TRS term
#           signature: an iterable of TRS Operators and Variables
#           old: the TRS term upon which new was conditioned during sampling
#           p_r: a float giving the node-wise probability of regeneration
#         Returns:
#           a float representing log(p(new | signature, old))
#         """
#         if new.give_head() == old.give_head():
#             p_make_head = log(p_r) + self.log_p(new, invent)
#             p_keep_head = log(1-p_r)
#             try:
#                 for tn, to in izip(new.body, old.body):
#                     p_keep_head += self.log_p_t(tn, to, p_r, invent)
#                     self |= (tn.variables() if invent else set())
#             except AttributeError:
#                 pass
#             return logsumexp([p_keep_head, p_make_head])
#         return log(p_r) + self.log_p(new, invent)
# 
#     def sample_term_c(self, constraints, invent=True):
#         """
#         generate a term conditioned on a set of required symbols
# 
#         Args:
#           signature: an iterable of TRS Operators and Variables
#           constraints: an iterable subset of signature that must appear in term
#           invent: a boolean marking whether to invent variables
#         Returns:
#           a TRS term
#         Raises:
#           SignatureError: raised when the signature or constraints are invalid
#         """
#         if self.leaves() == [] and not invent:
#             raise SignatureError('sample_term: no terminals!')
#         sig = copy(self)
#         if not set(sig) >= set(constraints):
#             raise SignatureError('sample_term_c: invalid constraints')
# 
#         head = sig.possible_roots(constraints).sample_head(
#             invent and len(constraints) == 0)
#         sig |= {head}
# 
#         try:
#             constraint_assignments = gift(set(constraints)-{head}, head.arity)
#             body = []
#             for cs in constraint_assignments:
#                 t = sig.sample_term_c(cs)
#                 sig |= t.variables()
#                 body.append(t)
#                 return A.App(head, body)
#         except AttributeError:
#             return head
# 
#     def log_p_c(self, term, constraints, invent=True):
#         """
#         compute the probability of sampling a term given a signature and term
# 
#         Args:
#           term: a TRS term
#           signature: an iterable of TRS Operators and Variables
#           constraints: an iterable subset of signature that must appear in term
#         Returns:
#           a float representing log(p(term | signature, constraints))
#         """
#         if not self >= set(constraints):
#             return log(0)
# 
#         p = self.possible_roots(constraints).log_p_head(term.give_head(), invent)
#         self |= ({term.give_head()} if invent else set())
# 
#         try:
#             who_has_what = [[(c if c in (t.variables() | t.operators())
#                               else None)
#                              for c in set(constraints)-{term.give_head()}]
#                             for t in term.body]
#             gifts = list_possible_gifts(who_has_what)
#             ps_gifts = list(repeat(log1of(gifts), len(gifts)))
#             for i, g in enumerate(gifts):
#                 new_sig = copy(self)
#                 for t, cs in izip(term.body, g):
#                     ps_gifts[i] += new_sig.log_p_c(t, cs)
#                     new_sig |= (t.variables() if invent else set())
#                     p += logsumexp(ps_gifts)
#         except AttributeError:
#             pass
#         return p
# 
#     def sample_term_tc(self, term, p_r, constraints, invent=True):
#         """
#         generate a term conditioned on a term and a set of required symbols
# 
#         Args:
#           signature: an iterable of TRS Operators and Variables
#           term: a TRS term
#           p_r: a float giving the node-wise probability of regeneration
#           constraints: an iterable subset of signature that must appear in term
#         Returns:
#           a TRS term
#         Raises:
#           SignatureError: raised when the signature or constraints are invalid
#         """
#         if not self >= set(constraints):
#             raise SignatureError('sample_term_tc: invalid constraints')
#         h = term.give_head()
#         if binomial(1, p_r) or \
#            (hasattr(h, 'identity') and not set(constraints) <= {h}) or \
#            (hasattr(h, 'arity') and len(constraints) == 1 and h.arity < 1) or \
#            (hasattr(h, 'arity') and len(constraints) > 1 and h.arity < 2):
#             return self.sample_term_c(constraints, invent)
#         try:
#             assignments = gift(set(constraints)-{h}, h.arity)
#             body = []
#             for t, cs in izip(term.body, assignments):
#                 new_t = self.sample_term_tc(t, p_r, cs, invent)
#                 body.append(new_t)
#                 self |= new_t.variables()
#                 return A.App(term.head, body)
#         except AttributeError:
#             return copy(term)
# 
#     def log_p_tc(self, new, old, p_r, constraints, invent=True):
#         """
#         compute the probability of sampling a term given a term and constraints
# 
#         Args:
#           new: a TRS term
#           signature: an iterable of TRS Operators and Variables
#           old: the TRS term on which new is conditioned
#           p_r: a float giving the node-wise probability of regeneration
#           constraints: an iterable subset of signature that must appear in term
#         Returns:
#           a float representing log(p(term | signature, old, constraints))
#         """
#         if (not self >= constraints):
#             return log(0)
# 
#         nh, oh = new.give_head(), old.give_head()
# 
#         if (hasattr(oh, 'identity') and not set(constraints) <= {oh}) or \
#            (getattr(oh, 'arity', 1) < 1 and len(constraints) == 1) or \
#            (getattr(oh, 'arity', 2) < 2 and len(constraints) > 1):
#             return self.log_p_c(new, constraints, invent)
# 
#         p_make_head = log(p_r) + self.log_p_c(new, constraints, invent)
#         if oh == nh:
#             who_has_what = [[c if c in (t.variables() | t.operators()) else None
#                              for c in set(constraints)-{oh}]
#                             for t in new.body]
#             gifts = list_possible_gifts(who_has_what)
#             ps_gifts = list(repeat(log1of(gifts), len(gifts)))
#             for i, g in enumerate(gifts):
#                 new_sig = copy(self)
#                 for n, o, cs in izip(new.body, old.body, g):
#                     ps_gifts[i] += new_sig.log_p_tc(n, o, p_r, cs)
#                     new_sig |= (t.variables() if invent else set())
#                     p_keep_head = log(1-p_r) + logsumexp(ps_gifts)
#                     return logsumexp([p_make_head, p_keep_head])
#                 return p_make_head
# 
#     def sample_rule(self, constraints=None, p_rhs=0.5, invent=True):
#         if constraints is None or len(constraints) == 0:
#             lhs = None
#             while not hasattr(lhs, 'head'):
#                 lhs = self.sample_term(invent)
#             self.replace_vars(lhs.variables())
#             rhs = [self.sample_term(invent=False)
#                    for _ in repeat(None, geom.rvs(p_rhs))]
#             return R.Rule(lhs, rhs)
# 
#         if self >= constraints:
#             op_constraints = {c for c in constraints if hasattr(c, 'arity')}
#             var_constraints = constraints - op_constraints
# 
#             lhs_constraints = var_constraints + {c for c in op_constraints
#                                                  if choice([True, False])}
#             rhs_constraints = constraints - lhs_constraints
# 
#             lhs = self.sample_term_c(lhs_constraints, invent)
#             self.replace_vars(lhs.variables())
#             rhs = [self.sample_term_c(rhs_constraints, invent=False)
#                    for _ in repeat(None, geom.rvs(p_rhs))]
#             return R.Rule(lhs, rhs)
#         raise SignatureError('sample_rule: constraints must be in signature')
#     
#     def log_p_rule(self, rule, p_rhs=0.5, invent=True):
#         p_lhs = self.log_p(rule.lhs, invent=invent)
#         p_n_clauses = geom.logpdf(p=p_rhs, k=len(rule.rhs))
#         self.replace_vars(rule.lhs.variables())
#         p_rhs = sum(self.log_p(rhs[0], invent=False) for rhs in rule.rhs)
#         return p_lhs + p_n_clauses + p_rhs


Sig = Signature

# if __name__ == '__main__':
# 
#     signature = Sig([O.Op('S', 0),
#                      O.Op('K', 0),
#                      O.Op('.', 2)])
# 
#     print 'terms'
#     ts = [signature.sample_term() for _ in range(20)]
#     ps = [signature.log_p(t) for t in ts]
#     for t, p in zip(ts, ps):
#         print '{}, {:f}, {:f}'.format(t.pretty_print(), p, exp(p))
# 
#     print '\nterms | terms'
#     ts2 = [signature.sample_term_t(ts[0], 0.5) for _ in range(20)]
#     ps2 = [signature.log_p_t(t2, ts[0], 0.5) for t2 in ts2]
#     for t, p in zip(ts2, ps2):
#         print '{} -> {}, {:f}, {:f}'.format(ts[0], t.pretty_print(), p, exp(p))
# 
#     print '\nterms | constraints'
#     ts3 = [signature.sample_term_c({O.Op('S', 0), O.Op('K', 0)})
#            for _ in range(20)]
#     ps3 = [signature.log_p_c(t, {O.Op('S', 0), O.Op('K', 0)}) for t in ts3]
#     for t, p in zip(ts3, ps3):
#         print '{}, {:f}, {:f}'.format(t.pretty_print(), p, exp(p))
# 
#     print '\nterms | term, constraints'
#     ts4 = [signature.sample_term_tc(ts[0], 0.2, {O.Op('S', 0), O.Op('K', 0)})
#            for _ in range(20)]
#     ps4 = [signature.log_p_tc(t, ts[0], 0.2, {O.Op('S', 0), O.Op('K', 0)})
#            for t in ts4]
#     for t, p in zip(ts4, ps4):
#         print '{}, {:f}, {:f}'.format(t.pretty_print(), p, exp(p))
# 
