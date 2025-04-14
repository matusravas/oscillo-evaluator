from flask import jsonify

from app import app
from app.evaluator import evaluate_measured_data
from app.fetcher import obtain_measured_data, post_anomaly_data


@app.route('/evaluate/<bulk_id>', methods=['GET'])
def evaluate(bulk_id: str):
    print(bulk_id)
    return 
    measured_data = obtain_measured_data(bulk_id) #TODO doplnit logy
    # if not measured_data.is_valid():
    evaluated_data = evaluate_measured_data(measured_data)
    if not evaluated_data.config_evaluations:
        _ = post_anomaly_data(evaluated_data)
        return jsonify({
            "status": "success"
            , "message": f"bulk_id: {bulk_id} data could not be analyzed voltages empty = nosiy data"
        }), 200
    else:
        _ = post_anomaly_data(evaluated_data)
        return jsonify({
            "status": "success"
            , "message": f"bulk_id: {bulk_id} data analyzed and results posted to Elasticsearch"
        }), 200

if __name__ == '__main__':
    app.run("0.0.0.0")
