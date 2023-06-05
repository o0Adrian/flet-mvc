import pytest
import flet as ft
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flet_mvc import FletModel, data


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

    # TODO TEST THIS:
    @data.RefOnly
    def ref_only_datapoint(self):
        return None


# Flet components to test
component_value_attr_map = {
    # TODO: Select the best option for every component.
    ft.TextField: "value",
    # ft.Checkbox: 'checked',
    # ... add all other Flet components here ...
}


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
    model.datapoint_list().append("Test Value")
    assert model.datapoint_list() == ["Test Value"]
    model.datapoint_list.reset()
    assert not model.datapoint_list()


# Test DataPoint logical operations
def test_datapoint_logical():
    model = MockModel()
    model.datapoint.set_value(None)
    assert not model.datapoint()  # Should evaluate to False
    model.datapoint.set_value("Test Value")
    assert model.datapoint()  # Should evaluate to True


# Test that we can set the initial value of a component using a Ref object
@pytest.mark.parametrize("component, value_attr", component_value_attr_map.items())
def test_initial_value(component, value_attr):
    model = MockModel()
    component_instance = component(ref=model.ref_datapoint, value="Initial value")
    assert getattr(component_instance, value_attr) == "Initial value"
    # The next ocurs every time an app is launched:
    model.ref_datapoint.reset()
    assert getattr(component_instance, value_attr) == "Datapoint initial value"


# Test that we can change the value of a component using a Ref object
@pytest.mark.parametrize("component, value_attr", component_value_attr_map.items())
def test_change_value(component, value_attr):
    model = MockModel()
    datapoint = model.datapoint

    component_instance = component(ref=datapoint, value="Initial value")
    datapoint.set_value("New value")
    assert getattr(component_instance, value_attr) == "New value"
