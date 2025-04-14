import logging
from datetime import datetime as dt
from datetime import timezone

from app.dtos import (
    ConfigStore,
    MeasurementData,
    OscilloConfigurationEvaluationResult,
    OscilloEvaluationResult,
)
from app.evaluator.consts import CHANNELS, OSCILLO_CONFIGURATIONS
from app.evaluator.methods import (
    area,
    combine_ko_pearson_and_area_anomalous_features,
    covariation_check,
    evaluate_area,
    evaluate_pearson,
    opposite_values,
    pearson,
)

logger = logging.getLogger(__name__)


def evaluate_measured_data(measurement_data: MeasurementData):
    evaluation_result = OscilloEvaluationResult(
        measurement_data.bulk_id,
        measurement_data.timestamp,
        dt.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    # # check if measurement is noise
    if not measurement_data.is_valid():
        return evaluation_result

    evaluation_result.rule1 = opposite_values(
        measurement_data.ch3, measurement_data.ch4
    )
    evaluation_result.rule2 = covariation_check(
        measurement_data.ch1,
        threshold=ConfigStore().covariation.get("ch1_threshold", 0.01),
    )
    evaluation_result.rule3 = covariation_check(
        measurement_data.ch2,
        threshold=ConfigStore().covariation.get("ch2_threshold", 0.05),
    )
    for (
        cfg,
        reference,
    ) in (
        OSCILLO_CONFIGURATIONS.items()
    ):  # ! must match class attribute names within OscilloEvaluationResult, e.g. self.config3
        # ? might specify combinator callback evaluation per oscillo configuration
        configuration_evaluation_result = OscilloConfigurationEvaluationResult(
            cfg,
            combinator=(
                lambda pearson, area: combine_ko_pearson_and_area_anomalous_features(
                    evaluation_result.rule1,
                    evaluation_result.rule2,
                    evaluation_result.rule3,
                    pearson,
                    area,
                )
            ),
        )
        configuration_evaluation_result.pearson = pearson(
            measurement_data, reference
        ).evaluate(lambda ev: evaluate_pearson(ev, measurement_data))
        configuration_evaluation_result.area = area(
            measurement_data, reference
        ).evaluate(lambda ev: evaluate_area(ev, measurement_data))
        evaluation_result.config_evaluations[cfg] = configuration_evaluation_result

    return evaluation_result
