from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Union

import yaml

from app.evaluator.consts import ESeverity
from app.evaluator.helpers import configuration_mapper, severity_evaluator


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigStore(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.opposite = {}
        self.covariation = {}
        self.pearson = {}
        self.area = {}
        with open(Path("app/evaluator/config.yaml"), "r") as f:
            config = yaml.safe_load(f)
            self.opposite = config.get("opposite", {})
            self.covariation = config.get("covariation", {})
            self.pearson = config.get("pearson", {})
            self.area = config.get("area", {})


class ChannelData:
    def __init__(
        self,
        channel: Union[str, None],
        channel_alias: Union[str, None],
        voltage: Union[List[float], None],
        timestamp: Union[str, None],
    ) -> None:
        self.channel = channel
        self.channel_alias = channel_alias
        self.voltage = voltage
        self.timestamp = timestamp

    @staticmethod
    def deserialize(hit: Optional[Union[None, Dict[str, str]]] = None):
        _source = hit.get("_source", {}) if hit else {}
        ch = _source.get("channel")
        ch_alias = _source.get("channel_alias", ch)
        voltage = _source.get("voltage")
        validated_voltage = (
            voltage
            if isinstance(voltage, list)
            else None
            # and (
            #     len(voltage) == 0 or len(voltage) == 4096 # == 0 if noise oscillo script sends empty array which is valid else 4096
            # )
        )
        timestamp = _source.get("timestamp_read_measurement")
        return ChannelData(ch, ch_alias, validated_voltage, timestamp)


class MeasurementData:
    def __init__(self, bulk_id: str) -> None:
        self.bulk_id = bulk_id
        self.timestamp = None
        self.ch1 = ChannelData.deserialize()
        self.ch2 = ChannelData.deserialize()
        self.ch3 = ChannelData.deserialize()
        self.ch4 = ChannelData.deserialize()

    def is_valid(self):
        return (
            True
            if (
                self.timestamp
                and (
                    self.ch1.voltage
                    and self.ch2.voltage
                    and self.ch3.voltage
                    and self.ch4.voltage
                    # (not self.ch1.voltage or len(self.ch1.voltage == n_samples))
                    # and (not self.ch2.voltage or len(self.ch2.voltage == n_samples))
                    # and (not self.ch3.voltage or len(self.ch3.voltage == n_samples))
                    # and (not self.ch4.voltage or len(self.ch4.voltage == n_samples))
                )
            )
            else False
        )

    @staticmethod
    def deserialize(bulk_id: str, buckets: Optional[List[Dict[str, str]]] = None):
        measurement_data = MeasurementData(bulk_id)
        if not buckets:
            return measurement_data
        for i, bucket in enumerate(buckets):
            channel = bucket.get("key")
            ch_hits = bucket.get("data", {}).get("hits", {}).get("hits", None)
            hit = ch_hits[0] if ch_hits else None
            ch_data = ChannelData.deserialize(hit)
            # if all channel's timestamps are in sync measurement_data.timestamp would not be None
            if i == 0:
                measurement_data.timestamp = ch_data.timestamp
            elif measurement_data.timestamp != ch_data.timestamp:
                measurement_data.timestamp = None  # setting None for timestamp which is used within is_valid function to validate measurement
            setattr(measurement_data, channel, ChannelData.deserialize(hit))
        return measurement_data


class KORule:
    def __init__(
        self,
        ok: bool,
        serialized: Optional[Dict[Any, Any]] = None,
        info: Optional[str] = None,
    ):
        self.ok = ok
        # self.value = value
        # self.threshold = threshold
        self.serialized = serialized
        self.info = info

    def serialize(self):
        obj = {
            "ok": self.ok,
        }
        if self.serialized is not None:
            obj = {**obj, **self.serialized}
        return obj


class SeverityWithAnomalousFeatures:
    def __init__(
        self
        # , evaluation_values: "EvaluationValues"
        ,
        evaluation_values: "EvaluationValues",
        severity: Union[None, ESeverity],
        anomalous_features: Union[None, Dict[Literal["ch1", "ch2", "ch3", "ch4"], str]],
        threshold_data: Optional[Dict[Any, Any]] = None,
    ) -> None:
        # self.evaluation_values: EvaluationValues = evaluation_values
        # self.evaluation_method_serialized_data = evaluation_method_serialized_data
        self.evaluation_values = evaluation_values
        self.severity = severity
        self.anomalous_features = anomalous_features
        self.threshold_data = threshold_data

    def serialize(self):
        obj = {
            "stats": self.evaluation_values.serialize(),
            "severity": self.severity,
            "anomalous_features": self.anomalous_features,
        }
        if self.threshold_data:
            obj["thresholds"] = self.threshold_data
        return obj


# class EvaluationValueInner:
#     def __init__(
#         self
#         , value: float
#         , ch_alias: str
#     ) -> None:
#         self.value = value
#         self.ch_alias = ch_alias


class EvaluationValues:
    def __init__(self, ch1: float, ch2: float, ch3: float, ch4: float) -> None:
        self.ch1 = ch1
        self.ch2 = ch2
        self.ch3 = ch3
        self.ch4 = ch4
        self.serialize: Callable[..., Dict[Any, Any]] = lambda: {}

    def future_serialized_as(self, callback: Callable[..., Dict[Any, Any]]):
        self.serialize = callback
        return self

    def evaluate(
        self,
        callback: Callable[
            ["EvaluationValues", "MeasurementData"], SeverityWithAnomalousFeatures
        ],
    ):
        return callback(self)


class CombinatorOutput:
    def __init__(
        self,
        severity: Union[None, ESeverity],
        anomalies: Optional[Union[None, Dict[Any, Any]]] = None,
    ) -> None:
        self.severity = severity
        self.anomalies = anomalies


class OscilloConfigurationEvaluationResult:
    def __init__(
        self,
        configuration: str
        # , rule1: KORule
        # , rule2: KORule
        # , rule3: KORule
        ,
        combinator: Callable[
            [bool, SeverityWithAnomalousFeatures, SeverityWithAnomalousFeatures],
            CombinatorOutput,
        ],
    ) -> None:
        self.configuration = configuration
        # self.rule1 = rule1
        # self.rule2 = rule2
        # self.rule3 = rule3
        self.pearson: SeverityWithAnomalousFeatures = None
        self.area: SeverityWithAnomalousFeatures = None
        self.combinator = combinator  # Todo instead of passing combinator callback to serialize pass it per config

    @property
    def combinator_output(self) -> CombinatorOutput:
        return self.combinator(
            # self.rule1, self.rule2, self.rule3
            self.pearson,
            self.area,
        )

    # @property
    # def severity(self):
    #     return self.combinator_output.s
    # @property
    # def severity(self):
    #     # Todo this severity is not relevant, MUST use that one that comes from combinator, must access combinators result severity. Return dto from combinator with severity and combined anomalous features

    #     # ko_rules_not_satisfied = any([
    #     #     self.rule1, self.rule2, self.rule3
    #     # ])
    #     return severity_evaluator([
    #         self.pearson.severity, self.area.severity
    #         # , ESeverity.ALARM if not ko_rules_not_satisfied else None
    #     ])
    #     # severity_data = list(filter(
    #     #     lambda q: q, [self.pearson.severity, self.area.severity]
    #     # )) # filter and use only initialized and computed statistic methods
    #     # return (
    #     #     ESeverity.ALARM
    #     #     if ESeverity.ALARM in severity_data
    #     #     else ESeverity.Warning if ESeverity.WARNING in severity_data
    #     #     else None
    #     # )

    def serialize(
        self,
        # , combinator: Callable[
        #     [bool, SeverityWithAnomalousFeatures, SeverityWithAnomalousFeatures]
        #     , Union[None, CombinatorOutput]
        # ]
    ):
        # Todo here must access combinators result severity. Return dto from combinator with severity and combined anomalous features
        # combinator_output = combinator(
        #     all([self.rule1, self.rule2, self.rule3])
        #     , self.pearson
        #     , self.area
        # )
        obj = {
            "alias": configuration_mapper(self.configuration),
            # "rules": {
            #     "rule1": self.rule1.serialize(),
            #     "rule2": self.rule2.serialize(),
            #     "rule3": self.rule3.serialize(),
            # },
            "methods": {
                "pearson": self.pearson.serialize(),
                "area": self.area.serialize(),
            },
            # "anomalous_features": {
            #     **combinator(
            #         all([self.rule1, self.rule2, self.rule3])
            #         , self.pearson
            #         , self.area
            #     )
            # },
            "severity": self.combinator_output.severity,
        }

        if isinstance(self.combinator_output.anomalies, dict):
            obj["anomalies"] = {**self.combinator_output.anomalies}
        return obj


class OscilloEvaluationResult:
    def __init__(
        self,
        bulk_id: str,
        timestamp: str,
        timestamp_evaluation: str,
        rule1: Optional[KORule] = None,
        rule2: Optional[KORule] = None,
        rule3: Optional[KORule] = None,
    ) -> None:
        self.bulk_id = bulk_id
        self.timestamp = timestamp
        self.timestamp_evaluation = timestamp_evaluation
        self.rule1 = rule1
        self.rule2 = rule2
        self.rule3 = rule3
        self.config_evaluations: Dict[str, OscilloConfigurationEvaluationResult] = {}

    def serialize(
        self,
        # , combinator: Callable[
        #     [bool, SeverityWithAnomalousFeatures, SeverityWithAnomalousFeatures]
        #     , Union[None, CombinatorOutput]
        # ]
    ):
        severities = [
            ce.combinator_output.severity for ce in self.config_evaluations.values()
        ]
        identified_configuration = None
        for cfg, evaluation in self.config_evaluations.items():
            if not evaluation.combinator_output.severity:
                identified_configuration = cfg  # configuration_mapper(cfg)
                break
        # else:
        #     identified_configuration = configuration_mapper()

        obj = {
            "bulk_id": self.bulk_id,
            "timestamp": self.timestamp,
            "timestamp_evaluation": self.timestamp_evaluation,
            # "evaluation": {
            #     **{
            #         cfg: cfg_data.serialize()
            #         for cfg, cfg_data in self.config_evaluations.items()
            #     }
            # },
            "configuration": identified_configuration,
            "severity": (
                None
                if None
                in severities  # ! if at least one severity is None not an anomaly
                else severity_evaluator(severities)
            ),
        }
        if all((self.rule1, self.rule2, self.rule3)):
            obj["rules"] = {
                "rule1": self.rule1.serialize(),
                "rule2": self.rule2.serialize(),
                "rule3": self.rule3.serialize(),
            }
        if self.config_evaluations:
            obj["evaluation"] = {
                **{
                    cfg: cfg_data.serialize()
                    for cfg, cfg_data in self.config_evaluations.items()
                }
            }

        return obj
