import asyncio
import aiohttp
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Union


# Enums
class ModelProvider(Enum):
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    HUGGINGFACE = "HUGGINGFACE"
    SAGEMAKER = "SAGEMAKER"
    BEDROCK = "BEDROCK"


class AssessmentStatus(Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Data classes
@dataclass
class AssessmentResult:
    assessment_id: str
    model_id: str
    status: AssessmentStatus
    overall_score: float
    risk_level: RiskLevel
    total_tests: int
    passed_tests: int
    failed_tests: int
    categories: Dict[str, Any]
    recommendations: List[str]
    started_at: datetime
    completed_at: Optional[datetime] = None


@dataclass
class UsageStats:
    models_registered: int
    models_limit: int
    assessments_this_month: int
    assessments_limit: int
    tier: str
    next_reset_date: str


# Exceptions
class ModelRedError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(ModelRedError):
    pass


class QuotaExceededError(ModelRedError):
    pass


class ModelNotFoundError(ModelRedError):
    pass


class ValidationError(ModelRedError):
    pass


class AssessmentError(ModelRedError):
    pass


# Main client
class ModelRed:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MODELRED_API_KEY")
        if not self.api_key:
            raise ValidationError(
                "API key required. Set MODELRED_API_KEY environment variable or pass api_key parameter."
            )

        if not self.api_key.startswith("mr_"):
            raise ValidationError(
                "Invalid API key format. API key must start with 'mr_'"
            )

        self.base_url = os.getenv("MODELRED_API_URL", "http://localhost:3000")
        self.logger = logging.getLogger("modelred")
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        if not self.session:
            raise RuntimeError(
                "Client not initialized. Use 'async with ModelRed() as client:'"
            )

        url = f"{self.base_url}/api/modelred{endpoint}"

        try:
            async with self.session.request(method, url, **kwargs) as response:
                try:
                    response_data = await response.json()
                except:
                    response_data = {"error": await response.text()}

                # Handle errors
                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status == 403:
                    raise QuotaExceededError(
                        response_data.get("message", "Quota exceeded")
                    )
                elif response.status == 404:
                    raise ModelNotFoundError(response_data.get("message", "Not found"))
                elif response.status == 409:
                    raise ValidationError(response_data.get("message", "Conflict"))
                elif response.status >= 400:
                    raise ModelRedError(
                        response_data.get("message", f"API error: {response.status}")
                    )

                return response_data

        except aiohttp.ClientError as e:
            raise ModelRedError(f"Network error: {str(e)}")

    async def validate_api_key(self) -> Dict[str, Any]:
        """Validate API key and get account info"""
        return await self._make_request("GET", "/auth/validate")

    async def get_usage_stats(self) -> UsageStats:
        """Get current usage statistics"""
        data = await self._make_request("GET", "/account/usage")
        return UsageStats(**data)

    async def register_model(
        self,
        model_id: str,
        provider: Union[str, ModelProvider],
        model_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: Optional[str] = None,
        endpoint_name: Optional[str] = None,
        bedrock_model_id: Optional[str] = None,
    ) -> bool:
        """Register a new model for security testing"""

        # Validation
        if not model_id.strip():
            raise ValidationError("Model ID cannot be empty")

        if isinstance(provider, str):
            try:
                provider = ModelProvider(provider.upper())
            except ValueError:
                raise ValidationError(f"Invalid provider: {provider}")

        # Build provider config based on provider type
        provider_config = {}

        if provider == ModelProvider.OPENAI:
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValidationError(
                    "OpenAI API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
                )
            provider_config = {
                "api_key": api_key,
                "model_name": model_name or "gpt-3.5-turbo",
            }

        elif provider == ModelProvider.ANTHROPIC:
            api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValidationError(
                    "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
                )
            provider_config = {
                "api_key": api_key,
                "model_name": model_name or "claude-3-sonnet-20240229",
            }

        elif provider == ModelProvider.HUGGINGFACE:
            if api_key:
                provider_config["api_key"] = api_key
            provider_config["model_name"] = model_name or "gpt2"

        elif provider == ModelProvider.SAGEMAKER:
            if not all([aws_access_key_id, aws_secret_access_key, endpoint_name]):
                raise ValidationError(
                    "SageMaker requires aws_access_key_id, aws_secret_access_key, and endpoint_name"
                )
            provider_config = {
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
                "aws_region": aws_region or "us-east-1",
                "endpoint_name": endpoint_name,
            }

        elif provider == ModelProvider.BEDROCK:
            if not all([aws_access_key_id, aws_secret_access_key, bedrock_model_id]):
                raise ValidationError(
                    "Bedrock requires aws_access_key_id, aws_secret_access_key, and bedrock_model_id"
                )
            provider_config = {
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
                "aws_region": aws_region or "us-east-1",
                "model_id": bedrock_model_id,
            }

        payload = {
            "model_id": model_id,
            "provider": provider.value,
            "model_name": model_name,
            "provider_config": provider_config,
            "metadata": metadata or {},
        }

        response = await self._make_request("POST", "/models", json=payload)
        return response.get("success", True)

    async def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models"""
        response = await self._make_request("GET", "/models")
        return response.get("models", [])

    async def get_model(self, model_id: str) -> Dict[str, Any]:
        """Get details of a specific model"""
        response = await self._make_request("GET", f"/models/{model_id}")
        return response

    async def delete_model(self, model_id: str) -> bool:
        """Delete a registered model"""
        response = await self._make_request("DELETE", f"/models/{model_id}")
        return response.get("success", True)

    async def run_assessment(
        self,
        model_id: str,
        test_types: Optional[List[str]] = None,
        priority: str = "normal",
        wait_for_completion: bool = True,
        timeout_minutes: int = 30,
    ) -> AssessmentResult:
        """Run a security assessment on a model"""

        if not test_types:
            test_types = ["prompt_injection", "jailbreak", "toxicity"]

        valid_test_types = [
            "prompt_injection",
            "jailbreak",
            "toxicity",
            "bias",
            "hallucination",
            "data_leakage",
            "malware_generation",
        ]

        for test_type in test_types:
            if test_type not in valid_test_types:
                raise ValidationError(
                    f"Invalid test type: {test_type}. Valid types: {valid_test_types}"
                )

        if priority not in ["low", "normal", "high", "critical"]:
            raise ValidationError(
                "Priority must be one of: low, normal, high, critical"
            )

        payload = {"model_id": model_id, "test_types": test_types, "priority": priority}

        response = await self._make_request("POST", "/assessments", json=payload)
        assessment_id = response["assessment_id"]

        if not wait_for_completion:
            return AssessmentResult(
                assessment_id=assessment_id,
                model_id=model_id,
                status=AssessmentStatus.QUEUED,
                overall_score=0.0,
                risk_level=RiskLevel.LOW,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                categories={},
                recommendations=[],
                started_at=datetime.now(),
            )

        # Wait for completion
        self.logger.info(
            f"Assessment {assessment_id} started. Waiting for completion..."
        )
        start_time = time.time()

        while time.time() - start_time < timeout_minutes * 60:
            try:
                status_response = await self.get_assessment_status(assessment_id)
                status = AssessmentStatus(status_response["status"])

                progress = status_response.get("progress", 0)
                self.logger.info(f"Assessment progress: {progress}%")

                if status == AssessmentStatus.COMPLETED:
                    self.logger.info("Assessment completed successfully!")
                    return await self.get_assessment_results(assessment_id)
                elif status == AssessmentStatus.FAILED:
                    error_msg = status_response.get("error_message", "Unknown error")
                    raise AssessmentError(f"Assessment failed: {error_msg}")

                await asyncio.sleep(10)  # Check every 10 seconds

            except (ModelNotFoundError, AssessmentError):
                raise
            except Exception as e:
                self.logger.warning(f"Error checking assessment status: {e}")
                await asyncio.sleep(10)

        raise AssessmentError(f"Assessment timeout after {timeout_minutes} minutes")

    async def get_assessment_status(self, assessment_id: str) -> Dict[str, Any]:
        """Get current status of an assessment"""
        return await self._make_request("GET", f"/assessments/{assessment_id}")

    async def get_assessment_results(self, assessment_id: str) -> AssessmentResult:
        """Get detailed results of a completed assessment"""
        data = await self._make_request("GET", f"/assessments/{assessment_id}/results")

        return AssessmentResult(
            assessment_id=data["assessment_id"],
            model_id=data["model_id"],
            status=AssessmentStatus(data["status"]),
            overall_score=data["overall_score"],
            risk_level=RiskLevel(data["risk_level"]),
            total_tests=data["total_tests"],
            passed_tests=data["passed_tests"],
            failed_tests=data["failed_tests"],
            categories=data["categories"],
            recommendations=data["recommendations"],
            started_at=datetime.fromisoformat(
                data["started_at"].replace("Z", "+00:00")
            ),
            completed_at=(
                datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00"))
                if data.get("completed_at")
                else None
            ),
        )

    async def list_assessments(self) -> List[Dict[str, Any]]:
        """List recent assessments"""
        response = await self._make_request("GET", "/assessments")
        return response.get("assessments", [])


# Convenience functions for synchronous usage
def create_client(api_key: Optional[str] = None) -> ModelRed:
    """Create a ModelRed client instance"""
    return ModelRed(api_key=api_key)


async def quick_assessment(
    model_id: str,
    provider: Union[str, ModelProvider],
    api_key: str,
    test_types: Optional[List[str]] = None,
    model_name: Optional[str] = None,
    modelred_api_key: Optional[str] = None,
) -> AssessmentResult:
    """Run a quick security assessment on a model"""

    async with ModelRed(api_key=modelred_api_key) as client:
        # Register model
        success = await client.register_model(
            model_id=model_id, provider=provider, model_name=model_name, api_key=api_key
        )

        if not success:
            raise ModelRedError("Failed to register model")

        # Run assessment
        result = await client.run_assessment(
            model_id=model_id,
            test_types=test_types,
            wait_for_completion=True,
            timeout_minutes=15,
        )

        return result
