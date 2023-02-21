from functools import reduce
from random import random


class NodeScores:
    def __init__(self, size=3, equal_threshold=1):
        self.scores = [None for _ in range(size + 1)]
        self.scores[size] = random()
        self.size = size
        self.equal_threshold = equal_threshold if equal_threshold >= 1 else 1 / equal_threshold

    def __repr__(self):
        return str(self.scores)

    def set_scores(self, scores):
        self.scores = scores
        return self

    def __mul__(self, other):
        return self

    def __lt__(self, other):
        for i in range(self.size):
            if self.scores[i] * self.equal_threshold < other.scores[i]:
                return True
            if self.scores[i] > other.scores[i] * self.equal_threshold:
                return False
        return self.scores[self.size] < other.scores[self.size]

    def __gt__(self, other):
        for i in range(self.size):
            if self.scores[i] > other.scores[i] * self.equal_threshold:
                return True
            if self.scores[i] * self.equal_threshold < other.scores[i]:
                return False
        return self.scores[self.size] > other.scores[self.size]

    def __eq__(self, other):
        for i in range(self.size):
            if self.scores[i] * self.equal_threshold < other.scores[i] or \
                    self.scores[i] > other.scores[i] * self.equal_threshold:
                return False
        return self.scores[self.size] == other.scores[self.size]


class flist(list):
    def copy(self):
        return flist(super(flist, self).copy())

    def reverse(self):
        super(flist, self).reverse()
        return self


class clist(flist):
    def copy(self):
        return clist(super(clist, self).copy())

    def reverse(self):
        length = len(self) // 2
        temp = flist([[self[2 * i], self[2 * i + 1]] for i in range(length)])
        return clist(reduce(list.__add__, temp.reverse()))


class tlist(flist):
    def index(self, elem):
        return tuple(zip(*self))[0].index(elem)
