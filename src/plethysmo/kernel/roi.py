class ROI:
    """This class defines a Region Of Interest
    """

    def __init__(self, lower_corner, upper_corner):
        """Constructor
        """

        self._lower_corner = lower_corner

        self._upper_corner = upper_corner

    @property
    def lower_corner(self):
        """Getter for _lower_corner attribute.
        """

        return self._lower_corner

    @property
    def upper_corner(self):
        """Getter for _upper_corner attribute.
        """

        return self._upper_corner

    @property
    def x_extend(self):
        """Return the extent of the ROI along X axis.
        """

        return self._upper_corner[0] - self._lower_corner[0]

    @property
    def xy_extend(self):
        """Return the extent of the ROI along X and Y axis.
        """

        x_extend = self.x_extend
        y_extend = self.y_extend

        return (x_extend,y_extend)

    @property
    def y_extend(self):
        """Return the extent of the ROI along Y axis.
        """

        return self._upper_corner[1] - self._lower_corner[1]
        
