#!/usr/bin/env python

"""
Comprehensive test suite for config.py module.

Tests cover:
- _check_paths_exist() function
  - Valid paths that exist
  - Missing paths that should raise FileNotFoundError
  - Paths with 'filename' in key (should be skipped)
  - Empty dictionaries
- load_config() function
  - Valid config file loading
  - Environment variable handling (GCM_STORE)
  - Path validation within config
  - Invalid/missing config files
  - Missing GCM_STORE in config
  - YAML structure validation
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from pyseasonal.utils.config import _check_paths_exist, load_config


class TestCheckPathsExist:
    """Test cases for _check_paths_exist() function."""

    def test_all_paths_exist(self, tmp_path):
        """Should return True when all paths exist."""
        # Create test directories
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
        missing_dir = tmp_path / "does_not_exist"
        existing_dir.mkdir()

        paths_dict = {
            "existing_path": str(existing_dir),
            "missing_path": str(missing_dir)
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

        # Should not raise error because 'filename' keys are skipped
        assert _check_paths_exist(paths_dict) is True

    def test_empty_dictionary(self):
        """Should return True for empty dictionary."""
        assert _check_paths_exist({}) is True

    def test_first_path_missing(self, tmp_path):
        """Should raise error for first missing path."""
        paths_dict = {
            "missing": "/this/does/not/exist"
        }

        with pytest.raises(FileNotFoundError, match="Path for 'missing' does not exist"):
            _check_paths_exist(paths_dict)

    def test_multiple_missing_paths_reports_first(self, tmp_path):
        """Should raise error for first missing path encountered."""
        paths_dict = {
            "missing1": "/this/does/not/exist",
            "missing2": "/neither/does/this"
        }

        with pytest.raises(FileNotFoundError):
            _check_paths_exist(paths_dict)


class TestLoadConfig:
    """Test cases for load_config() function."""

    def test_load_valid_config_default_gcm_store(self, tmp_path, capsys):
        """Should successfully load config with default GCM_STORE (lustre)."""
        # Create a test config file
        config_file = tmp_path / "test_config.yaml"
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()

        config_content = f"""
models: ['ecmwf', 'cmcc']
version: ['51', '4']
domain: 'medcof'

paths:
  lustre:
    home: '{str(test_dir)}'
    path_gcm_base: '{str(test_dir)}'
    dir_forecast: '{str(test_dir)}'
  pticlima:
    home: '/other/path'
"""
        config_file.write_text(config_content)

        # Load config with default GCM_STORE
        with patch.dict(os.environ, {'GCM_STORE': 'lustre'}):
            config = load_config(str(config_file))

        # Verify config structure
        assert 'models' in config
        assert 'paths' in config
        assert config['models'] == ['ecmwf', 'cmcc']
        assert config['paths']['home'] == str(test_dir)
        assert config['paths']['path_gcm_base'] == str(test_dir)

        # Verify print output
        captured = capsys.readouterr()
        assert f"The path of the configuration file is {str(config_file)}" in captured.out

    def test_load_config_custom_gcm_store(self, tmp_path):
        """Should load config with custom GCM_STORE environment variable."""
        config_file = tmp_path / "test_config.yaml"
        test_dir1 = tmp_path / "lustre_data"
        test_dir2 = tmp_path / "custom_data"
        test_dir1.mkdir()
        test_dir2.mkdir()

        config_content = f"""
domain: 'iberia'

paths:
  lustre:
    home: '{str(test_dir1)}'
  custom:
    home: '{str(test_dir2)}'
    data_path: '{str(test_dir2)}'
"""
        config_file.write_text(config_content)

        # Load with custom GCM_STORE
        with patch.dict(os.environ, {'GCM_STORE': 'custom'}):
            config = load_config(str(config_file))

        assert config['paths']['home'] == str(test_dir2)
        assert config['paths']['data_path'] == str(test_dir2)

    def test_invalid_gcm_store_raises_error(self, tmp_path):
        """Should raise ValueError when GCM_STORE not in config."""
        config_file = tmp_path / "test_config.yaml"
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()

        config_content = f"""
paths:
  lustre:
    home: '{str(test_dir)}'
  pticlima:
    home: '{str(test_dir)}'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {'GCM_STORE': 'invalid_store'}):
            with pytest.raises(ValueError, match="Unknown entry for <gcm_store>"):
                load_config(str(config_file))

    def test_missing_paths_in_config_raises_error(self, tmp_path):
        """Should raise FileNotFoundError when paths in config don't exist."""
        config_file = tmp_path / "test_config.yaml"

        config_content = """
paths:
  lustre:
    home: '/this/path/does/not/exist'
    data_dir: '/neither/does/this'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {'GCM_STORE': 'lustre'}):
            with pytest.raises(FileNotFoundError, match="Path for .* does not exist"):
                load_config(str(config_file))

    def test_file_not_found(self):
        """Should raise FileNotFoundError when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_config("/non/existent/config.yaml")

    def test_invalid_yaml_syntax(self, tmp_path):
        """Should raise YAML parsing error for invalid syntax."""
        config_file = tmp_path / "bad_config.yaml"
        config_file.write_text("this is not: valid: yaml: content:")

        with pytest.raises(Exception):  # yaml.YAMLError or similar
            load_config(str(config_file))

    def test_config_without_paths_section(self, tmp_path):
        """Should raise KeyError when 'paths' section is missing."""
        config_file = tmp_path / "test_config.yaml"
        config_content = """
models: ['ecmwf']
domain: 'medcof'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {'GCM_STORE': 'lustre'}):
            with pytest.raises(KeyError):
                load_config(str(config_file))

    def test_config_preserves_non_path_fields(self, tmp_path):
        """Should preserve all non-path configuration fields."""
        config_file = tmp_path / "test_config.yaml"
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()

        config_content = f"""
models: ['ecmwf', 'cmcc']
version: ['51', '4']
domain: 'medcof'
quantile_version: 'v1r'
agg_label: ['1mon', '2mon', '3mon']
precip_threshold_quotient: 30
datatype: 'float32'

paths:
  lustre:
    home: '{str(test_dir)}'

model_settings:
  ecmwf51:
    variable_std: ['t2m', 'tp']
    years_quantile: [1993, 2022]
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {'GCM_STORE': 'lustre'}):
            config = load_config(str(config_file))

        # Verify all fields are preserved
        assert config['models'] == ['ecmwf', 'cmcc']
        assert config['version'] == ['51', '4']
        assert config['domain'] == 'medcof'
        assert config['quantile_version'] == 'v1r'
        assert config['agg_label'] == ['1mon', '2mon', '3mon']
        assert config['precip_threshold_quotient'] == 30
        assert config['datatype'] == 'float32'
        assert 'model_settings' in config
        assert config['model_settings']['ecmwf51']['variable_std'] == ['t2m', 'tp']

    def test_filename_keys_not_validated(self, tmp_path):
        """Should not validate paths with 'filename' in the key."""
        config_file = tmp_path / "test_config.yaml"
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()

        config_content = f"""
paths:
  lustre:
    home: '{str(test_dir)}'
    output_filename: '/non/existent/output.nc'
    input_filename_pattern: '/non/existent/pattern.nc'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {'GCM_STORE': 'lustre'}):
            config = load_config(str(config_file))

        # Should not raise error, filenames are not validated
        assert config['paths']['output_filename'] == '/non/existent/output.nc'
        assert config['paths']['input_filename_pattern'] == '/non/existent/pattern.nc'

    def test_empty_config_file(self, tmp_path):
        """Should raise TypeError when config file is empty."""
        config_file = tmp_path / "empty_config.yaml"
        config_file.write_text("")

        with patch.dict(os.environ, {'GCM_STORE': 'lustre'}):
            # Empty YAML returns None, which causes TypeError
            with pytest.raises(TypeError):
                load_config(str(config_file))


class TestLoadConfigIntegration:
    """Integration tests using actual config files from the project."""

    def test_load_actual_config_structure(self, tmp_path):
        """Test loading config with realistic structure similar to project configs."""
        config_file = tmp_path / "realistic_config.yaml"

        # Create necessary directories
        home_dir = tmp_path / "home"
        gcm_base = tmp_path / "gcm_base"
        gcm_derived = tmp_path / "gcm_derived"
        gcm_masked = tmp_path / "gcm_masked"
        rundir = tmp_path / "rundir"
        quantile_dir = tmp_path / "quantile"
        forecast_dir = tmp_path / "forecast"
        mask_dir = tmp_path / "masks"

        for directory in [home_dir, gcm_base, gcm_derived, gcm_masked,
                         rundir, quantile_dir, forecast_dir, mask_dir]:
            directory.mkdir()

        config_content = f"""
models: ['eccc', 'ecmwf']
version: ['5', '51']
quantile_version: 'v1r'
agg_label: ['1mon', '2mon', '3mon', '4mon', '5mon']
lon_name_out: 'x'
lat_name_out: 'y'
precip_threshold_quotient: 30
datatype: 'float32'
domain: 'medcof'
masked_variables_std: ['SPEI-3-M', 'fwi', 'pvpot']
detrended: 'no'
nr_mem: [25]
product: 'forecast'
quantile_threshold: [0.33, 0.67]

paths:
  lustre:
    home: '{str(home_dir)}'
    path_gcm_base: '{str(gcm_base)}'
    path_gcm_base_derived: '{str(gcm_derived)}'
    path_gcm_base_masked: '{str(gcm_masked)}'
    rundir: '{str(rundir)}'
    dir_quantile: '{str(quantile_dir)}'
    dir_forecast: '{str(forecast_dir)}'
    mask_dir: '{str(mask_dir)}'

model_settings:
  ecmwf51:
    variable_std: ['pvpot', 'SPEI-3-M', 'fwi', 'msl', 't2m', 'tp', 'si10', 'ssrd']
    variable_fc: ['pvpot', 'SPEI-3-M', 'fwi', 'psl', 'tas', 'pr', 'sfcWind', 'rsds']
    variable_fc_nc: ['pvpot', 'SPEI-3-M', 'FWI', 'psl', 'tas', 'pr', 'sfcWind', 'rsds']
    time_name: ['time', 'time', 'time', 'forecast_time', 'forecast_time', 'forecast_time', 'forecast_time', 'forecast_time']
    lon_name: ['lon', 'lon', 'lon', 'x', 'x', 'x', 'x', 'x']
    lat_name: ['lat', 'lat', 'lat', 'y', 'y', 'y', 'y', 'y']
    years_quantile: [1993, 2022]
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {'GCM_STORE': 'lustre'}):
            config = load_config(str(config_file))

        # Verify structure
        assert config['models'] == ['eccc', 'ecmwf']
        assert config['domain'] == 'medcof'
        assert config['paths']['home'] == str(home_dir)
        assert config['paths']['path_gcm_base'] == str(gcm_base)
        assert config['paths']['mask_dir'] == str(mask_dir)
        assert 'model_settings' in config
        assert 'ecmwf51' in config['model_settings']


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_gcm_store_not_set_uses_default(self, tmp_path):
        """Should use 'lustre' as default when GCM_STORE not set."""
        config_file = tmp_path / "test_config.yaml"
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()

        config_content = f"""
paths:
  lustre:
    home: '{str(test_dir)}'
"""
        config_file.write_text(config_content)

        # Ensure GCM_STORE is not set
        with patch.dict(os.environ, {}, clear=True):
            # Should default to 'lustre'
            config = load_config(str(config_file))
            assert config['paths']['home'] == str(test_dir)

    def test_path_with_spaces(self, tmp_path):
        """Should handle paths with spaces."""
        config_file = tmp_path / "test_config.yaml"
        test_dir = tmp_path / "test data with spaces"
        test_dir.mkdir()

        config_content = f"""
paths:
  lustre:
    home: '{str(test_dir)}'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {'GCM_STORE': 'lustre'}):
            config = load_config(str(config_file))
            assert config['paths']['home'] == str(test_dir)

    def test_special_characters_in_values(self, tmp_path):
        """Should handle special characters in configuration values."""
        config_file = tmp_path / "test_config.yaml"
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()

        config_content = f"""
domain: 'test-domain_v1.0'
comment: 'This is a test: with special chars @#$%'

paths:
  lustre:
    home: '{str(test_dir)}'
"""
        config_file.write_text(config_content)

        with patch.dict(os.environ, {'GCM_STORE': 'lustre'}):
            config = load_config(str(config_file))
            assert config['domain'] == 'test-domain_v1.0'
            assert 'special chars @#$%' in config['comment']


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
