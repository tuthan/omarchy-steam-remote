from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ContractTests(unittest.TestCase):
    def test_pinned_contract_bundle_is_complete_and_versioned(self):
        schema = json.loads((ROOT / "protocol" / "schema.json").read_text())
        self.assertEqual(schema["$id"], "https://steamos-remote.local/protocol/v1/schema.json")
        fixtures = sorted((ROOT / "protocol" / "fixtures").glob("*.json"))
        self.assertGreaterEqual(len(fixtures), 6)
        for fixture in fixtures:
            self.assertEqual(json.loads(fixture.read_text())["protocol_version"], 1, fixture.name)

    def test_manifest_uses_native_bar_widget_entry_point(self):
        manifest = json.loads((ROOT / "manifest.json").read_text())
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["kinds"], ["bar-widget"])
        self.assertEqual(manifest["entryPoints"]["barWidget"], "BarWidget.qml")
        self.assertFalse(manifest["barWidget"]["allowMultiple"])


if __name__ == "__main__":
    unittest.main()
