import logging
from typing import Dict, List, Literal, Union

import numpy as np
from scipy.integrate import simpson
from scipy.stats import pearsonr

from app.dtos import (
    ChannelData,
    CombinatorOutput,
    ConfigStore,
    ESeverity,
    EvaluationValues,
    KORule,
    MeasurementData,
    SeverityWithAnomalousFeatures,
)
from app.evaluator.consts import CHANNELS
from app.evaluator.helpers import severity_evaluator

logger = logging.getLogger(__name__)


def opposite_values(ch3: ChannelData, ch4: ChannelData):
    """
    check if two functions have opposite values
    """
    IDX = ConfigStore().opposite.get("index", 1850)
    DIFF = ConfigStore().opposite.get("diff", 0.5)
    result = (
        ch3.voltage[IDX] < ch4.voltage[IDX]
        and ch4.voltage[IDX] - ch3.voltage[IDX] > DIFF
    )
    return KORule(
        ok=result,
        serialized={
            "ch3": ch3.voltage[IDX],
            "ch4": ch4.voltage[IDX],
            "diff": ch4.voltage[IDX] - ch3.voltage[IDX],
            "threshold_diff": DIFF,
        },
        info=(
            None
            if result
            else "Channels {} and {} are not inverted".format(
                ch3.channel_alias, ch4.channel_alias
            )
        ),
    )


def covariation_check(ch: ChannelData, threshold: float):
    """
    covariation coeficient for the window of the function
    """
    data = ch.voltage[
        ConfigStore()
        .covariation.get("start", 1650) : ConfigStore()
        .covariation.get("end", 2000)
    ]

    # define function to calculate covariation
    cv = lambda x: np.std(x, ddof=1) / np.mean(x)

    covariation = cv(data)
    result = bool(covariation < threshold)
    return KORule(
        ok=result,
        serialized={"covariation": float(covariation), "threshold": threshold},
        info=(
            None
            if result
            else "Channel {} covariation below threshold".format(ch.channel_alias)
        ),
    )


def pearson(
    measurement_data: MeasurementData,
    reference: Dict[Literal["ch1", "ch2", "ch3", "ch4"], List[float]],
):
    ch1 = pearsonr(measurement_data.ch1.voltage, reference["ch1"])
    ch2 = pearsonr(measurement_data.ch2.voltage, reference["ch2"])
    ch3 = pearsonr(measurement_data.ch3.voltage, reference["ch3"])
    ch4 = pearsonr(measurement_data.ch4.voltage, reference["ch4"])
    return EvaluationValues(
        float(ch1.correlation),
        float(ch2.correlation),
        float(ch3.correlation),
        float(ch4.correlation),
    )


def evaluate_pearson(ev: EvaluationValues, measurement_data: MeasurementData):
    severities = []
    anomalous_features = {}
    # with open(Path("app/evaluator/config.yaml"), "r") as f:
    #     config = yaml.safe_load(f)
    WARNING_THRESHOLD = ConfigStore().pearson.get(ESeverity.WARNING.casefold())
    ALARM_THRESHOLD = ConfigStore().pearson.get(ESeverity.ALARM.casefold())
    for ch in CHANNELS:
        ch_value: Union[float, None] = getattr(ev, ch, None)
        ch_data: Union[ChannelData, None] = getattr(measurement_data, ch, None)
        ch_alias = ch_data.channel_alias if isinstance(ch_data, ChannelData) else None
        if not ch_value:
            continue
        if ch_value <= WARNING_THRESHOLD:
            anomalous_features[ch] = ch_alias
        if ALARM_THRESHOLD < ch_value <= WARNING_THRESHOLD:
            severities.append(ESeverity.WARNING)
        elif ch_value <= ALARM_THRESHOLD:
            severities.append(ESeverity.ALARM)
    return SeverityWithAnomalousFeatures(
        # ev.serialize(
        #     lambda e: {
        #         "ch1": float(e.ch1.value),
        #         "ch2": float(e.ch2.value),
        #         "ch3": float(e.ch3.value),
        #         "ch4": float(e.ch4.value)
        #     }
        # )
        ev.future_serialized_as(
            lambda: {"ch1": ev.ch1, "ch2": ev.ch2, "ch3": ev.ch3, "ch4": ev.ch4}
        )
        # {
        #     "ch1": float(ev.ch1.value),
        #     "ch2": float(ev.ch2.value),
        #     "ch3": float(ev.ch3.value),
        #     "ch4": float(ev.ch4.value)
        # }
        ,
        severity_evaluator(severities, take_worst=True),
        anomalous_features if anomalous_features else None,
        threshold_data={
            ESeverity.ALARM: ALARM_THRESHOLD,
            ESeverity.WARNING: WARNING_THRESHOLD,
        },
    )
    # config_3["severity"] = None
    # # config_3["anomalous_features"] = []
    # config_3["anomalous_features"] = {}
    # is_alarm = False
    # is_warning = False

    # if (config_3["ch1"] > config_3["ch1_threshold"]*config["anomaly_limit"]["alarm"] or
    #         config_3["ch2"] > config_3["ch2_threshold"]*config["anomaly_limit"]["alarm"] or
    #         config_3["ch3"] > config_3["ch3_threshold"]*config["anomaly_limit"]["alarm"] or
    #         config_3["ch4"] > config_3["ch4_threshold"]*config["anomaly_limit"]["alarm"]):

    #     is_alarm = True

    # if config_3["ch1"] > config_3["ch1_threshold"]*config["anomaly_limit"]["warning"]:
    #     config_3["anomalous_features"]["ch1"] = aliases.get("ch1", "ch1")
    #     is_warning = True
    # if config_3["ch2"] > config_3["ch2_threshold"]*config["anomaly_limit"]["warning"]:
    #     config_3["anomalous_features"]["ch2"] = aliases.get("ch2", "ch2")
    #     is_warning = True
    # if config_3["ch3"] > config_3["ch3_threshold"]*config["anomaly_limit"]["warning"]:
    #     config_3["anomalous_features"]["ch3"] = aliases.get("ch3", "ch3")
    #     is_warning = True
    # if config_3["ch4"] > config_3["ch4_threshold"]*config["anomaly_limit"]["warning"]:
    #     config_3["anomalous_features"]["ch4"] = aliases.get("ch4", "ch4")
    #     is_warning = True

    # if not config_3["rule_1"] or not config_3["rule_2"] or not config_3["rule_3"]:
    #     config_3["anomalous_features"]["KO"] = "KO"
    #     config_3["severity"] = "Alarm"

    # if is_alarm:
    #     config_3["severity"] = "Alarm"
    # elif is_warning:
    #     config_3["severity"] = "Warning"


def area(
    measurement_data: MeasurementData,
    reference: Dict[Literal["ch1", "ch2", "ch3", "ch4"], List[float]],
):
    from similaritymeasures import area_between_two_curves

    x = [i for i in range(4096)]
    area_ch1 = area_between_two_curves(
        np.array([x, measurement_data.ch1.voltage]).T, np.array([x, reference["ch1"]]).T
    )
    area_ch2 = area_between_two_curves(
        np.array([x, measurement_data.ch2.voltage]).T, np.array([x, reference["ch2"]]).T
    )
    area_ch3 = area_between_two_curves(
        np.array([x, measurement_data.ch3.voltage]).T, np.array([x, reference["ch3"]]).T
    )
    area_ch4 = area_between_two_curves(
        np.array([x, measurement_data.ch4.voltage]).T, np.array([x, reference["ch4"]]).T
    )
    # Compute the area under the reference curve
    # ch1_reference_area = simpson(np.abs(reference["ch1"]))
    # ch2_reference_area = simpson(np.abs(reference["ch2"]))
    # ch3_reference_area = simpson(np.abs(reference["ch3"]))
    # ch4_reference_area = simpson(np.abs(reference["ch4"]))

    # # Compute the absolute difference between the two curves
    # ch1_y_diff = np.abs(np.array(measurement_data.ch1.voltage) - np.array(reference["ch1"]))
    # ch1_area = simpson(ch1_y_diff)
    # ch2_y_diff = np.abs(np.array(measurement_data.ch2.voltage) - np.array(reference["ch2"]))
    # ch2_area = simpson(ch2_y_diff)
    # ch3_y_diff = np.abs(np.array(measurement_data.ch3.voltage) - np.array(reference["ch3"]))
    # ch3_area = simpson(ch3_y_diff)
    # ch4_y_diff = np.abs(np.array(measurement_data.ch4.voltage) - np.array(reference["ch4"]))
    # ch4_area = simpson(ch4_y_diff)

    # # Calculate similarity percentage
    # ch1_similarity_percentage = (1 - (ch1_area / ch1_reference_area)) * 100# Calculate similarity percentage
    # ch2_similarity_percentage = (1 - (ch2_area / ch2_reference_area)) * 100# Calculate similarity percentage
    # ch3_similarity_percentage = (1 - (ch3_area / ch3_reference_area)) * 100# Calculate similarity percentage
    # ch4_similarity_percentage = (1 - (ch4_area / ch4_reference_area)) * 100
    return EvaluationValues(
        float(area_ch1), float(area_ch2), float(area_ch3), float(area_ch4)
    )


def evaluate_area(ev: EvaluationValues, measurement_data: MeasurementData):
    severities = []
    anomalous_features = {}
    WARNING_THRESHOLD = ConfigStore().area.get(ESeverity.WARNING.casefold())
    ALARM_THRESHOLD = ConfigStore().area.get(ESeverity.ALARM.casefold())
    for ch in CHANNELS:
        ch_value: Union[float, None] = getattr(ev, ch, None)
        ch_data: Union[ChannelData, None] = getattr(measurement_data, ch, None)
        ch_alias = ch_data.channel_alias if isinstance(ch_data, ChannelData) else None
        if not ch_value:
            continue
        if ch_value >= WARNING_THRESHOLD:
            anomalous_features[ch] = ch_alias
        if WARNING_THRESHOLD < ch_value < ALARM_THRESHOLD:
            severities.append(ESeverity.WARNING)
        elif ch_value >= ALARM_THRESHOLD:
            severities.append(ESeverity.ALARM)
    return SeverityWithAnomalousFeatures(
        # ev.serialize(
        #     lambda e: {
        #         "ch1": e.ch1.value,
        #         "ch2": e.ch2.value,
        #         "ch3": e.ch3.value,
        #         "ch4": e.ch4.value
        #     }
        # )
        # {
        #     "ch1": ev.ch1.value,
        #     "ch2": ev.ch2.value,
        #     "ch3": ev.ch3.value,
        #     "ch4": ev.ch4.value
        # }
        ev.future_serialized_as(
            lambda: {"ch1": ev.ch1, "ch2": ev.ch2, "ch3": ev.ch3, "ch4": ev.ch4}
        ),
        severity_evaluator(severities, take_worst=True),
        anomalous_features if anomalous_features else None,
        threshold_data={
            ESeverity.ALARM: ALARM_THRESHOLD,
            ESeverity.WARNING: WARNING_THRESHOLD,
        },
    )


def combine_ko_pearson_and_area_anomalous_features(
    rule1: KORule,
    rule2: KORule,
    rule3: KORule,
    pearson: SeverityWithAnomalousFeatures,
    area: SeverityWithAnomalousFeatures,
):
    rules = [rule1, rule2, rule3]
    kos_satisfied = all(map(lambda r: r.ok, rules))
    combined_severity = severity_evaluator(
        [
            ESeverity.ALARM if not kos_satisfied else None,
            pearson.severity,
            area.severity,
        ],
        take_worst=True,
    )
    if kos_satisfied and not pearson.anomalous_features and not area.anomalous_features:
        return CombinatorOutput(severity=combined_severity)
    anomalous_features = {}
    if not kos_satisfied:
        kos = ""
        for rule in filter(lambda r: not r.ok, rules):
            kos = "{}, {}".format(kos, rule.info) if kos else rule.info
        if kos:
            anomalous_features["ko"] = kos
        # anomalous_features["KO"] = "Curves positions: KO criteria not satisfied - curves positions KO rules not satisfied"

    anomalous_features["pearson"] = {}
    if pearson.anomalous_features:
        for ch, ch_alias in pearson.anomalous_features.items():
            value: Union[float, None] = getattr(pearson.evaluation_values, ch, None)
            if not value:
                continue
            anomalous_features["pearson"][ch_alias] = value  # percentage of difference
    if not anomalous_features["pearson"]:
        anomalous_features.pop("pearson")

    anomalous_features["area"] = {}
    if area.anomalous_features:
        for ch, ch_alias in area.anomalous_features.items():
            value: Union[float, None] = getattr(area.evaluation_values, ch, None)
            #! if we already have anomalous feature identified by pearson, which is prioritized,
            #! do not override it by area
            if not value or ch_alias in anomalous_features:
                continue
            anomalous_features["area"][ch_alias] = value  # percentage of difference
    if not anomalous_features["area"]:
        anomalous_features.pop("area")

    return CombinatorOutput(combined_severity, anomalous_features)
