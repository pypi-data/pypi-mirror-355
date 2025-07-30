from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class OptimizationConfig(BaseModel):
    type: str = Field(..., description="Type of optimization to apply")
    defaultPricingMode: Optional[str] = Field(None, description="Default pricing mode for the job")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration specific to the optimization type")

class OptimizationResult(BaseModel):
    type: str = Field(..., description="Type of optimization that was attempted")
    performed: bool = Field(..., description="Whether the optimization was performed")
    estimatedSavings: float = Field(..., description="Estimated cost savings from the optimization")
    context: Dict[str, Any] = Field(..., description="Additional context about the optimization decision")

class OptimizationResponse(BaseModel):
    optimizedJob: Dict[str, Any] = Field(..., description="The optimized BigQuery job configuration")
    optimizationResults: List[OptimizationResult] = Field(..., description="Results of each optimization attempt")
    estimatedSavings: float = Field(..., description="Total estimated cost savings across all optimizations")
    optimizationPerformed: bool = Field(..., description="Whether any optimization was performed") 