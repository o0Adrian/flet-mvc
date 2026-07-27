import flet.testing as ftt


async def test_reactivity_components_table_tabs_and_routing(
    flet_app: ftt.FletTestApp,
):
    tester = flet_app.tester
    await tester.pump_and_settle()

    assert (await tester.find_by_text("initial:0")).count == 1
    assert (await tester.find_by_text("Declarative ready")).count == 1
    assert (await tester.find_by_text("FletComponent ready")).count == 1
    assert (await tester.find_by_text("Ada")).count == 1
    assert (await tester.find_by_text("Grace")).count == 1
    assert (await tester.find_by_text("State")).count == 1

    await tester.enter_text(await tester.find_by_key("query"), "typed")
    await tester.pump_and_settle()
    assert (await tester.find_by_text("typed:0")).count == 1

    await tester.tap(await tester.find_by_key("set-from-model"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("server:0")).count == 1

    await tester.tap(await tester.find_by_key("component-increment"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("server:1")).count == 1

    await tester.tap(await tester.find_by_text("About"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("Integration ready")).count == 1

    await tester.tap(await tester.find_by_key("open-details"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("Details route")).count == 1

    await tester.tap(await tester.find_by_key("return-home"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("server:1")).count == 1
