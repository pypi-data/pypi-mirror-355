def get_excluded_fields_for_model(live_model):
    if not hasattr(live_model, "excluded_diff_fields"):
        return ["id"]

    return ["id", *live_model.excluded_diff_fields]


def get_diffable_fields_for_model(live_model):
    history_model = live_model._history_class
    all_fields = [
        *history_model.get_fields_to_version(),
        *history_model.get_m2m_fields_to_version(),
    ]

    excluded = get_excluded_fields_for_model(live_model)

    ret = []
    for f in all_fields:
        if f.name in excluded:
            continue
        ret.append(f)

    return ret
