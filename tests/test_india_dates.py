"""DoPT's later 2026 orders supersede the annual Annexure-I list."""
import unittest

from providers.global_regions import _in_region


class IndiaOfficialAmendments(unittest.TestCase):
    def test_later_orders_are_reflected_in_2026_dates(self):
        events = [e for e in _in_region()["events"] if e["date"].startswith("2026-")]
        # DoPT 22 May 2026: Bakrid is moved from 27 May to 28 May.
        # DoPT 9 April 2026: Ambedkar's birthday is an additional holiday.
        for holiday, expected in (("Bakrid", "2026-05-28"), ("Ambedkar", "2026-04-14")):
            with self.subTest(holiday=holiday):
                self.assertEqual([e["date"] for e in events if holiday in e["name"]], [expected])


if __name__ == "__main__":
    unittest.main()
