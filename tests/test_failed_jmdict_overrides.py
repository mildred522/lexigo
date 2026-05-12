from pathlib import Path

from dict_feasibility.translation import load_supplemental_translation_overrides


def test_source_overrides_include_repaired_jmdict_failures() -> None:
    overrides = load_supplemental_translation_overrides(
        Path("sources/translations/supplemental_overrides.json")
    )
    by_id = {item.source_entry_id: item.meaning_zh for item in overrides}

    assert by_id["1137540"] == "约德尔唱法"
    assert by_id["1292170"] == "催情药"
    assert by_id["1983850"] == "冲击横纲"
    assert by_id["2249790"] == "虚拟语气过去完成时"
    assert by_id["5741293"] == "《女杀油地狱》（近松门左卫门净琉璃剧作）"
