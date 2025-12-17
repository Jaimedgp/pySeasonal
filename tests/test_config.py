#!/usr/bin/env python

"""
Comprehensive test suite for config.py module.

Tests cover:
- _check_paths_exist() function
  - Valid paths that exist
  - Missing paths that should raise FileNotFoundError
  - Paths with 'filename' in key (should be skipped)
  - Empty 'home' path (should be skipped)
  - Empty dictionaries
- load_config() function
  - Valid config file loading
  - Path validation within config
  - Invalid/missing config files
  - Missing 'paths' section
  - YAML structure validation
"""

import os
import pytest
from pathlib import Path

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

    def test_skip_empty_home_path(self, tmp_path):
        """Should skip validation for empty 'home' path."""
        existing_dir = tmp_path / "exists"
        existing_dir.mkdir()

        paths_dict = {
            "existing_path": str(existing_dir),
            "home": ""  # Empty home path should be skipped
        }

        # Should not raise error because empty 'home' is allowed
        assert _check_paths_exist(paths_dict) is True

    def test_non_empty_home_path_must_exist(self, tmp_path):
        """Should validate non-empty 'home' path."""
        paths_dict = {
            "home": "/this/path/does/not/exist"
        }

        # Non-empty home path must exist
        with pytest.raises(FileNotFoundError, match="Path for 'home' does not exist"):
            _check_paths_exist(paths_dict)

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

    def test_combination_of_skipped_and_validated_paths(self, tmp_path):
        """Should properly handle mix of skipped and validated paths."""
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()

        paths_dict = {
            "home": "",  # Skip empty home
            "valid_path": str(valid_dir),  # Validate this
            "output_filename": "/fake/file.nc",  # Skip filename
            "config_filename": "/another/fake.yaml"  # Skip filename
        }

        assert _check_paths_exist(paths_dict) is True


class TestLoadConfig:
    """Test cases for load_config() function."""

    def test_load_valid_config(self, tmp_path, capsys):
        """Should successfully load config with valid paths."""
        # Create a test config file
        config_file = tmp_path / "test_config.yaml"
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()

        config_content = f"""
models: ['ecmwf', 'cmcc']
version: ['51', '4']
domain: 'medcof'

paths:
  home: '{str(test_dir)}'
  path_gcm_base: '{str(test_dir)}'
  dir_forecast: '{str(test_dir)}'
"""
        config_file.write_text(config_content)

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

    def test_load_config_with_empty_home(self, tmp_path):
        """Should load config with empty home path."""
        config_file = tmp_path / "test_config.yaml"
        test_dir = tmp_path / "data"
        test_dir.mkdir()

        config_content = f"""
domain: 'test'

paths:
  home: ''
  data_path: '{str(test_dir)}'
"""
        config_file.write_text(config_content)

        config = load_config(str(config_file))

        assert config['paths']['home'] == ''
        assert config['paths']['data_path'] == str(test_dir)

    def test_missing_paths_in_config_raises_error(self, tmp_path):
        """Should raise FileNotFoundError when paths in config don't exist."""
        config_file = tmp_path / "test_config.yaml"

        config_content = """
paths:
  home: '/this/path/does/not/exist'
  data_dir: '/neither/does/this'
"""
        config_file.write_text(config_content)

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
  home: '{str(test_dir)}'

model_settings:
  ecmwf51:
    variable_std: ['t2m', 'tp']
    years_quantile: [1993, 2022]
"""
        config_file.write_text(config_content)

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
  home: '{str(test_dir)}'
  output_filename: '/non/existent/output.nc'
  input_filename_pattern: '/non/existent/pattern.nc'
"""
        config_file.write_text(config_content)

        config = load_config(str(config_file))

        # Should not raise error, filenames are not validated
        assert config['paths']['output_filename'] == '/non/existent/output.nc'
        assert config['paths']['input_filename_pattern'] == '/non/existent/pattern.nc'

    def test_empty_config_file(self, tmp_path):
        """Should raise error when config file is empty."""
        config_file = tmp_path / "empty_config.yaml"
        config_file.write_text("")

        # Empty YAML returns None, which causes error when accessing ['paths']
        with pytest.raises((KeyError, TypeError)):
            load_config(str(config_file))

    def test_paths_section_is_validated(self, tmp_path):
        """Should validate all paths in the 'paths' section."""
        config_file = tmp_path / "test_config.yaml"
        existing_dir = tmp_path / "exists"
        existing_dir.mkdir()

        config_content = f"""
domain: 'test'

paths:
  home: ''
  valid_path: '{str(existing_dir)}'
  invalid_path: '/does/not/exist'
"""
        config_file.write_text(config_content)

        with pytest.raises(FileNotFoundError, match="Path for 'invalid_path' does not exist"):
            load_config(str(config_file))


class TestLoadConfigIntegration:
    """Integration tests using realistic config structures."""

    def test_load_realistic_config_structure(self, tmp_path):
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

        config = load_config(str(config_file))

        # Verify structure
        assert config['models'] == ['eccc', 'ecmwf']
        assert config['domain'] == 'medcof'
        assert config['paths']['home'] == str(home_dir)
        assert config['paths']['path_gcm_base'] == str(gcm_base)
        assert config['paths']['mask_dir'] == str(mask_dir)
        assert 'model_settings' in config
        assert 'ecmwf51' in config['model_settings']

    def test_config_with_empty_home_and_filenames(self, tmp_path):
        """Test config with empty home and filename entries (common pattern)."""
        config_file = tmp_path / "test_config.yaml"
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        config_content = f"""
domain: 'argo'

paths:
  home: ''
  data_path: '{str(data_dir)}'
  output_filename: 'forecast.nc'
  mask_filename: 'land_sea_mask.nc'
"""
        config_file.write_text(config_content)

        config = load_config(str(config_file))

        assert config['paths']['home'] == ''
        assert config['paths']['data_path'] == str(data_dir)
        assert config['paths']['output_filename'] == 'forecast.nc'
        assert config['paths']['mask_filename'] == 'land_sea_mask.nc'


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_path_with_spaces(self, tmp_path):
        """Should handle paths with spaces."""
        config_file = tmp_path / "test_config.yaml"
        test_dir = tmp_path / "test data with spaces"
        test_dir.mkdir()

        config_content = f"""
paths:
  home: '{str(test_dir)}'
"""
        config_file.write_text(config_content)

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
  home: '{str(test_dir)}'
"""
        config_file.write_text(config_content)

        config = load_config(str(config_file))
        assert config['domain'] == 'test-domain_v1.0'
        assert 'special chars @#$%' in config['comment']

    def test_mixed_valid_and_invalid_paths(self, tmp_path):
        """Should fail if any non-skipped path is invalid."""
        config_file = tmp_path / "test_config.yaml"
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()

        config_content = f"""
paths:
  home: ''
  valid_path: '{str(valid_dir)}'
  output_filename: '/fake/output.nc'
  invalid_path: '/does/not/exist'
"""
        config_file.write_text(config_content)

        with pytest.raises(FileNotFoundError, match="Path for 'invalid_path' does not exist"):
            load_config(str(config_file))

    def test_only_skipped_paths(self, tmp_path):
        """Should succeed when only skipped paths are present."""
        config_file = tmp_path / "test_config.yaml"

        config_content = """
paths:
  home: ''
  output_filename: '/fake/output.nc'
  input_filename: '/fake/input.nc'
"""
        config_file.write_text(config_content)

        config = load_config(str(config_file))
        assert config['paths']['home'] == ''
        assert config['paths']['output_filename'] == '/fake/output.nc'

    def test_relative_paths(self, tmp_path):
        """Should handle relative paths correctly."""
        config_file = tmp_path / "test_config.yaml"
        
        # Create a relative directory from tmp_path
        rel_dir = tmp_path / "relative_dir"
        rel_dir.mkdir()

        config_content = f"""
paths:
  home: '{str(rel_dir)}'
"""
        config_file.write_text(config_content)

        config = load_config(str(config_file))
        assert config['paths']['home'] == str(rel_dir)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
