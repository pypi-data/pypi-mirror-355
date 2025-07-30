# locust-victoria-metrics

**A Locust plugin to extract test results and push metrics to [VictoriaMetrics](https://victoriametrics.com/).**

![PyPI](https://img.shields.io/pypi/v/locust-victoria-metrics)
![License](https://img.shields.io/github/license/dsetiawan230294/locust-victoria-metrics)

---

## 📦 Overview

`locust-victoria-metrics` is a plugin for [Locust](https://locust.io/) that captures test metrics such as request statistics, failures, and custom events, then pushes them to [VictoriaMetrics](https://victoriametrics.com/), a fast, cost-effective, and scalable time-series database.

This helps you:

- Collect detailed performance test data over time
- Build dashboards using Grafana + VictoriaMetrics
- Analyze trends and regressions across multiple test runs

---

## 🚀 Features

- Push Locust metrics in real-time or at test end
- Automatic metric formatting for VictoriaMetrics (Prometheus format)
- Lightweight and easy to plug into existing Locust tests
- Supports custom metric tags (test name, environment, etc.)

---

## 🛠️ Installation

### From PyPI
```bash
pip install locust-victoria-metrics
```

### From Source
```bash
git clone https://github.com/dsetiawan230294/locust-victoria-metrics.git
cd locust-victoria-metrics
pip install .
```

---

## 🧪 Usage

### 1. Enable the plugin in your Locust script:

```python
from locust import HttpUser, task, between, events, TaskSet
from locust_victoria_metrics.pusher import VictoriaMetricsPusher

# Initialize the plugin (can be done once globally or inside a test runner)
# Place below snippet code at the end of locust script file.
def on_locust_init(environment, **_kwargs):
    metrics_pusher = VictoriaMetricsPusher(
        locust_host= "http://localhost:8089"
        victoria_host="http://your-victoria-metrics-host:8428/api/v1/import/prometheus",
        interval=5,  
        product_name="Transaction" # for filtering in grafana
    )

    def run_exporter():
        while True:
            try:
                exporter.collect()
            except Exception as e:
                logger.error(f"Error in metrics exporter: {e}")
            time.sleep(1)

    from threading import Thread

    Thread(target=run_exporter, daemon=True).start()

events.init.add_listener(on_locust_init)

```
- MANDATORY to run the locust script with argument ```--autostart --autoquit 1```
---

## ⚙️ Configuration

| Parameter       | Type     | Description                                                                 |
|----------------|----------|-----------------------------------------------------------------------------|
| `locust_host`      | `str`    | Locust Exposed Endpoint                       |
| `victoria_host`      | `str`    | VictoriaMetrics HTTP API endpoint (Prometheus format)                       |
| `interval`      | `int`    | Push interval in seconds (default: `10`)                                   |
| `product_name`          | `str`   | Additional tags/labels to include with each metric                         |

---

## 📊 Example Metrics Pushed

```
locust_request_count{method="GET", name="/api/test", status="200", job="loadtest", instance="test-runner-1"} 123
locust_request_failure_count{method="GET", name="/api/test", job="loadtest"} 4
locust_avg_response_time{name="/api/test"} 245.7
```

> These metrics can be visualized in Grafana using VictoriaMetrics as a data source.

---

## 📈 Grafana Dashboard

You can build custom dashboards using:
- `locust_request_count`
- `locust_request_failure_count`
- `locust_avg_response_time`
- `locust_users`

---

## 🧩 Compatibility

- ✅ Locust 2.29.1+
- ✅ Python 3.10+
- ✅ Tested with VictoriaMetrics single-node and cluster setups

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork this repository
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a pull request

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

Didit Setiawan  
[GitHub](https://github.com/dsetiawan230294) · [Email](mailto:didit@pintu.co.id)
