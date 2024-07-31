from datetime import date
import cwpl.ui as ui


def test_get_previous_month_end():
    assert ui.get_previous_month_end(date(2001, 1, 1)) == date(2000, 12, 30)
    assert ui.get_previous_month_end(date(2001, 2, 1)) == date(2001, 1, 30)
    # february
    assert ui.get_previous_month_end(date(2001, 3, 1)) == date(2001, 2, 27)
    assert ui.get_previous_month_end(date(2000, 3, 1)) == date(2000, 2, 28)
    # other days
    assert ui.get_previous_month_end(date(2001, 1, 12)) == date(2000, 12, 30)
    assert ui.get_previous_month_end(date(2001, 1, 21)) == date(2000, 12, 30)
    assert ui.get_previous_month_end(date(2001, 1, 31)) == date(2000, 12, 30)
