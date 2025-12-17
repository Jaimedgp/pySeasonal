#!/usr/bin/env python

"""
Comprehensive test suite for config.py module.

Tests cover:
- _build_paths() function
  - Building paths with DATA_DIR environment variable
  - Building paths with 'home' from config
  - Skipping 'home', 'dir_output', and 'filename' keys
- _check_paths_exist() function
  - Valid paths that exist
  - Missing paths that should raise FileNotFoundError
  - Paths with 'filename' in key (should be skipped)
  - Empty 'home' path (should be skipped)
- load_config() function
  - Valid config file loading with path building
  - Path validation within config
  - Environment variable handling (DATA_DIR)
  - Invalid/missing config files
  - YAML structure validation
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from pyseasonal.utils.config import _build_paths, _check_paths_exist, load_config


class TestBuildPaths:
    """Test cases for _build_paths() function."""

    def test_build_paths_with_home_from_config(self, tmp_path):
        """Should build paths using 'home' from config when DATA_DIR not set."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        paths_dict = {
            "home": str(base_dir),
            "data_path": "/data",
            "gcm_path": "/gcm",
            "output_path": "/output"
        }

        with patch.dict(os.environ, {}, clear=True):
            result = _build_paths(paths_dict.copy())

        assert result["home"] == str(base_dir)
        assert result["data_path"] == str(base_dir) + "/data"
        assert result["gcm_path"] == str(base_dir) + "/gcm"
        assert result["output_path"] == str(base_dir) + "/output"

    def test_build_paths_with_data_dir_env(self, tmp_path):
        """Should use DATA_DIR environment variable as base path."""
        base_dir = tmp_path / "env_base"
        base_dir.mkdir()

        paths_dict = {
            "home": "/config/home",
            "data_path": "/data",
            "gcm_path": "/gcm"
        }

        with patch.dict(os.environ, {"DATA_DIR": str(base_dir)}):
            result = _build_paths(paths_dict.copy())

        # DATA_DIR takes precedence over home
        assert result["home"] == "/config/home"  # home is not modified
        assert result["data_path"] == str(base_dir) + "/data"
        assert result["gcm_path"] == str(base_dir) + "/gcm"

    def test_build_paths_skips_home_key(self):
        """Should not modify 'home' key."""
        paths_dict = {
            "home": "/original/home",
            "data_path": "/data"
        }

        with patch.dict(os.environ, {}, clear=True):
            result = _build_paths(paths_dict.copy())

        assert result["home"] == "/original/home"
        assert result["data_path"] == "/original/home/data"

    def test_build_paths_skips_dir_output_key(self):
        """Should not modify 'dir_output' key."""
        paths_dict = {
            "home": "/base",
            "dir_output": "/separate/output",
            "data_path": "/data"
        }

        with patch.dict(os.environ, {}, clear=True):
            result = _build_paths(paths_dict.copy())

        assert result["dir_output"] == "/separate/output"
        assert result["data_path"] == "/base/data"

    def test_build_paths_skips_filename_keys(self):
        """Should not modify keys containing 'filename'."""
        paths_dict = {
            "home": "/base",
            "data_path": "/data",
            "output_filename": "result.nc",
            "input_filename_pattern": "input_*.nc"
        }

        with patch.dict(os.environ, {}, clear=True):
            result = _build_paths(paths_dict.copy())

        assert result["output_filename"] == "result.nc"
        assert result["input_filename_pattern"] == "input_*.nc"
        assert result["data_path"] == "/base/data"

    def test_build_paths_with_empty_home(self):
        """Should handle empty home path."""
        paths_dict = {
            "home": "",
            "data_path": "/data"
        }

        with patch.dict(os.environ, {}, clear=True):
            result = _build_paths(paths_dict.copy())

        assert result["home"] == ""
        assert result["data_path"] == "/data"

    def test_build_paths_data_dir_precedence(self, tmp_path):
        """DATA_DIR environment variable should take precedence over home."""
        env_base = tmp_path / "env_dir"
        env_base.mkdir()

        paths_dict = {
            "home": "/config/home",
            "data_path": "/data"
        }

        with patch.dict(os.environ, {"DATA_DIR": str(env_base)}):
            result = _build_paths(paths_dict.copy())

        assert result["data_path"] == str(env_base) + "/data"

    def test_build_paths_multiple_skipped_keys(self):
        """Should skip all special keys: home, dir_output, and filename keys."""
        paths_dict = {
            "home": "/base",
            "dir_output": "/output",
            "output_filename": "out.nc",
            "mask_filename": "mask.nc",
            "data_path": "/data",
            "gcm_path": "/gcm"
        }

        with patch.dict(os.environ, {}, clear=True):
            result = _build_paths(paths_dict.copy())

        # Skipped keys remain unchanged
        assert result["home"] == "/base"
        assert result["dir_output"] == "/output"
        assert result["output_filename"] == "out.nc"
        assert result["mask_filename"] == "mask.nc"
        
        # Modified keys
        assert result["data_path"] == "/base/data"
        assert result["gcm_path"] == "/base/gcm"


class TestCheckPathsExist:
    """Test cases for _check_paths_exist() function."""

    def test_all_paths_exist(self, tmp_path):
        """Should return True when all paths exist."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        file1 = tmp_path / "file.txt"
        dir1.mkdir()
        dir2.mkdir()
        file1.write_text("test content")

        paths_dict = {
            "path1": str(dir1),
            "path2": str(dir2),
            "file_path": str(file1)
        }

        assert _check_paths_exist(paths_dict) is True

    def test_missing_path_raises_error(self, tmp_path):
        """Should raise FileNotFoundError when a path doesn't exist."""
        existing_dir = tmp_path / "exists"
        existing_dir.mkdir()

        paths_dict = {
            "existing_path": str(existing_dir),
            "missing_path": "/does/not/exist"
        }

        with pytest.raises(FileNotFoundError, match="Path for 'missing_path' does not exist"):
            _check_paths_exist(paths_dict)

    def test_skip_filename_keys(self, tmp_path):
        """Should skip validation for keys containing 'filename'."""
        existing_dir = tmp_path / "exists"
        existing_dir.mkdir()

        paths_dict = {
            "existing_path": str(existing_dir),
            "output_filename": "/non/existent/file.txt",
            "input_filename_pattern": "/another/non/existent/pattern.nc"
        }

        assert _check_paths_exist(paths_dict) is True

    def test_skip_empty_home_path(self, tmp_path):
        """Should skip validation for empty 'home' path."""
        existing_dir = tmp_path / "exists"
        existing_dir.mkdir()

        paths_dict = {
            "existing_path": str(existing_dir),
            "home": ""
        }

        assert _check_paths_exist(paths_dict) is True

    def test_non_empty_home_path_must_exist(self):
        """Should validate non-empty 'home' path."""
        paths_dict = {
            "home": "/this/path/does/not/exist"
        }

        with pytest.raises(FileNotFoundError, match="Path for 'home' does not exist"):
            _check_paths_exist(paths_dict)

    def test_empty_dictionary(self):
        """Should return True for empty dictionary."""
        assert _check_paths_exist({}) is True


class TestLoadConfig:
    """Test cases for load_config() function."""

    def test_load_config_builds_and_validates_paths(self, tmp_path, capsys):
        """Should load config, build paths, and validate them."""
        config_file = tmp_path / "test_config.yaml"
        base_dir = tmp_path / "base"
        data_dir = base_dir / "data"
        gcm_dir = base_dir / "gcm"
        
        base_dir.mkdir()
        data_dir.mkdir()
        gcm_dir.mkdir()

        config_content = f"""
models: ['ecmwf']
domain: 'medcof'

paths:
  home: '{str(base_dir)}'
  data_path: '/data'
  gcm_path: '/gcm'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {}, clear=True):
            config = load_config(str(config_file))

        assert config['models'] == ['ecmwf']
        assert config['paths']['home'] == str(base_dir)
        assert config['paths']['data_path'] == str(data_dir)
        assert config['paths']['gcm_path'] == str(gcm_dir)

        captured = capsys.readouterr()
        assert f"The path of the configuration file is {str(config_file)}" in captured.out

    def test_load_config_with_data_dir_env(self, tmp_path):
        """Should use DATA_DIR environment variable when set."""
        config_file = tmp_path / "test_config.yaml"
        env_base = tmp_path / "env_base"
        data_dir = env_base / "data"
        
        env_base.mkdir()
        data_dir.mkdir()

        config_content = """
domain: 'test'

paths:
  home: ''
  data_path: '/data'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {"DATA_DIR": str(env_base)}):
            config = load_config(str(config_file))

        assert config['paths']['data_path'] == str(data_dir)

    def test_load_config_with_empty_home(self, tmp_path):
        """Should handle empty home path."""
        config_file = tmp_path / "test_config.yaml"
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        config_content = f"""
domain: 'test'

paths:
  home: ''
  data_path: '{str(data_dir)}'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {}, clear=True):
            config = load_config(str(config_file))

        assert config['paths']['home'] == ''
        assert config['paths']['data_path'] == str(data_dir)

    def test_load_config_skips_special_keys_in_build(self, tmp_path):
        """Should not modify home, dir_output, and filename keys in _build_paths."""
        config_file = tmp_path / "test_config.yaml"
        base_dir = tmp_path / "base"
        data_dir = base_dir / "data"
        output_dir = tmp_path / "separate" / "output"
        
        base_dir.mkdir()
        data_dir.mkdir()
        output_dir.mkdir(parents=True)

        config_content = f"""
paths:
  home: '{str(base_dir)}'
  dir_output: '{str(output_dir)}'
  output_filename: 'result.nc'
  data_path: '/data'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {}, clear=True):
            config = load_config(str(config_file))

        assert config['paths']['home'] == str(base_dir)
        assert config['paths']['dir_output'] == str(output_dir)
        assert config['paths']['output_filename'] == 'result.nc'
        assert config['paths']['data_path'] == str(data_dir)

    def test_load_config_missing_built_path_raises_error(self, tmp_path):
        """Should raise error if built path doesn't exist."""
        config_file = tmp_path / "test_config.yaml"
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        # Don't create /data directory

        config_content = f"""
paths:
  home: '{str(base_dir)}'
  data_path: '/data'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(FileNotFoundError, match="Path for 'data_path' does not exist"):
                load_config(str(config_file))

    def test_load_config_file_not_found(self):
        """Should raise FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_config("/non/existent/config.yaml")

    def test_load_config_invalid_yaml(self, tmp_path):
        """Should raise YAML parsing error for invalid syntax."""
        config_file = tmp_path / "bad_config.yaml"
        config_file.write_text("this is not: valid: yaml: content:")

        with pytest.raises(Exception):
            load_config(str(config_file))

    def test_load_config_without_paths_section(self, tmp_path):
        """Should raise KeyError when 'paths' section is missing."""
        config_file = tmp_path / "test_config.yaml"
        config_content = """
models: ['ecmwf']
domain: 'medcof'
"""
        config_file.write_text(config_content)

        with pytest.raises(KeyError):
            load_config(str(config_file))

    def test_load_config_preserves_non_path_fields(self, tmp_path):
        """Should preserve all non-path configuration fields."""
        config_file = tmp_path / "test_config.yaml"
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        config_content = f"""
models: ['ecmwf', 'cmcc']
version: ['51', '4']
domain: 'medcof'
quantile_version: 'v1r'
agg_label: ['1mon', '2mon', '3mon']

paths:
  home: '{str(base_dir)}'

model_settings:
  ecmwf51:
    variable_std: ['t2m', 'tp']
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {}, clear=True):
            config = load_config(str(config_file))

        assert config['models'] == ['ecmwf', 'cmcc']
        assert config['version'] == ['51', '4']
        assert config['domain'] == 'medcof'
        assert config['quantile_version'] == 'v1r'
        assert 'model_settings' in config


class TestLoadConfigIntegration:
    """Integration tests using realistic config structures."""

    def test_realistic_config_with_relative_paths(self, tmp_path):
        """Test realistic config with relative paths that get built."""
        config_file = tmp_path / "realistic_config.yaml"
        
        # Create directory structure
        home_dir = tmp_path / "pticlima"
        data_dir = home_dir / "DATA" / "SEASONAL"
        results_dir = home_dir / "Results"
        masks_dir = home_dir / "Auxiliary-material" / "Masks"
        
        home_dir.mkdir()
        data_dir.mkdir(parents=True)
        results_dir.mkdir()
        masks_dir.mkdir(parents=True)

        config_content = f"""
models: ['ecmwf', 'cmcc']
version: ['51', '4']
domain: 'medcof'

paths:
  home: '{str(home_dir)}'
  path_gcm_base: '/DATA/SEASONAL'
  dir_results: '/Results'
  mask_dir: '/Auxiliary-material/Masks'
  output_filename: 'forecast.nc'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {}, clear=True):
            config = load_config(str(config_file))

        assert config['models'] == ['ecmwf', 'cmcc']
        assert config['paths']['home'] == str(home_dir)
        assert config['paths']['path_gcm_base'] == str(data_dir)
        assert config['paths']['dir_results'] == str(results_dir)
        assert config['paths']['mask_dir'] == str(masks_dir)
        assert config['paths']['output_filename'] == 'forecast.nc'

    def test_config_with_data_dir_override(self, tmp_path):
        """Test that DATA_DIR environment variable overrides home."""
        config_file = tmp_path / "test_config.yaml"
        
        config_home = tmp_path / "config_home"
        env_home = tmp_path / "env_home"
        data_dir = env_home / "data"
        
        config_home.mkdir()
        env_home.mkdir()
        data_dir.mkdir()

        config_content = f"""
domain: 'argo'

paths:
  home: '{str(config_home)}'
  data_path: '/data'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {"DATA_DIR": str(env_home)}):
            config = load_config(str(config_file))

        # home stays as configured, but paths are built from DATA_DIR
        assert config['paths']['home'] == str(config_home)
        assert config['paths']['data_path'] == str(data_dir)

    def test_config_with_empty_home_and_data_dir(self, tmp_path):
        """Test config with empty home using DATA_DIR."""
        config_file = tmp_path / "test_config.yaml"
        
        env_home = tmp_path / "env_home"
        data_dir = env_home / "data"
        
        env_home.mkdir()
        data_dir.mkdir()

        config_content = """
domain: 'docker'

paths:
  home: ''
  data_path: '/data'
  output_filename: 'output.nc'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {"DATA_DIR": str(env_home)}):
            config = load_config(str(config_file))

        assert config['paths']['home'] == ''
        assert config['paths']['data_path'] == str(data_dir)
        assert config['paths']['output_filename'] == 'output.nc'


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_path_concatenation(self, tmp_path):
        """Test that paths are correctly concatenated."""
        config_file = tmp_path / "test_config.yaml"
        base_dir = tmp_path / "base"
        subdir = base_dir / "sub" / "path"
        
        base_dir.mkdir()
        subdir.mkdir(parents=True)

        config_content = f"""
paths:
  home: '{str(base_dir)}'
  nested_path: '/sub/path'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {}, clear=True):
            config = load_config(str(config_file))

        assert config['paths']['nested_path'] == str(subdir)

    def test_trailing_slash_handling(self, tmp_path):
        """Test handling of paths with and without trailing slashes."""
        config_file = tmp_path / "test_config.yaml"
        base_dir = tmp_path / "base"
        data_dir = base_dir / "data"
        
        base_dir.mkdir()
        data_dir.mkdir()

        # Test with trailing slash on base
        config_content = f"""
paths:
  home: '{str(base_dir)}/'
  data_path: '/data'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {}, clear=True):
            config = load_config(str(config_file))

        # Path should still work (though might have // in it)
        assert 'data' in config['paths']['data_path']

    def test_dir_output_not_modified_by_build_paths(self, tmp_path):
        """Test that dir_output is not modified by _build_paths but must exist for validation."""
        config_file = tmp_path / "test_config.yaml"
        base_dir = tmp_path / "base"
        output_dir = tmp_path / "output"
        base_dir.mkdir()
        output_dir.mkdir()

        config_content = f"""
paths:
  home: '{str(base_dir)}'
  dir_output: '{str(output_dir)}'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {}, clear=True):
            config = load_config(str(config_file))
            # dir_output is not modified by _build_paths
            assert config['paths']['dir_output'] == str(output_dir)
            # But it still exists, so validation passes


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
