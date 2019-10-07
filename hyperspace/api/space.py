from abc import ABCMeta, abstractmethod


class HyperSpace(object):
    """ Base class for all HyperSpaces """
    __metaclass__ = ABCMeta

    def _divide_space(self):
        raise NotImplementedError

    @abstractmethod
    def get_hyperspace(self):
        raise NotImplementedError