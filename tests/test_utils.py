import pytest
import yaml
from src.utils.load_config import load_config

def test_load_config_success(tmp_path):
    d = tmp_path / "configs"
    d.mkdir()
    config_file = d / "test_config.yaml"

    expected_data = {
        "model": "test-gpt",
        "params": {"temp": 0.7, "top_p": 1.0}
    }

    config_file.write_text(yaml.dump(expected_data), encoding="utf-8")

    result = load_config(config_file)

    assert result == expected_data
    assert isinstance(result, dict)

def test_load_config_file_not_found():
    non_existent_path = "ghost_config.yaml"

    with pytest.raises(FileNotFoundError) as exc_info:
        load_config(non_existent_path)
    
    assert "Config file not found" in str(exc_info.value)

def test_load_config_invalid_yaml(tmp_path):
    bad_file = tmp_path / "broken.yaml"

    bad_file.write_text("key: [unclosed bracket", encoding="utf-8")

    with pytest.raises(RuntimeError) as exc_info:
        load_config(bad_file)
    
    assert "Failed to parse YAML" in str(exc_info.value)

    