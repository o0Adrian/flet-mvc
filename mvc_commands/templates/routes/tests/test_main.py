import flet.testing as ftt


async def test_navigate_between_views(flet_app: ftt.FletTestApp) -> None:
    tester = flet_app.tester
    await tester.pump_and_settle()

    assert (await tester.find_by_text("This is the home view.")).count == 1

    await tester.tap(await tester.find_by_key("go-secondary"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("This is the secondary view.")).count == 1

    await tester.tap(await tester.find_by_key("return-home"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("This is the home view.")).count == 1
