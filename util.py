from functools import reduce

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