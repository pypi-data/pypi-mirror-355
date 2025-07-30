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
    AZURE = "AZURE"
    ANTHROPIC = "ANTHROPIC"
    HUGGINGFACE = "HUGGINGFACE"
    SAGEMAKER = "SAGEMAKER"
    BEDROCK = "BEDROCK"
    CUSTOM_REST = "CUSTOM_REST"


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


class AuthType(Enum):
    NONE = "none"
    BEARER = "bearer"
    API_KEY = "api_key"
    CUSTOM_HEADER = "custom_header"


class RequestFormat(Enum):
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC_STYLE = "anthropic_style"
    SIMPLE = "simple"
    CUSTOM = "custom"


# Data classes
@dataclass
class ProviderInfo:
    name: str
    display_name: str
    description: str
    supported_models: List[str]
    required_fields: List[str]
    optional_fields: List[str]
    tier_required: str
    # Note: icon and config_schema are UI-only fields, ignored in SDK


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
    probes_used: Optional[List[str]] = None
    progress: int = 0
    report_url: Optional[str] = None


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


class TierRestrictedError(ModelRedError):
    pass


# Provider configuration helpers
class ProviderConfig:
    """Helper class for creating provider configurations"""

    @staticmethod
    def openai(
        api_key: Optional[str] = None,
        model_name: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create OpenAI provider configuration"""
        config = {
            "api_key": api_key or os.getenv("OPENAI_API_KEY"),
            "model_name": model_name,
        }
        if base_url:
            config["base_url"] = base_url
        if organization:
            config["organization"] = organization
        return config

    @staticmethod
    def azure(
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
    ) -> Dict[str, Any]:
        """Create Azure OpenAI provider configuration"""
        return {
            "api_key": api_key or os.getenv("AZURE_OPENAI_API_KEY"),
            "endpoint": endpoint or os.getenv("AZURE_OPENAI_ENDPOINT"),
            "deployment_name": deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            "api_version": api_version,
        }

    @staticmethod
    def anthropic(
        api_key: Optional[str] = None, model_name: str = "claude-3-sonnet-20240229"
    ) -> Dict[str, Any]:
        """Create Anthropic provider configuration"""
        return {
            "api_key": api_key or os.getenv("ANTHROPIC_API_KEY"),
            "model_name": model_name,
        }

    @staticmethod
    def huggingface(
        model_name: str,
        api_key: Optional[str] = None,
        use_inference_api: bool = True,
        endpoint_url: Optional[str] = None,
        task: str = "text-generation",
    ) -> Dict[str, Any]:
        """Create Hugging Face provider configuration"""
        config = {
            "model_name": model_name,
            "use_inference_api": use_inference_api,
            "task": task,
        }
        if api_key:
            config["api_key"] = api_key
        elif os.getenv("HUGGINGFACE_API_TOKEN"):
            config["api_key"] = os.getenv("HUGGINGFACE_API_TOKEN")
        if endpoint_url:
            config["endpoint_url"] = endpoint_url
        return config

    @staticmethod
    def sagemaker(
        endpoint_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
    ) -> Dict[str, Any]:
        """Create AWS SageMaker provider configuration"""
        return {
            "endpoint_name": endpoint_name,
            "aws_access_key_id": aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": aws_secret_access_key
            or os.getenv("AWS_SECRET_ACCESS_KEY"),
            "region": region,
        }

    @staticmethod
    def bedrock(
        model_id: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
    ) -> Dict[str, Any]:
        """Create AWS Bedrock provider configuration"""
        return {
            "model_id": model_id,
            "aws_access_key_id": aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": aws_secret_access_key
            or os.getenv("AWS_SECRET_ACCESS_KEY"),
            "region": region,
        }

    @staticmethod
    def custom_rest(
        endpoint_url: str,
        auth_type: Union[str, AuthType] = AuthType.NONE,
        auth_value: Optional[str] = None,
        custom_header_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        request_format: Union[str, RequestFormat] = RequestFormat.OPENAI_COMPATIBLE,
        response_path: str = "choices.0.message.content",
        custom_payload_template: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create custom REST API provider configuration"""
        if isinstance(auth_type, AuthType):
            auth_type = auth_type.value
        if isinstance(request_format, RequestFormat):
            request_format = request_format.value

        config = {
            "endpoint_url": endpoint_url,
            "auth_type": auth_type,
            "request_format": request_format,
            "response_path": response_path,
            "headers": headers or {},
        }

        if auth_value:
            config["auth_value"] = auth_value
        if custom_header_name:
            config["custom_header_name"] = custom_header_name
        if custom_payload_template:
            config["custom_payload_template"] = custom_payload_template

        return config


# Main client
class ModelRed:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("MODELRED_API_KEY")
        if not self.api_key:
            raise ValidationError(
                "API key required. Set MODELRED_API_KEY environment variable or pass api_key parameter."
            )

        if not self.api_key.startswith("mr_"):
            raise ValidationError(
                "Invalid API key format. API key must start with 'mr_'"
            )

        self.base_url = "http://localhost:3000"
        self.logger = logging.getLogger("modelred")
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "ModelRed-SDK/2.0",
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

                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status == 403:
                    error_msg = response_data.get("error", "Access denied")
                    if (
                        "tier" in error_msg.lower()
                        or "subscription" in error_msg.lower()
                        or "requires" in error_msg.lower()
                    ):
                        raise TierRestrictedError(error_msg)
                    else:
                        raise QuotaExceededError(error_msg)
                elif response.status == 404:
                    raise ModelNotFoundError(response_data.get("error", "Not found"))
                elif response.status == 409:
                    raise ValidationError(response_data.get("error", "Conflict"))
                elif response.status >= 400:
                    raise ModelRedError(
                        response_data.get("error", f"API error: {response.status}")
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

    async def get_providers(self) -> List[ProviderInfo]:
        """Get list of supported providers"""
        data = await self._make_request("GET", "/providers")
        return [ProviderInfo(**provider_data) for provider_data in data["providers"]]

    async def register_model(
        self,
        model_id: str,
        provider: Union[str, ModelProvider],
        provider_config: Dict[str, Any],
        model_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Register a new model for security testing"""

        if not model_id.strip():
            raise ValidationError("Model ID cannot be empty")

        if isinstance(provider, str):
            try:
                provider = ModelProvider(provider.upper())
            except ValueError:
                raise ValidationError(f"Invalid provider: {provider}")

        # Validate required fields based on provider
        if not provider_config:
            raise ValidationError("Provider configuration is required")

        payload = {
            "model_id": model_id,
            "provider": provider.value,
            "model_name": model_name,
            "provider_config": provider_config,
            "metadata": metadata or {},
        }

        response = await self._make_request("POST", "/models", json=payload)
        return response.get("success", True)

    async def register_openai_model(
        self,
        model_id: str,
        api_key: Optional[str] = None,
        model_name: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Convenience method to register an OpenAI model"""
        config = ProviderConfig.openai(api_key, model_name, base_url, organization)
        return await self.register_model(
            model_id, ModelProvider.OPENAI, config, model_name, metadata
        )

    async def register_azure_model(
        self,
        model_id: str,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Convenience method to register an Azure OpenAI model"""
        config = ProviderConfig.azure(api_key, endpoint, deployment_name, api_version)
        return await self.register_model(
            model_id, ModelProvider.AZURE, config, deployment_name, metadata
        )

    async def register_anthropic_model(
        self,
        model_id: str,
        api_key: Optional[str] = None,
        model_name: str = "claude-3-sonnet-20240229",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Convenience method to register an Anthropic model"""
        config = ProviderConfig.anthropic(api_key, model_name)
        return await self.register_model(
            model_id, ModelProvider.ANTHROPIC, config, model_name, metadata
        )

    async def register_huggingface_model(
        self,
        model_id: str,
        model_name: str,
        api_key: Optional[str] = None,
        use_inference_api: bool = True,
        endpoint_url: Optional[str] = None,
        task: str = "text-generation",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Convenience method to register a Hugging Face model"""
        config = ProviderConfig.huggingface(
            model_name, api_key, use_inference_api, endpoint_url, task
        )
        return await self.register_model(
            model_id, ModelProvider.HUGGINGFACE, config, model_name, metadata
        )

    async def register_sagemaker_model(
        self,
        model_id: str,
        endpoint_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Convenience method to register a SageMaker model"""
        config = ProviderConfig.sagemaker(
            endpoint_name, aws_access_key_id, aws_secret_access_key, region
        )
        return await self.register_model(
            model_id, ModelProvider.SAGEMAKER, config, endpoint_name, metadata
        )

    async def register_bedrock_model(
        self,
        model_id: str,
        bedrock_model_id: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Convenience method to register a Bedrock model"""
        config = ProviderConfig.bedrock(
            bedrock_model_id, aws_access_key_id, aws_secret_access_key, region
        )
        return await self.register_model(
            model_id, ModelProvider.BEDROCK, config, bedrock_model_id, metadata
        )

    async def register_custom_rest_model(
        self,
        model_id: str,
        endpoint_url: str,
        auth_type: Union[str, AuthType] = AuthType.NONE,
        auth_value: Optional[str] = None,
        custom_header_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        request_format: Union[str, RequestFormat] = RequestFormat.OPENAI_COMPATIBLE,
        response_path: str = "choices.0.message.content",
        custom_payload_template: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Convenience method to register a custom REST API model"""
        config = ProviderConfig.custom_rest(
            endpoint_url,
            auth_type,
            auth_value,
            custom_header_name,
            headers,
            request_format,
            response_path,
            custom_payload_template,
        )
        return await self.register_model(
            model_id,
            ModelProvider.CUSTOM_REST,
            config,
            model_name or "custom-model",
            metadata,
        )

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

    async def get_test_suites(self) -> List[Dict[str, Any]]:
        """Get available test suites for the current tier"""
        response = await self._make_request("GET", "/test-suites")
        return response.get("test_suites", [])

    async def run_assessment(
        self,
        model_id: str,
        test_suites: List[str],
        priority: str = "normal",
        wait_for_completion: bool = False,
        timeout_minutes: int = 60,
        progress_callback: Optional[callable] = None,
    ) -> AssessmentResult:
        """Run a security assessment on a model using specified test suites"""

        if not test_suites:
            raise ValidationError("At least one test suite must be specified")

        if priority not in ["low", "normal", "high", "critical"]:
            raise ValidationError(
                "Priority must be one of: low, normal, high, critical"
            )

        payload = {
            "model_id": model_id,
            "test_types": test_suites,
            "priority": priority,
        }

        # Start the assessment
        response = await self._make_request("POST", "/assessments", json=payload)
        assessment_id = response["assessment_id"]

        self.logger.info(f"✅ Assessment {assessment_id} queued successfully")
        self.logger.info(f"🔗 View results at: {response.get('report_url', 'N/A')}")

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
                progress=0,
                report_url=response.get("report_url"),
            )

        # Wait for completion with progress updates
        self.logger.info(f"⏳ Waiting for assessment completion...")
        start_time = time.time()
        last_progress = 0

        while time.time() - start_time < timeout_minutes * 60:
            try:
                status_response = await self.get_assessment_status(assessment_id)
                status = AssessmentStatus(status_response["status"])
                progress = status_response.get("progress", 0)

                # Call progress callback if provided and progress changed
                if progress_callback and progress != last_progress:
                    progress_callback(progress, status.value)
                    last_progress = progress

                self.logger.info(
                    f"📊 Assessment progress: {progress}% - {status.value}"
                )

                if status == AssessmentStatus.COMPLETED:
                    self.logger.info("🎉 Assessment completed successfully!")
                    return await self.get_assessment_results(assessment_id)
                elif status == AssessmentStatus.FAILED:
                    error_msg = status_response.get("error_message", "Unknown error")
                    raise AssessmentError(f"Assessment failed: {error_msg}")

                await asyncio.sleep(10)

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
            probes_used=data.get("probes_used", []),
            progress=data.get("progress", 0),
            report_url=data.get("report_url"),
        )

    async def list_assessments(self) -> List[Dict[str, Any]]:
        """List recent assessments"""
        response = await self._make_request("GET", "/assessments")
        return response.get("assessments", [])

    async def cancel_assessment(self, assessment_id: str) -> bool:
        """Cancel a running assessment"""
        response = await self._make_request("DELETE", f"/assessments/{assessment_id}")
        return response.get("success", True)

    async def get_assessment_stats(self) -> Dict[str, Any]:
        """Get assessment statistics"""
        return await self._make_request("GET", "/assessments/stats")
