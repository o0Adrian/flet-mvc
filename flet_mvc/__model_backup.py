"""
Data decorator. Originally created to be used in every method of the model class
it will convert the method to a datapoint/node that can be set and reset.

It will allows using a reference datapoints automatically when sent in
the "ref" parameter of a Flet Control.

Next Feature: Dependency between datapoints (currently we can't set default values
with other datapoints and make them change automatically when the parent changes).
Send/Receive decorators.
"""

import logging
from typing import Any, Optional, Callable, List


logging.basicConfig(level=logging.WARNING)

__all__ = [
    'data',
    'FletModel'
]


class FletModel():
    def __init__(self, **kwargs):
        self.ref_objs = []


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

    def __init__(self, f: Callable[..., Any]):
        self.func = f
        self.datapoint_name: str = f.__name__
        self.__value: Optional[Any] = NULL
        self.__new_default: Optional[Any] = NULL

        # Ref obj
        self.__current: Optional[Any] = NULL
        self.ref_attr: Optional[str] = NULL
        self.ref_type: Optional[Any] = NULL
        self.is_ref_obj: bool = False
        self.is_container_ref: bool = False

    def __call__(self) -> Any:
        """
        Return current value when datapoint is called
        e.g. print(self.model.fruit()) -> 'Apple'
        """
        if self.is_ref_obj:
            return getattr(self.current, self.ref_attr)
        else:
            return self.value

    def __get__(self, instance, owner):
        """
        Return value when accessing the datapoint instance.
        This will return the self instance of the datapoint in order to
        access the other methods of the datapoint.
        """
        self.model_instance = instance
        self.model_class = self.model_instance.__class__

        if not hasattr(self.model_instance, "ref_objs"):
            super(self.model_class, self.model_instance).__init__()

        if self.value is NULL:
            self.value = self.func(instance)

        return self

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        print("yoo")
        # triggered by __get__ when setting the initial value
        # triggered by reset
        # triggered by set_value
        self.__value = value

        if self.is_ref_obj:
            # this should  automatically modify content and controls properties of the control instance.
            setattr(self.current, self.ref_attr, value)

    @property
    def current(self):
        """
        If the datapoint is a ref object, and want to access the Flet control for any other propeties
        use this property, it works as a Ref Object.
        """
        return self.__current

    @current.setter
    def current(self, current):
        """ First triggered when adding to ref property of a control, this is how we will set the datapoint to a ref obj"""
        self.__current = current
        potential_attributes = {
            'value': None,  # accept any value
            'label': str,
            'src': str,
            'text': str,
            'name': str,
            'title': str,
            'controls': list,
            'content': list,
            'figure': None  # accept any value
        }
        for attr, attr_type in potential_attributes.items():
            if hasattr(current.__class__, attr):
                setattr(self.__current, attr, self.value)
                self.ref_attr = attr
                self.ref_type = attr_type
                break
        else:
            logging.warning(
                f"No default value was set to Flet control '{self.__current}', the datapoint '{self.datapoint_name}' will behave as a normal RefObj"
            )

        self.is_container_ref = self.ref_attr in ['controls', 'content', 'figure']
        self.model_instance.ref_objs.append(self)
        self.is_ref_obj = True

    def set_value(self, x: Any) -> None:
        """
        Set value method
        e.g.
        self.model.fruit.set_value('Pear')
        print(model.fruit()) -> 'Pear'
        """
        # set control value
        if self.current is not NULL:
            if self.ref_type is None or isinstance(x, self.ref_type):
                self.current.value = x
            else:
                raise TypeError(
                    f"Provided value '{x}' does not match expected type '{self.ref_type}' for '{self.__current}'"
                )

        # set data value
        self.value = x

    def reset(self) -> None:
        """
        Reset methods - Resets a datapoint to their initial value
        e.g.
        print(self.model.fruit()) -> 'Apple'
        self.model.fruit.set_value('Pear')
        print(self.model.fruit()) -> 'Pear'
        self.model.fruit.reset()
        print(model.fruit()) -> 'Apple'
        """
        self.value = self.func(self.model_instance) if self.__new_default is NULL else self.__new_default

    def set_new_default(self, x: Any) -> None:
        """
        WARNING: once you set a new default, every time you hit reset,
        it will always return this new value. Haven't thought of a use
        case, but adding the possibility just in case.
        """
        self.__new_default = x

    def append(self, newitem: Any) -> None:
        if self.is_container_ref:
            getattr(self.current, self.ref_attr).append(newitem)
        else:
            raise TypeError(
                f"Append failed. Datapoint '{self.datapoint_name}' is not a ref obj. Maybe you meant '{self.datapoint_name}().append({newitem})'"
            )

    def __set__(self, instance, value):
        raise AttributeError("Can't set attribute, please use attr.set_value() instead")

    def __bool__(self):
        return True

    def __repr__(self) -> str:
        return f"<Datapoint: name={self.datapoint_name} value={self.value}>"

    # Not sure the operators should be valid... TODO: Think on valid operators for datapoint object:
    # def __lt__(self, other):
    #     return self.value < other

    # def __le__(self, other):
    #     return self.value <= other

    # def __eq__(self, other):
    #     return self.value == other

    # def __ne__(self, other):
    #     return self.value != other

    # def __gt__(self, other):
    #     return self.value > other

    # def __ge__(self, other):
    #     return self.value >= other

    def __len__(self):
        return len(self.value)

    # def __add__(self, other):
    #     return self.value + other

    # def __sub__(self, other):
    #     return self.value - other

    # def __div__(self, other):
    #     return self.value/other

    # def __mul__(self, other):
    #     return self.value * other

    # def __neg__(self):
    #     return -self.value

    # def __pos__(self):
    #     return +self.value

    # def __abs__(self):
    #     return abs(self.value)

    # def __invert__(self):
    #     return ~self.value
