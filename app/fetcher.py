import logging
import os
import ssl
from datetime import datetime, timezone

from elasticsearch import Elasticsearch
from elasticsearch.connection import create_ssl_context

from app.dtos import MeasurementData, OscilloEvaluationResult

logger = logging.getLogger(__name__)

ES_OSCILLO_DATA_INDEX = lambda date: f"oscillo-ch*-{date}"
ES_ANOMALIES_INDEX = "oscillo-anomalies"


ssl_context = create_ssl_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


auth_token = "Basic {}".format(os.getenv("ES_TOKEN", ""))
ES_REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "Connection": "keep-alive",
    "Accept": "application/json",
    "Authorization": auth_token,
    "Cache-Control": "no-cache, no-store",
}

es = Elasticsearch(
    hosts=[
        host for host in os.getenv("ES_HOSTS", "").split(",")
    ],
    headers=ES_REQUEST_HEADERS,  # your username and password
    ssl_context=ssl_context,
    timeout=300,
)


def obtain_measured_data(bulk_id: str):
    date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    _ = es.indices.refresh(index=ES_OSCILLO_DATA_INDEX(date))
    query = {
        "size": 0,
        "sort": [{"timestamp_read_measurement": {"order": "asc"}}],
        "query": {
            "bool": {"must": [{"term": {"bulk_id.keyword": {"value": bulk_id}}}]}
        },
        "aggs": {
            "channels": {
                "terms": {"field": "channel.keyword"},
                "aggs": {"data": {"top_hits": {"size": 1}}},
            }
        },
    }
    try:
        index = ES_OSCILLO_DATA_INDEX(date)
        data = es.search(index=index, body=query)
        if (
            data
            and "aggregations" in data
            and "channels" in data["aggregations"]
            and "buckets" in data["aggregations"]["channels"]
            and data["aggregations"]["channels"]["buckets"]
        ):
            buckets = data["aggregations"]["channels"]["buckets"]
            measurement_data = MeasurementData.deserialize(bulk_id, buckets)
            return measurement_data
        else:
            return MeasurementData.deserialize(bulk_id)
    except Exception as e:
        logger.error(f"Error fetching data from Elasticsearch: {e}")
        return MeasurementData.deserialize(bulk_id)


# def post_measured_but_noise_data(measurement_data: MeasurementData):
#     serialized_data = measurement_data.serialize(
#     )
#     result = es.index(
#       index=ES_ANOMALIES_INDEX
#       , document=serialized_data
#     )
#     logger.info(result)
#     return result


def post_anomaly_data(evaluation_result: OscilloEvaluationResult):
    serialized_data = evaluation_result.serialize()
    # logger.info(serialized_data)
    result = es.index(index=ES_ANOMALIES_INDEX, document=serialized_data)
    logger.info(result)
    return result
