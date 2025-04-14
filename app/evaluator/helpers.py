from typing import List, Optional, Union

from app.evaluator.consts import CONFIG3, CONFIG4, ESeverity


def configuration_mapper(cfg: Optional[Union[None, str]] = None) -> str:
    return {CONFIG3: "Configuration 3", CONFIG4: "Configuration 4"}.get(
        cfg, "Unknow configuration"
    )


def severity_evaluator(
    severities: List[Union[None, ESeverity]], take_worst: Optional[bool] = False
):
    not_null_severities = list(
        set(filter(lambda q: q, severities))
    )  # filter and use only initialized and computed statistic methods
    if take_worst:
        return (
            ESeverity.ALARM
            if ESeverity.ALARM in not_null_severities
            else ESeverity.WARNING if ESeverity.WARNING in not_null_severities else None
        )
    else:
        return (
            ESeverity.ALARM
            if ESeverity.ALARM in not_null_severities
            and ESeverity.WARNING not in not_null_severities
            else ESeverity.WARNING if ESeverity.WARNING in not_null_severities else None
        )
