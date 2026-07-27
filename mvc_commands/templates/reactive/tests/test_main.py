import flet.testing as ftt


async def test_increment_updates_count_and_message(
    flet_app: ftt.FletTestApp,
) -> None:
    tester = flet_app.tester
    await tester.pump_and_settle()

    assert (await tester.find_by_text("0")).count == 1
    assert (await tester.find_by_text("You clicked 0 times.")).count == 1

    await tester.tap(await tester.find_by_key("increment"))
    await tester.pump_and_settle()

    assert (await tester.find_by_text("1")).count == 1
    assert (await tester.find_by_text("You clicked 1 time.")).count == 1
