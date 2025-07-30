class Detector:
    """
    A class with functions to help with certain things that
    turtle is not able to do alone, like color detection at
    a certain pixel
    """

    def __init__(self, turtle):
        self.turtle = turtle

    def marked(self) -> bool:
        """
        A function to see if a certain pixel is marked

        Args:
            x (int): the x coordinate of the pixel
            y (int): the y coordinate of the pixel
        Returns:
            bool: True if the pixel is marked
        """
        x, y = self.turtle.pos()

        # tkinter canvas idiosyncracy
        y = -y

        canvas = self.turtle.getcanvas()
        ids = canvas.find_overlapping(x, y, x, y)

        # Returns true if an object was found at this pixel - turtle is counted as an object
        if len(ids) > 0:
            index = None
            # Gets the topmost object that isn't the turtle (which always has id 3 as far as I know)
            for id in ids[::-1]:
                if id > 3:
                    index = id
                    break
            if index is None:
                return False
        else:
            return False
        
        color = canvas.itemcget(index, "fill")

        if color == self.turtle.color()[1]:
            return True
        
        return False

