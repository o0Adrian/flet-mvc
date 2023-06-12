import pytest
import flet as ft
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flet_mvc import FletModel, data
from data.component_attribute import component_value_attr_map, potential_attributes


# define your model
class MockModel(FletModel):
    @data
    def datapoint(self):
        return ""

    @data
    def datapoint_list(self):
        return []

    @data
    def ref_datapoint(self):
        return "Datapoint initial value"

    @data.RefOnly
    def ref_only_datapoint(self):
        return None


# Test DataPoint initialization
def test_datapoint_init():
    model = MockModel()
    assert isinstance(model.datapoint, data)


# Test DataPoint set, get and reset value
def test_datapoint_set_get():
    model = MockModel()
    model.datapoint.set_value("Test Value")
    assert model.datapoint() == "Test Value"
    model.datapoint.reset()
    assert model.datapoint() == ""


# Test DataPoint append value
def test_datapoint_append():
    model = MockModel()
    assert not model.datapoint_list.has_set_value()

    model.datapoint_list().append("Test Value") # normal append won't modify has_set_value attr.
    assert not model.datapoint_list.has_set_value()
    assert model.datapoint_list() == ["Test Value"]

    model.datapoint_list.set_value(["Test Value"])
    assert model.datapoint_list.has_set_value()

    model.datapoint_list.reset()
    assert not model.datapoint_list.has_set_value()
    assert not model.datapoint_list()


# Test DataPoint logical operations
def test_datapoint_logical():
    model = MockModel()
    model.datapoint.set_value(None)
    assert not model.datapoint()  # Should evaluate to False
    model.datapoint.set_value("Test Value")
    assert model.datapoint()  # Should evaluate to True


# Test DataPoint logical operations
def test_datapoint_ref_only():
    model = MockModel()

    with pytest.raises(TypeError):
        model.ref_only_datapoint()

    with pytest.raises(TypeError):
        model.ref_only_datapoint.set_value()

    with pytest.raises(TypeError):
        model.ref_only_datapoint.append(1)

    with pytest.raises(TypeError):
        model.ref_only_datapoint.value

    with pytest.raises(TypeError):
        model.ref_only_datapoint.value = 1

    with pytest.raises(TypeError):
        model.ref_only_datapoint.set_default()

    with pytest.raises(TypeError):
        model.ref_only_datapoint.reset()


def test_datapoint_ref_only2():
    model = MockModel()
    assert not model.ref_only_datapoint.current
    ft.Text(ref=model.ref_only_datapoint)
    assert model.ref_only_datapoint.current


# Test that we can set the initial value of a component using a Ref object
@pytest.mark.parametrize("component, value_attr", component_value_attr_map.items())
def test_initial_value(component, value_attr):
    model = MockModel()

    if potential_attributes[value_attr] == list:
        value = ["item1", "item2"]
        new_default = ["default1", "default2"]
    elif potential_attributes[value_attr] == str:
        value = "Initial value"
        new_default = "Default"
    else:
        value = ft.Text("test")  # Default case
        new_default = ft.Text("new_default")

    model.ref_datapoint.set_default(new_default)
    kwargs = {value_attr: value}

    component_instance = component(ref=model.ref_datapoint, **kwargs)

    assert getattr(component_instance, value_attr) == value
    model.ref_datapoint.reset()
    assert getattr(component_instance, value_attr) == new_default
    model.ref_datapoint.set_value(value)
    assert getattr(component_instance, value_attr) == value

    model.ref_datapoint.__hard_reset__()
