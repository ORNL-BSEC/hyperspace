from skopt.space import Categorical
from hyperspace.api.space import HyperSpace


class _Ellipsis:
    def __repr__(self):
        return '...'


class HyperCategorical(HyperSpace, Categorical):
    """ Search space dimension that can take on categorical values.

    Args: 
        categories: [list, shape=(n_categories,)]:
            Sequence of possible categories.

        prior: [list, shape=(categories,), default=None]:
            Prior probabilities for each category. By default all categories
            are equally likely.

        transform: ["onehot", "identity", default="onehot"] :
            - "identity", the transformed space is the same as the original
              space.
            - "onehot", the transformed space is a one-hot encoded
              representation of the original space.

        name: [str or None]:
            Name associated with dimension, e.g., "colors".
    """
    def __init__(self, categories, prior=None, transform=None, overlap=0.25, name=None):
        super().__init__(categories, prior, transform)
        self.categories = categories
        self.prior = prior
        self.transform = transform
        self.overlap = overlap
        self.name = name
        self.cat_low = None
        self.cat_high = None
        self._divide_space()

    def __repr__(self):
        if len(self.categories) > 7:
            cats = self.categories[:3] + [_Ellipsis()] + self.categories[-3:]
        else:
            cats = self.categories

        if self.prior is not None and len(self.prior) > 7:
            prior = self.prior[:3] + [_Ellipsis()] + self.prior[-3:]
        else:
            prior = self.prior

        return "Categorical(categories={}, prior={})".format(cats, prior)

    def _divide_space(self):
        """
        Divides the original search space into overlapping subspaces.
        """
        subinterval_length = floor(len(self.categories)/2)
        overlap_length = ceil(subinterval_length * self.overlap)

        if subinterval_length < 1:
            warnings.warn("Each hyperspace contains a single value.")

        cat_low = self.categories[0:subinterval_length + overlap_length]
        self.cat_low = tuple(cat_low)
        cat_reverse = self.categories[::-1]
        cat_high = cat_reverse[0:subinterval_length + overlap_length]
        self.cat_high = tuple(cat_high[::-1])

    def get_hyperspace(self):
        """
        Create integer HyperSpaces.
        """
        return Categorical(self.cat_low, self.prior, self.transform), \
               Categorical(self.cat_high, self.prior, self.transform)