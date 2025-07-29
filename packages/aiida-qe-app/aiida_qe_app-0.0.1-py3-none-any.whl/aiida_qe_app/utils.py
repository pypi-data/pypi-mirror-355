import sys


# functions to get entry points is copied from aiidalab_qe.app.utils
# because we want to decouple the workflows from the app, so I copied it here
# instead of importing it.
# load entry points


def get_entries(entry_point_name="aiidalab_qe.property"):
    from importlib.metadata import entry_points

    entries = {}
    eps = entry_points()
    if sys.version_info >= (3, 10):
        group = eps.select(group=entry_point_name)
    else:
        group = eps.get(entry_point_name, [])
    for entry_point in group:
        try:
            # Attempt to load the entry point
            loaded_entry_point = entry_point.load()
            entries[entry_point.name] = loaded_entry_point
        except Exception as e:
            # Handle loading errors
            print(f"Failed to load entry point {entry_point.name}: {e}")

    return entries


# load entry point items
def get_entry_items(entry_point_name, item_name="workchain"):
    entries = get_entries(entry_point_name)
    return {
        name: entry_point.get(item_name)
        for name, entry_point in entries.items()
        if entry_point.get(item_name, False)
    }


plugin_entries = get_entry_items("aiidalab_qe.properties", "workchain")
