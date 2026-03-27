---
description: Automatically generates properly encoded MT5 Setfiles (UTF-16LE with BOM) for new GU experiments based on user discussion.
---

# Workflow: `/create-sets`

When the user requests `/create-sets` (or asks to generate new MT5 setfiles based on a discussion), you must follow these exact steps to ensure the setfiles are properly encoded for MetaTrader 5.

## 1. Define the Configurations
Based on the agreed-upon test sets, create a JSON file in `/tmp/new_sets.json` outlining the modifications needed from the base `gu_template.set` and `sl_template.set`. 

The JSON should be a list of dictionaries. For each dictionary:
- `name`: The core name of the file (e.g. `test_20`). This will generate `gu_test_20.set` and `sl_test_20.set`.
- `gu`: A key-value dictionary of the exact parameter names and their new values for the EA.
- `sl`: A key-value dictionary of the exact parameter names and their new values for SL Maestro.

Example `/tmp/new_sets.json`:
```json
[
  {
    "name": "test_20",
    "gu": {
      "InpMagicNumber": 28260320,
      "InpCommentTag": "GU_TEST_20",
      "InpCooldownMin": 1,
      "InpMAFast": 10,
      "InpMASlow": 40
    },
    "sl": {
      "comment_to_include": "GU_TEST_20",
      "sl_type": 4,
      "sl_atr_period": 60,
      "sl_atr_multiplier": 1.5
    }
  }
]
```

// turbo-all
## 2. Generate the Setfiles
Execute the built-in python script passing the JSON definition you just created. This script automatically handles reading the templates, injecting your values, and writing the final files encoded in strict MT5 `UTF-16LE + BOM` format into `c:\Trading_GU\Setfiles`.

```shell
python c:\Trading_GU\.agents\scripts\create_sets.py /tmp/new_sets.json
```

## 3. Notify the User
Inform the user that the new `gu_` and `sl_` setfiles have been generated in `c:\Trading_GU\Setfiles` and are ready to be dragged into their terminal. Remind them to check `knowledge_base.md` if the configurations represent a structural shift that needs tracking.
