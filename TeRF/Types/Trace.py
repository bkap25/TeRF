from heapq import heappush, heappop
from itertools import chain
from numpy import exp
from numpy.random import choice

from TeRF.Miscellaneous import log, log1of


class TraceComplete(Exception):
    pass


class Trace(object):
    """An evaluation trace for a TRS term"""
    def __init__(self, trs, term, p_observe=0.2, max_steps=1000, min_p=1e-6):
        root = TraceState(term)
        self.unobserved = heappush([], root)
        self.root = root
        self.trs = trs
        self.p_observe = p_observe
        self.max_steps = max_steps
        self.min_p = min_p
        self.steps = 0

    def all_outcomes(self):
        return self.root.leaves()

    def sample(self):
        outcomes = self.all_outcomes()
        ps = [exp(o.log_p) for o in outcomes]
        return choice(outcomes, p=ps)

    def run(self):
        while True:
            try:
                self.step()
            except TraceComplete:
                return self

    def step(self):
        try:
            state = heappop(self.unobserved)
        except IndexError:
            raise TraceComplete('step: no further steps can be taken')

        if state.log_p < log(self.min_p) or self.steps > self.max_steps:
            raise TraceComplete('step: no further steps can be taken')

        rewrites = state.term.single_rewrite(self.trs, type='all')

        if rewrites == [state.term] or rewrites == []:
            nf = TraceState(state.term,
                            log_p=state.log_p,
                            parent=state,
                            state='normal')
            state.children.append(nf)

        observed = TraceState(state.term,
                              log_p=(log(self.p_observe) + state.log_p),
                              parent=state,
                              state='observed')
        state.children.append(observed)

        for term in rewrites:
            unobserved = TraceState(term,
                                    log_p=(log1of(rewrites) + state.log_p),
                                    parent=state,
                                    state='unobserved')
            heappush(self.unobserved, unobserved)
            state.children.append(unobserved)

    def rewrites_to(self, term):
        # NOTE: we only use tree equality and don't consider tree edit distance
        self.run()
        return sum(l.log_p for l in self.leaves()
                   if l == term and (l.state in ['normal', 'observed']))


class TraceState(object):
    """A single state in a Trace"""
    def __init__(self, term, log_p=0.0, parent=None, state='start'):
        self.term = term
        self.log_p = log_p
        self.parent = parent
        self.state = state
        self.children = []

    def leaves(self):
        if self.children != []:
            return list(chain(*[c.leaves() for c in self.children]))
        return [self]

    def __cmp__(self, other):
        return self.log_p < other.log_p
