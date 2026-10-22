import unittest

from chexsa_browser.models import Element
from chexsa_browser.regions import group_regions


class RegionTests(unittest.TestCase):
    def element(self, node, role, path=(), focused=False):
        return Element("t", "f", "d", node, role, "Same name", states={"focused": focused}, region_path=path)

    def test_duplicate_named_regions_do_not_merge(self):
        first, second = self.element(1, "dialog"), self.element(2, "dialog")
        a = self.element(3, "button", (first.identity,))
        b = self.element(4, "textbox", (second.identity,), True)
        regions = group_regions([first, second, a, b])
        self.assertEqual(len(regions), 2)
        self.assertEqual(regions[0].key, second.identity)
        self.assertNotEqual(a.region, b.region)

    def test_form_inside_dialog_stays_with_dialog(self):
        dialog = self.element(1, "dialog")
        form = self.element(2, "form", (dialog.identity,))
        field = self.element(3, "textbox", (dialog.identity, form.identity))
        regions = group_regions([dialog, form, field])
        self.assertEqual(len(regions), 1)
        self.assertEqual(field.region, dialog.identity)
