from typing import Dict, List, Any
import os
import requests

from .models import OptimizationConfig, OptimizationResponse
from .exceptions import RabbitBQOptimizerError

class RabbitBQOptimizer:
    API_KEY_ENV_VAR = "RABBIT_API_KEY"
    BASE_URL_ENV_VAR = "RABBIT_API_BASE_URL"

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv(self.API_KEY_ENV_VAR)
        if not self.api_key:
            raise ValueError(f"API key must be provided either as an argument or via the {self.API_KEY_ENV_VAR} environment variable")

        self.base_url = (base_url or os.getenv(self.BASE_URL_ENV_VAR))
        if not self.base_url:
            raise ValueError(f"Base URL must be provided either as an argument or via the {self.BASE_URL_ENV_VAR} environment variable")
        
        self.base_url = self.base_url.rstrip('/')
        
        self.session = requests.Session()
        self.session.headers.update({
            'rabbit-api-key': self.api_key,
            'Content-Type': 'application/json'
        })

    def optimize_job(
        self,
        configuration: Dict[str, Any],
        enabledOptimizations: List[OptimizationConfig]
    ) -> OptimizationResponse:
        """
        Optimize a BigQuery job configuration.

        Args:
            configuration: The BigQuery job configuration to optimize
            enabledOptimizations: List of optimizations to enable

        Returns:
            OptimizationResponse containing the optimized configuration and results

        Raises:
            RabbitBQOptimizerError: If the API request fails
        """
        url = f"{self.base_url}/api/v1/bigquery/optimize-job"
        
        payload = {
            "job": configuration,
            "enabledOptimizations": [opt.dict() for opt in enabledOptimizations]
        }

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return OptimizationResponse(**response.json())
        except requests.exceptions.RequestException as e:
            raise RabbitBQOptimizerError(f"Failed to optimize job: {str(e)}") 