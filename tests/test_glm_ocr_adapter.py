from pathlib import Path

from features.ocr.glm_ocr_adapter import GLMOCRAdapter, SUPPORT_FILES, TASK_PROMPTS


def test_glm_ocr_describes_missing_weights(tmp_path):
    adapter = GLMOCRAdapter(model_dir=tmp_path, strict=True)
    assert adapter.available is False
    assert "not found" in adapter.describe().lower()


def test_glm_ocr_reports_missing_input_file(tmp_path):
    adapter = GLMOCRAdapter(model_dir=tmp_path, strict=True)
    assert "not found" in adapter.extract_text(tmp_path / "missing.png").lower()


def test_glm_ocr_rejects_unknown_task_without_loading_model(tmp_path):
    image = tmp_path / "receipt.png"
    image.touch()
    adapter = GLMOCRAdapter(model_dir=tmp_path, strict=True)
    assert "unsupported" in adapter.extract_text(image, task="layout").lower()


def test_glm_ocr_uses_documented_task_prompts():
    assert TASK_PROMPTS == {
        "text": "Text Recognition:",
        "formula": "Formula Recognition:",
        "table": "Table Recognition:",
    }
    assert "config.json" in SUPPORT_FILES
    assert "tokenizer.json" in SUPPORT_FILES
