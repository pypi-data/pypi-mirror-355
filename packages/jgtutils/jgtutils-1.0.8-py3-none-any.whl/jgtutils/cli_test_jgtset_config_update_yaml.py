#%%
from io import StringIO
# Optional YAML support - graceful fallback to JSON-only if not available
try:
    import ruamel.yaml
    yaml = ruamel.yaml.YAML()
    HAS_YAML = True
except ImportError:
    yaml = None
    HAS_YAML = False

book_config_file="_config.yml" #Probably related to that experimentation that when launching a trading campaign, jupyter book is created therefore, we store configuration into the jupyter book config file

import jgtset as jset
jgtset_included_keys = "_jgtset_included.json"

updated_yaml_data=jset.update_jgt_on_existing_yaml_file(custom_path=jgtset_included_keys, target_filepath=book_config_file)
# %%
stream = StringIO()
yaml.dump(updated_yaml_data, stream)
print(stream.getvalue())



