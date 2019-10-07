import warnings
from math import floor, ceil

from skopt.space import Integer
from hyperspace.api.space import HyperSpace


class HyperInteger(HyperSpace, Integer):
    """ Hyperspace for integers

    Args:
        low: [int]
            Lower bound (inclusive).
    
        high: [int]
            Upper bound (inclusive).
        
        transform: ["identity", "normalize", optional]:
            The following transformations are supported.
            - "identity", (default) the transformed space is the same as the
               original space.
            - "normalize", the transformed space is scaled to be between
               0 and 1.
    
        name: [str or None]:
            Name associated with dimension, e.g., "number of trees".
    
        overlap: [float, default=0.25]:
            Amount of overlap between between each hyperspace.
            - Should be between 0 and 1.
            - If overlap=0, there are no shared values between the hyperspaces.
            - If overlap=1, two copies of the search space is made.
    """
    def __init__(self, low, high, transform=None, overlap=0.25, name=None):
        super().__init__(low, high, transform)
        self.transform = transform
        self.overlap = overlap
        self.name = name
        self.space0_low = None
        self.space0_high = None
        self.space1_low = None
        self.space1_high = None
        self._divide_space()

        if high <= low:
            raise ValueError("the lower bound {} has to be less than the"
                             " upper bound {}".format(low, high))

    def __repr__(self):
        """
        Representation of the Integer HyperSpace. Useful when checking the hyperspace bounds.
        """
        return "HyperInteger(low={}, high={})\n" \
               "HyperInteger(low={}, high={})".format(self.space0_low, self.space0_high,
                                                      self.space1_low, self.space1_high)

    def _divide_space(self):
        """
        Divides the original search space into overlapping subspaces.
        """
        subinterval_length = abs(self.high - self.low)/2
        overlap_length = subinterval_length * self.overlap

        if subinterval_length < 1:
            warnings.warn("Each hyperspace contains a single value.")

        # Define the bounds of the hyperspaces.
        # Mind the floor and ceiling: spaces defined with short ranges can get interesting.
        self.space0_low = self.low
        self.space0_high = floor(self.space0_low + subinterval_length + overlap_length)
        self.space1_low = ceil(self.high - (subinterval_length + overlap_length))
        self.space1_high = self.high

    def get_hyperspace(self):
        """
        Create integer HyperSpaces.
        """
        return Integer(self.space0_low, self.space0_high), \
               Integer(self.space1_low, self.space1_high)