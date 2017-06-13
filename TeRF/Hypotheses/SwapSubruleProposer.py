from copy import deepcopy
from itertools import permutations
from LOTlib.Hypotheses.Proposers.Proposer import (Proposer,
                                                  ProposalFailedException)
from numpy import log, inf
from numpy.random import choice
from random import sample
from scipy.misc import logsumexp

from TeRF.Hypotheses.TRSProposerUtilities import make_a_rule
from TeRF.Miscellaneous import find_difference, log1of
from TeRF.TRS import App


def can_be_swapped(rule, swap):
    return ((swap == 'rhs' or len(rule.lhs.body) > 1) and
            (swap == 'lhs' or (hasattr(rule.rhs, 'body') and
                               len(rule.rhs.body) > 1)))


def unique_shuffle(xs):
    if len(set(xs)) == 1:
        return None
    while True:
        result = sample(xs, len(xs))
        if xs != result:
            return result


def propose_value(value, **kwargs):
    new_value = deepcopy(value)
    swap = choice(['lhs', 'rhs', 'both'])
    idxs = [i for i, r in enumerate(value.rules) if can_be_swapped(r, swap)]
    try:
        idx = choice(idxs)
        rule = value.rules[idx]
    except ValueError:
        raise ProposalFailedException('SwapSubruleProposer: no TRS rules')
    try:
        new_lhs = App(rule.lhs.head, unique_shuffle(rule.lhs.body)) \
                  if swap != 'rhs' else rule.lhs
        new_rhs = App(rule.rhs.head, unique_shuffle(rule.rhs.body)) \
                  if swap != 'lhs' else rule.rhs
    except TypeError:
        raise ProposalFailedException('SwapSubruleProposer: cannot swap')

    new_rule = make_a_rule(new_lhs, new_rhs)
    # print 'ssp: changing', rule, 'to', new_rule
    new_value.rules[idx] = new_rule
    return new_value


def log_p_is_a_swap(old, new):
    try:
        if old.head == new.head and len(old.body) == len(new.body) > 1:
            options = [x for x in list(permutations(old.body))
                       if x != tuple(old.body)]
            return log(options.count(tuple(new.body))) + log1of(options)
    except (AttributeError, ValueError):
        pass
    return log(0)


def give_proposal_log_p(old, new, **kwargs):
    if old.variables == new.variables and old.operators == new.operators:
        old_rule, new_rule = find_difference(old.rules, new.rules)
        try:
            p_method = -log(3)
            p_swap_lhs = log_p_is_a_swap(old_rule.lhs, new_rule.lhs)
            p_swap_rhs = log_p_is_a_swap(old_rule.rhs, new_rule.rhs)

            p_lhs = log(0)
            if p_swap_rhs == -inf:
                rules = [r for r in old.rules if len(r.lhs.body) > 1]
                p_rule = log1of(rules)
                p_lhs = p_method + p_rule + p_swap_lhs

            p_rhs = log(0)
            if p_swap_lhs == -inf:
                rhs_rules = [r for r in old.rules
                             if hasattr(r.rhs, 'body') and len(r.rhs.body) > 1]
                p_rhs_rule = log1of(rhs_rules)
                p_rhs = p_method + p_rhs_rule + p_swap_rhs

            both_rules = [r for r in old.rules if len(r.lhs.body) > 1 and
                          hasattr(r.rhs, 'body') and len(r.rhs.body) > 1]
            p_both_rule = log1of(both_rules)
            p_both = p_method + p_both_rule + p_swap_lhs + p_swap_rhs

            return logsumexp([p_lhs, p_rhs, p_both])
        except AttributeError:
            pass
    return log(0)


class SwapSubruleProposer(Proposer):
    """
    Proposer for modifying a rule by swapping the children of its trees
    (NON-ERGODIC FOR TRSs)

    Given a TRS (S,R U {x}), give a new TRS (S, R U {x'}), where x is a rule,
    l -> r,  and x' is l' -> r'. l' has the same head and children as l, but
    the order of the children is permuted. The same is true for r' and r.
    """
    def __init__(self, **kwargs):
        """Create a SwapSubruleProposer"""
        self.propose_value = propose_value
        self.give_proposal_log_p = give_proposal_log_p
        super(SwapSubruleProposer, self).__init__(**kwargs)
