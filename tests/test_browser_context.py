import json
import unittest

from chexsa_browser.context import ContextView, changes
from chexsa_browser.models import BrowserError, Element, Observation
from chexsa_browser.regions import group_regions


def snapshot(count=500, generation="o1"):
    elements = [Element("t", "f", "d", i, "button", f"Message {i}", capabilities=("click",), ref=f"e{i}") for i in range(count)]
    result = Observation(generation, "p", "http://local", "Inbox", [], elements, {})
    result.regions = group_regions(elements)
    return result


class ContextTests(unittest.TestCase):
    def test_large_page_is_bounded_and_every_control_can_be_paged(self):
        observation = snapshot()
        view = ContextView(3000)
        rendered = json.loads(view.render(observation))
        self.assertLessEqual(len(observation.context), 3000)
        self.assertGreater(rendered["controls"]["omitted"], 0)
        seen, cursor = [], None
        while True:
            page = view.inspect(observation, cursor=cursor)
            seen.extend(e["ref"] for e in page["elements"])
            cursor = page["next_cursor"]
            if cursor is None:
                break
        self.assertEqual(len(seen), 500)
        self.assertEqual(len(set(seen)), 500)

    def test_search_finds_a_control_beyond_the_initial_budget(self):
        observation = snapshot()
        found = ContextView().find(observation, "Message 499")
        self.assertEqual(found["elements"][0]["ref"], "e499")

    def test_huge_names_and_values_still_advance_the_cursor(self):
        observation = snapshot(2)
        for element in observation.elements:
            element.name = "long " * 1000
            element.value = "value " * 1000
            element.context = ("context " * 1000,)
        page = ContextView(2000).page(observation, observation.elements, budget=650)
        self.assertGreater(len(page["elements"]), 0)
        self.assertNotEqual(page["next_cursor"], "o1:0")

    def test_old_cursors_are_rejected(self):
        with self.assertRaises(BrowserError):
            ContextView().inspect(snapshot(generation="o2"), cursor="o1:20")

    def test_ref_refresh_does_not_create_false_changes(self):
        first, second = snapshot(2), snapshot(2, "o2")
        second.elements[0].ref = "e100"
        self.assertEqual(changes(first, second), ["No visible changes."])
        second.elements.pop()
        self.assertIn("Removed:", changes(first, second)[0])

    def test_late_confirmation_text_survives_large_page(self):
        first, second = snapshot(), snapshot(generation="o2")
        second.text["status"] = {"text": "Message sent", "region_path": ()}
        second.changes = changes(first, second)
        self.assertIn("Message sent", ContextView(3000).render(second))
