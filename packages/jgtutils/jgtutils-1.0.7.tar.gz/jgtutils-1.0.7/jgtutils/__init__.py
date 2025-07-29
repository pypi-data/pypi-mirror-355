"""
jgtutils package
"""

version='1.0.7'

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from jgtos import (tlid_range_to_jgtfxcon_start_end_str,
                   tlid_range_to_start_end_datetime)

import jgtcommon as common
import jgtos as jos
import jgtpov as pov
import jgtwslhelper as wsl
# Import from jgtcore for library functions
from jgtcore import get_config as core_get_config, get_setting as core_get_setting, setup_environment as core_setup_environment, get_config_value as core_get_config_value, is_demo_mode as core_is_demo_mode
from jgtcore import readconfig as core_readconfig, load_settings as core_load_settings, get_settings as core_get_settings
from jgtcore import dt_from_last_week_as_string_fxformat as dt_from_last_week

# Re-expose with original names
get_config = core_get_config
get_setting = core_get_setting  
setup_environment = core_setup_environment
get_config_value = core_get_config_value
is_demo_mode = core_is_demo_mode
readconfig = core_readconfig
load_settings = core_load_settings
get_settings = core_get_settings

# Import CLI-specific functions from jgtcommon
from jgtcommon import new_parser, parse_args
from jgtpov import calculate_tlid_range as get_tlid_range
from FXTransact import (FXTransactDataHelper as ftdh,
                        FXTransactWrapper as ftw)

from jgtclihelper import (print_jsonl_message as printl)

from jgtenv import load_dotjgt_env_sh,load_dotjgtset_exported_env,load_dotfxtrade_env,load_env

def load_logging():
  from jgtutils import jgtlogging as jlog

# Explicitly expose the simple API functions for external packages
__all__ = [
    # Simple API from jgtcore
    'get_config', 'get_setting', 'setup_environment', 'get_config_value', 'is_demo_mode',
    # Core functions from jgtcore  
    'readconfig', 'load_settings', 'get_settings',
    # Utilities
    'dt_from_last_week',
    # CLI functions
    'new_parser', 'parse_args',
    # Other utilities
    'get_tlid_range', 'ftdh', 'ftw', 'printl',
    'load_dotjgt_env_sh', 'load_dotjgtset_exported_env', 'load_dotfxtrade_env', 'load_env',
    # Modules
    'common', 'jos', 'pov', 'wsl',
    # Version
    'version'
]
