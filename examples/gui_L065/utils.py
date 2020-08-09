import json


def json_boot_routine(file):
    config = {}

    with open(file) as f:
        config = json.load(f)
        f.close()

    config["clean_exit"] = False
    config["boot_count"] += 1

    with open(file, 'w') as f:
        json.dump(config, f, sort_keys=True, indent=4)

    return config


def json_exit_routine(file, config):
    config["clean_exit"] = True
    with open(file, 'w') as f:
        json.dump(config, f, sort_keys=True, indent=4)
