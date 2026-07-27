import flet.testing as ftt


async def test_select_settings_tab(flet_app: ftt.FletTestApp) -> None:
    tester = flet_app.tester
    await tester.pump_and_settle()

    assert (await tester.find_by_text("This is the home tab.")).count == 1

    await tester.tap(await tester.find_by_key("settings-tab"))
    await tester.pump_and_settle()

    assert (await tester.find_by_text("This is the settings tab.")).count == 1
