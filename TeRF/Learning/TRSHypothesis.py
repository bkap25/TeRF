import copy
from LOTlib.Hypotheses.Hypothesis import Hypothesis
from LOTlib.Inference.Samplers.StandardSample import standard_sample
from numpy import exp
from numpy.random import choice
from scipy.misc import logsumexp
import time

from TeRF.Learning.GenerativePrior import GenerativePrior
from TeRF.Learning.Likelihood import Likelihood
from TeRF.Learning.TestProposer import TestProposer
from TeRF.Language.parser import load_source
from TeRF.Types.TRS import TRS
from TeRF.Types.Rule import Rule
from TeRF.Types.Application import App


class TRSHypothesis(GenerativePrior, Likelihood, TestProposer, Hypothesis):
    """
    A Hypothesis in the space of Term Rewriting Systems (TRS)

    The args below are TRSHypothesis specific. The Hypothesis baseclass also
    has: value, prior_temperature, likelihood_temperature, & display.

    Args:
      data: a list of Rules to explain
      p_observe: rate of observation (in timesteps)
      p_similar: rate of noisiness in evaluation (in timesteps)
      p_operators: probability of adding a new operator
      p_arity: probability of increasing the arity of an operator
      p_rules: probability of adding a new rule
      p_r: probability of regenerating any given subtree
      proposers: the components of the mixture
      weights: the weights of the mixture components
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(TRSHypothesis, self).__init__(**kwargs)


def fix_ps(log_ps):
    sum_ps = logsumexp(log_ps)
    return [exp(p-sum_ps) for p in log_ps]


def test(n, filename, start_string):
    trs, _ = load_source(filename)

    start = App(trs.signature.find(start_string), [])

    print '# Ground Truth:\n# {}\n#'.format(str(trs).replace('\n', '\n# '))

    def make_data_maker(nChanged=10, nTotal=20):
        def make_data():
            data = TRS()
            temp = copy.deepcopy(trs)
            data.signature = copy.deepcopy(trs.signature)

            for i, rule in enumerate(list(temp.rules())):
                if i > 3:
                    print '# deleting', rule
                    del temp[rule]

            print '#'
            print '# Start symbol:', start.pretty_print()
            lhs_start = time.time()
            trace = start.rewrite(temp, max_steps=11, type='all', trace=True)
            lhs_end = time.time()
            states = trace.root.leaves(states=['normal'])
            terms = [s.term for s in states]
            log_ps = [s.log_p*0.5 for s in states]
            ps = fix_ps(log_ps)
            print '# {:d} LHSs generated in {:.2f}s'.format(
                len(terms),
                lhs_end-lhs_start)

            rhs_start = time.time()
            tries = 0
            while data.num_rules() < nTotal:
                tries += 1
                lhs = choice(terms, p=ps)
                rhs = lhs.rewrite(trs, max_steps=7, type='one')
                rule = Rule(lhs, rhs)
                if (rule not in trs) and \
                   ((data.num_rules() < nChanged and lhs != rhs) or
                   (data.num_rules() >= nChanged) and (lhs == rhs)):
                    data[len(data)] = rule
            rhs_end = time.time()
            print '# {:d} rules selected in {:.2f}s and {:d} tries'.format(
                data.num_rules(),
                rhs_end-rhs_start,
                tries)
            return list(data.rules())

        return make_data

    def make_hypothesis(data):
        hyp_trs = TRS()
        for rule in data:
            for op in rule.operators:
                hyp_trs.signature.add(op)
        return TRSHypothesis(value=hyp_trs,
                             data=data,
                             privileged_ops={s for s in hyp_trs.signature},
                             p_observe=0.1,
                             p_similar=0.99,
                             p_operators=0.5,
                             p_arity=0.9,
                             p_rules=0.5,
                             start=start,
                             p_r=0.3)

    hyps_start = time.time()
    hyps = standard_sample(make_hypothesis,
                           make_data_maker(nChanged=20, nTotal=40),
                           save_top=None, show_skip=0, trace=False, N=10,
                           steps=n, clean=False, likelihood_temperature=0.5)
    hyps_end = time.time()

    print '\n\n# The best hypotheses of', n, 'samples:'
    for hyp in hyps.get_all(sorted=True):
        print '#'
        print '#', hyp.prior, hyp.likelihood, hyp.posterior_score
        print '# ' + str(hyp).replace('\n', '\n# ')

    print 'samples were generated in {:.2f}s'.format(hyps_end-hyps_start)


if __name__ == '__main__':
    import sys
    n = 1600 if len(sys.argv) < 2 else int(sys.argv[1])
    default_filename = 'library/simple_tree_manipulations/001.terf'
    filename = default_filename if len(sys.argv) < 3 else sys.argv[2]
    start = 'tree' if len(sys.argv) < 4 else sys.argv[3]
    test(n, filename, start)
