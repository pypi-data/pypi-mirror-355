import requests
import json
import logging
import time

logger = logging.getLogger(__name__)


class VictoriaMetrics:
    def __init__(self, locust_host, victoria_host, product_name, interval=10):
        self._host = locust_host
        self._victoria_host = victoria_host
        self._interval = interval
        self.product_name = product_name
        self.consecutive_failures = 0

    def collect(self):
        logger.info(f"Collecting metrics at {time.time()}")
        url = self._host + "/stats/requests"

        try:
            response = requests.get(url).content.decode("utf-8")
            response = json.loads(response)
            logger.info(f"Got metrics from Locust: {url}")

            self.consecutive_failures = 0
            metrics = self._collect_metrics(response)
            self._push_metrics_to_victoria(metrics)

        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to Locust: {url}")
            self.consecutive_failures += 1

            if self.consecutive_failures >= (10 // self._interval):
                logger.error(
                    "Failed to connect to Locust for 10 seconds. Exiting script."
                )
                exit(1)

        except json.decoder.JSONDecodeError:
            logger.warning(f"Wrong response from server: {url}")
            return

    def _collect_metrics(self, response):
        metrics = []

        def append_metric(name, value, labels=None):
            metric = f"{self.product_name}_{name}{{"
            if labels:
                label_parts = [f'{k}="{v}"' for k, v in labels.items()]
                metric += ",".join(label_parts)
            metric += f"}} {value}\n"
            metrics.append(metric)

        append_metric("locust_fail_ratio", response["fail_ratio"])
        append_metric(
            "locust_total_avg_response_time", response["total_avg_response_time"]
        )
        append_metric(
            "locust_state",
            1 if response["state"] in ["running", "spawning", "cleanup"] else 0,
        )
        append_metric("locust_total_fail_per_sec", response["total_fail_per_sec"])
        append_metric("locust_total_rps", response["total_rps"])
        append_metric("locust_user_count", response["user_count"])

        for error in response["errors"]:
            append_metric(
                "locust_errors",
                error["occurrences"],
                labels={
                    "name": error["name"],
                    "method": error["method"],
                    "error": error["error"],
                },
            )

        if "workers" in response:
            for worker in response["workers"]:
                append_metric(
                    "locust_worker_info",
                    1,
                    labels={
                        "cpu_usage": str(worker["cpu_usage"]),
                        "memory_usage": str(worker["memory_usage"]),
                        "user_count": str(worker["user_count"]),
                        "state": worker["state"],
                        "worker_id": worker["id"],
                    },
                )
            append_metric("locust_workers_count", len(response["workers"]))

        stats = [
            "avg_content_length",
            "avg_response_time",
            "current_fail_per_sec",
            "current_rps",
            "max_response_time",
            "median_response_time",
            "min_response_time",
            "num_failures",
            "num_requests",
            "response_time_percentile_0.95",
            "response_time_percentile_0.99",
        ]

        for req_metric in stats:
            for stat in response["stats"]:
                if stat["name"] != "Aggregated":
                    labels = {"name": stat["name"], "method": stat["method"]}
                    if req_metric in ["num_requests", "num_failures"]:
                        append_metric(
                            f"locust_requests_{req_metric}", stat[req_metric], labels
                        )
                    else:
                        append_metric(
                            f"locust_requests_{req_metric.replace('0.', '')}",
                            stat[req_metric],
                            labels,
                        )

        return metrics

    def _push_metrics_to_victoria(self, metrics):
        data = "".join(metrics)
        logger.info(f"Pushing metrics:\n{data}")
        url = f"{self._victoria_host}/insert/0/prometheus/api/v1/import/prometheus"
        headers = {"Content-Type": "text/plain"}

        try:
            response = requests.post(url, data=data, headers=headers)
            if response.status_code in [200, 204]:
                logger.info("Metrics successfully pushed.")
            else:
                logger.error(
                    f"Failed to push metrics. Status: {response.status_code}, Response: {response.text}"
                )
        except Exception as e:
            logger.error(f"Exception while pushing metrics: {e}")

    def start(self):
        while True:
            self.collect()
            time.sleep(self._interval)
