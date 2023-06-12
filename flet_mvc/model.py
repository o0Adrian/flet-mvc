"""
Data decorator. Originally created to be used in every method of the model class
it will convert the method to a datapoint/node that can be set and reset.

It allows using a reference datapoints automatically when sent in
the "ref" parameter of a Flet Control.

Next Feature: Dependency between datapoints (currently we can't set default values
with other datapoints and make them change automatically when the parent changes).
Send/Receive decorators.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional, Callable, List

logging.basicConfig(level=logging.WARNING)

__all__ = ["data", "FletModel"]


class FletModel:
    def __init__(self, **kwargs):
        self.ref_objs = []
        self.controller = None


class _Null:
    """Null class that will be used when the datapoint is still empty"""

    def __bool__(self):
        return False

    def __repr__(self):
        return "Null"


NULL = _Null()


@dataclass
class RefDatapoint:
    current: Optional[Any] = NULL
    ref_attr: Optional[str] = NULL
    ref_type: Optional[Any] = NULL


class data:
    """
    data decorator
    Converts a class method (intended for the Model class) to a datapoint
    """

    def __init__(self, f: Callable[..., Any]):
        self.is_instanciated = False
        self.func = f
        self.name: str = f.__name__
        self.__has_set_value = False
        self.__value: Optional[Any] = NULL
        self.__new_default: Optional[Any] = NULL
        self.__ref_only = False

        # Ref obj
        self.__ref_datapoints: List[RefDatapoint] = []
        self.is_ref_obj: bool = False
        self.is_container_ref: bool = False
        self.is_ref_multi_referenced: bool = False

    @classmethod
    def RefOnly(cls, f):
        instance = cls(f)
        instance.__ref_only = True  # noqa
        return instance

    def __call__(self) -> Any:
        """
        Return current value when datapoint is called
        e.g. print(self.model.fruit()) -> 'Apple'
        """
        # ref_only
        if self.__ref_only:
            raise TypeError(
                f"'Ref Only' datapoint is not callable; perhaps you meant 'self.model.{self.name}.current' to access Referenced object."
            )

        if self.is_ref_obj:
            # Expecting for all of them to be the same, else don't use multi datapoints if they are going to be different.
            return getattr(
                self.__ref_datapoints[0].current, self.__ref_datapoints[0].ref_attr
            )
        else:
            return self.value

    def __hard_reset__(self) -> None:
        """Used on testing only so far"""
        self.is_instanciated = False
        self.__has_set_value = False
        self.__value: Optional[Any] = NULL
        self.__new_default: Optional[Any] = NULL
        self.__ref_datapoints: List[RefDatapoint] = []
        self.is_ref_obj: bool = False
        self.is_container_ref: bool = False
        self.is_ref_multi_referenced: bool = False
        self.__get__(self.model_instance, None)

    def __get__(self, instance, owner):
        """
        Return value when accessing the datapoint instance.
        This will return the self instance of the datapoint in order to
        access the other methods of the datapoint.
        """
        if self.is_instanciated:
            return self

        self.model_instance = instance
        self.model_class = self.model_instance.__class__
        self.is_instanciated = True

        if not hasattr(self.model_instance, "ref_objs"):
            super(self.model_class, self.model_instance).__init__()

        # ref only warning
        if self.__ref_only:
            if self.func(instance) != None:
                logging.warning(
                    f"The datapoint '{self.name}' is Ref Only, the returned value '{self.func(instance)}' won't have any impact. Consider returning 'None' value."
                )
            return self

        if self.value is NULL:
            self.value = self.func(instance)

        return self

    def has_set_value(self):
        return self.__has_set_value

    @property
    def value(self):
        if self.__ref_only:
            raise TypeError(
                f"'Ref Only' datapoint doesn't have a 'value' functionality; perhaps you meant 'self.model.{self.name}.current.<desired method/attribute>' to retrieve a value"
            )
        return self.__value

    @value.setter
    def value(self, value):
        # triggered by __get__ when setting the initial value
        # triggered by reset
        # triggered by set_value
        if self.__ref_only:
            raise TypeError(
                f"'Ref Only' datapoint doesn't have a 'value' property, to set a value use 'self.model.{self.name}.current.<desired method/attribute> = {value}'"
            )

        self.__value = value
        if self.is_ref_obj:
            # this should  automatically modify content and controls properties of the control instance.
            for ref_obj in self.__ref_datapoints:
                if ref_obj.ref_type is None or isinstance(value, ref_obj.ref_type):
                    setattr(ref_obj.current, ref_obj.ref_attr, value)
                else:
                    help_str = (
                        ""
                        if value
                        else " Perhaps you meant to use the @data.RefOnly decorator."
                    )
                    raise TypeError(
                        f"The {type(value)} value of the Datapoint '{self.name}' does not match expected type '{ref_obj.ref_type}' for '{ref_obj.current}'.{help_str}"
                    )

    @property
    def current(self):
        """
        If the datapoint is a ref object, and want to access the Flet control for any other propeties
        use this property, it works as a Ref Object.

        In case the datapoint is used in several Flet controls, it returns the list of all of them.
        """
        return (
            [ref_obj.current for ref_obj in self.__ref_datapoints]
            if self.is_ref_multi_referenced
            else self.__ref_datapoints[0].current
            if self.__ref_datapoints
            else None
        )

    @current.setter
    def current(self, current):
        """First triggered when adding to ref property of a control, this is how we will set the datapoint as a ref obj"""
        if self.__ref_only:
            # if is ref_only and being assigned to another control
            if len(self.__ref_datapoints) == 1:
                raise ValueError(
                    f"The datapoint '{self.name}' is a (Single) Ref object only and has already been asigned to {self.__ref_datapoints[0].current.__class__}, cannot be linked to multiple Controls"
                )
            self.__ref_datapoints.append(RefDatapoint(current=current))
            self.is_ref_obj = True
            return

        ref_datapoint = RefDatapoint(current=current)
        potential_attributes = {
            # order matters, controls may have more than one atribute.
            # DO NOT TOUCH ORDER, they were carefully selected.
            "options": list,
            "value": None,  # accept any value
            "label": str,
            "src": str,
            "text": str,
            "name": str,
            "items": list,
            "shapes": list,
            "content": None,  # Either List or Flet Control. | Why? don't know, inconsistency on Flet's attrs
            "actions": list,
            "controls": list,
            "figure": None,  # accept any value
            "title": None,  # accept any value
            "rows": list,
            "cells": list,
            "destinations": list,
            "tabs": list,
            "paint": None,
        }
        for attr, attr_type in potential_attributes.items():
            if hasattr(current.__class__, attr):
                setattr(ref_datapoint.current, attr, self.value)
                ref_datapoint.ref_attr = attr
                ref_datapoint.ref_type = attr_type
                break

        self.__ref_datapoints.append(ref_datapoint)
        self.is_container_ref = ref_datapoint.ref_attr in [
            "controls",
            "content",
            "figure",
        ]
        self.model_instance.ref_objs.append(self)
        self.is_ref_obj = True
        # if it's assigned to other controls
        if len(self.__ref_datapoints) > 1:
            self.is_ref_multi_referenced = True

    def set_value(self, x: Any) -> None:
        """
        Set value method
        e.g.
        self.model.fruit.set_value('Pear')
        print(model.fruit()) -> 'Pear'
        """
        # set data value, calling value setter
        if self.__ref_only:
            raise TypeError(
                f"'Ref Only' datapoint is not settable; perhaps you meant to change a value using 'self.model.{self.name}.current.<desired method/attribute> = {x}' to modify the Referenced object."
            )
        self.__has_set_value = True
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
        # calling value setter
        if self.__ref_only:
            raise TypeError(f"'Ref Only' datapoint cannot be reset")
        self.value = (
            self.func(self.model_instance)
            if self.__new_default is NULL
            else self.__new_default
        )
        self.__has_set_value = False

    def set_default(self, x: Any) -> None:
        """
        WARNING: once you set a new default, every time you hit reset,
        it will always return this new value. Haven't thought of a use
        case, but adding the possibility just in case.
        """
        if self.__ref_only:
            raise TypeError(f"'Ref Only' datapoint cannot have a default value")
        self.__new_default = x

    def append(self, newitem: Any) -> None:
        if self.__ref_only:
            raise TypeError(
                f"'Ref Only' datapoint doesn't have 'append' functionality; perhaps you meant 'self.model.{self.name}.current.<desired method>.append({newitem})' to append a new object."
            )
        if self.is_container_ref:
            # Using first element since they share the same list reference.
            getattr(
                self.__ref_datapoints[0].current, self.__ref_datapoints[0].ref_attr
            ).append(newitem)
            self.__has_set_value = False
        elif type(self.__value) != list:
            raise AttributeError(
                f"'{type(self.__value)}' object has no attribute 'append'"
            )
        else:
            raise TypeError(
                f"Append failed. Datapoint '{self.name}' is not a ref obj. Maybe you meant 'self.model.{self.name}().append({newitem})'"
            )

    def __set__(self, instance, value):
        raise AttributeError("Can't set attribute, please use attr.set_value() instead")

    def __bool__(self):
        # Always true, since it's used by the Control class in Flet library control.py
        return True

    def __repr__(self) -> str:
        return f"<Datapoint: name={self.name} value={self.value}>"

    def __len__(self):
        return len(self.value)
