import random


class ValuationSampler:

    def __init__(self, function):
        self.function = function

    def sample(self, auction_id):
        return self.function(auction_id)


ALL_SAMPLERS = {
    "constant": ValuationSampler(lambda x: 10 + x),
    "uniform": ValuationSampler(lambda x: random.randrange(7 + x, 13 + x)),
    "binomial": ValuationSampler(lambda x: sum(random.random() < 0.5 for _ in range(20 + 2 * x))),
}
