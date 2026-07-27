import flet.testing as ftt


async def test_toggle_title(flet_app: ftt.FletTestApp) -> None:
    tester = flet_app.tester
    await tester.pump_and_settle()

    assert (await tester.find_by_text("Hello, World!")).count == 1

    await tester.tap(await tester.find_by_key("toggle-title"))
    await tester.pump_and_settle()

    assert (await tester.find_by_text("Hello from Flet MVC!")).count == 1
