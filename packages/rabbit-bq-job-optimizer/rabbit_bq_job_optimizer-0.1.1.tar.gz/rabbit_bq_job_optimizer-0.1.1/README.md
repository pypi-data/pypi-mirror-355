# Rabbit BigQuery Job Optimizer Python Client

This is the official Python client library for the Rabbit BigQuery Job Optimizer API.

## Installation

```bash
pip install rabbit-bq-job-optimizer
```

## Usage

```python
from rabbit_bq_job_optimizer import RabbitBQOptimizer, OptimizationConfig

# Initialize the client
client = RabbitBQOptimizer(
    api_key="your-api-key",
    base_url="https://api.rabbit.com/v1"  # Optional, defaults to production URL
)

# Optimize a BigQuery job configuration
job_config = {
    "configuration": {
        "query": {
            "query": "SELECT * FROM my_table",
            "useLegacySql": False,
            "priority": "INTERACTIVE"
        }
    }
}

optimization_config = OptimizationConfig(
    type="reservation_assignment",
    config={
        "defaultPricingMode": "on_demand",
        "reservationIds": [
            "projects/my-project/locations/US/reservations/my-reservation-us",
            "projects/my-project/locations/EU/reservations/my-reservation-eu"
        ]
    }
)

# Optimize the job
result = client.optimize_job(
    configuration=job_config,
    enabledOptimizations=[optimization_config]
)

# Access the optimized configuration
optimized_config = result.optimizedJob

# Access optimization results
for optimization in result.optimizationResults:
    print(f"Type: {optimization.type}")
    print(f"Applied: {optimization.performed}")
    print(f"Estimated Savings: {optimization.estimatedSavings}")
```

## Error Handling

The client raises exceptions for API errors:

```python
from rabbit_bq_job_optimizer import RabbitBQOptimizerError

try:
    result = client.optimize_job(job_config)
except RabbitBQOptimizerError as e:
    print(f"Error: {e.message}")
    print(f"Status Code: {e.status_code}")
```

## Development

To install the package in development mode:

```bash
pip install -e .
```

## License

Apache License 2.0 