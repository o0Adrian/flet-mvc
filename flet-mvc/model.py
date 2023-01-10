"""
Data decorator. Originally created to be used in every method of the model class
it will convert the method to a datapoint/node that can be set and reset.

Next feature: It will allow using a reference datapoints automatically when sent in
the "ref" parameter of a Flet Control.
"""

__all__ = [
    'data'
]

class _Null:
    """ Null class that will be used when the datapoint is still empty """
    def __bool__(self):
        return False

    def __repr__(self):
        return 'Null'

NULL = _Null()


class data:
    """
    data decorator
    Converts a class method (intended for the Model class) to a datapoint
    """
    def __init__(self, f):
        self.func = f
        self.current_value = NULL
    
    
    def __call__(self):
        """
        Return current value when datapoint is called
        e.g. print(self.model.fruit()) -> 'Apple'
        """
        return self.current_value
        
    def __get__(self, instance, owner):
        """
        Return value when accessing the datapoint instance.
        This will return the self instance of the datapoint in order to
        access the other methods of the datapoint.
        """
        self.model_instance = instance
        self.model_class = self.model_instance.__class__
        
        if self.current_value is NULL:
            self.current_value = self.func(instance)
            
        return self
        
    def set_value(self, x):
        """
        Set value method
        e.g.
        self.model.fruit.set_value('Pear')
        print(model.fruit()) -> 'Pear'
        """
        self.current_value = x
    
    def reset(self):
        """
        Reset methods - Resets a datapoint to their initial value
        e.g.
        print(self.model.fruit()) -> 'Apple'
        self.model.fruit.set_value('Pear')
        print(self.model.fruit()) -> 'Pear'
        self.model.fruit.reset()
        print(model.fruit()) -> 'Apple'
        """
        self.current_value = self.func(self.model_instance)

    # TODO: Here the current setter and getter will be defined in order to save a ref object in a datapoint     
    
    # Magic Methods so the datapoint can be used as any other data type
    def __lt__(self, other):
        return self.current_value < other
    
    def __le__(self, other):
        return self.current_value <= other
    
    def __eq__(self, other):
        return self.current_value == other
    
    def __ne__(self, other):
        return self.current_value != other
    
    def __gt__(self, other):
        return self.current_value > other
    
    def __ge__(self, other):
        return self.current_value >= other
    
    def __len__(self):
        return len(self.current_value)
    
    def __add__(self, other):
        return self.current_value + other
    
    def __sub__(self, other):
        return self.current_value - other
    
    def __div__(self, other):
        return self.current_value/other
    
    def __mul__(self, other):
        return self.current_value * other
    
    def __neg__(self):
        return -self.current_value
    
    def __pos__(self):
        return +self.current_value
    
    def __abs__(self):
        return abs(self.current_value)
    
    def __invert__(self):
        return ~self.current_value