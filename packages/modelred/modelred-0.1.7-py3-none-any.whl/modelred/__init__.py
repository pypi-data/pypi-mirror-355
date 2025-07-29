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


class SubscriptionTier(Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Data classes
@dataclass
class TestSuite:
    name: str
    description: str
    tier_required: SubscriptionTier
    probe_count: int
    estimated_time: str
    categories: List[str]


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
    raw_results: Optional[List[Dict[str, Any]]] = None


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

        self.base_url = os.getenv("MODELRED_API_URL", "https://api.modelred.ai")
        self.logger = logging.getLogger("modelred")
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(
                total=300
            ),  # Increased timeout for long assessments
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "ModelRed-SDK/1.0",
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
                    error_msg = response_data.get("message", "Access denied")
                    if (
                        "tier" in error_msg.lower()
                        or "subscription" in error_msg.lower()
                    ):
                        raise TierRestrictedError(error_msg)
                    else:
                        raise QuotaExceededError(error_msg)
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

    async def get_available_test_suites(self) -> List[TestSuite]:
        """Get all available test suites with tier information"""
        return [
            TestSuite(
                name="basic_security",
                description="Basic security testing for common vulnerabilities",
                tier_required=SubscriptionTier.FREE,
                probe_count=4,
                estimated_time="2-3 minutes",
                categories=["prompt_injection", "jailbreak"],
            ),
            TestSuite(
                name="prompt_injection",
                description="Comprehensive prompt injection testing",
                tier_required=SubscriptionTier.STARTER,
                probe_count=6,
                estimated_time="4-6 minutes",
                categories=["prompt_injection", "encoding"],
            ),
            TestSuite(
                name="basic_jailbreak",
                description="Standard jailbreak detection tests",
                tier_required=SubscriptionTier.STARTER,
                probe_count=4,
                estimated_time="5-7 minutes",
                categories=["jailbreak"],
            ),
            TestSuite(
                name="content_safety",
                description="Content safety and toxicity detection",
                tier_required=SubscriptionTier.STARTER,
                probe_count=4,
                estimated_time="4-6 minutes",
                categories=["toxicity", "bias"],
            ),
            TestSuite(
                name="advanced_jailbreak",
                description="Advanced jailbreak and bypass techniques",
                tier_required=SubscriptionTier.PRO,
                probe_count=6,
                estimated_time="8-12 minutes",
                categories=["jailbreak", "advanced_attacks"],
            ),
            TestSuite(
                name="encoding_attacks",
                description="Encoding-based attack detection",
                tier_required=SubscriptionTier.PRO,
                probe_count=7,
                estimated_time="6-9 minutes",
                categories=["prompt_injection", "encoding"],
            ),
            TestSuite(
                name="toxicity_comprehensive",
                description="Comprehensive toxicity and bias testing",
                tier_required=SubscriptionTier.PRO,
                probe_count=6,
                estimated_time="7-10 minutes",
                categories=["toxicity", "bias"],
            ),
            TestSuite(
                name="bias_fairness",
                description="Bias and fairness evaluation",
                tier_required=SubscriptionTier.PRO,
                probe_count=4,
                estimated_time="5-8 minutes",
                categories=["bias"],
            ),
            TestSuite(
                name="data_leakage",
                description="Data leakage and privacy testing",
                tier_required=SubscriptionTier.PRO,
                probe_count=4,
                estimated_time="6-10 minutes",
                categories=["data_leakage"],
            ),
            TestSuite(
                name="hallucination",
                description="Hallucination and factual accuracy testing",
                tier_required=SubscriptionTier.PRO,
                probe_count=4,
                estimated_time="5-8 minutes",
                categories=["hallucination"],
            ),
            TestSuite(
                name="advanced_prompt_injection",
                description="Advanced prompt injection techniques",
                tier_required=SubscriptionTier.ENTERPRISE,
                probe_count=3,
                estimated_time="8-12 minutes",
                categories=["prompt_injection"],
            ),
            TestSuite(
                name="malware_generation",
                description="Malware generation detection",
                tier_required=SubscriptionTier.ENTERPRISE,
                probe_count=4,
                estimated_time="10-15 minutes",
                categories=["malware_generation"],
            ),
            TestSuite(
                name="exploitation",
                description="Code injection and exploitation testing",
                tier_required=SubscriptionTier.ENTERPRISE,
                probe_count=2,
                estimated_time="6-10 minutes",
                categories=["malware_generation", "advanced_attacks"],
            ),
            TestSuite(
                name="latent_injection",
                description="Latent injection and steganographic attacks",
                tier_required=SubscriptionTier.ENTERPRISE,
                probe_count=4,
                estimated_time="12-18 minutes",
                categories=["advanced_attacks"],
            ),
            TestSuite(
                name="advanced_attacks",
                description="Cutting-edge attack techniques",
                tier_required=SubscriptionTier.ENTERPRISE,
                probe_count=2,
                estimated_time="15-25 minutes",
                categories=["advanced_attacks"],
            ),
            TestSuite(
                name="xss_security",
                description="Cross-site scripting and web security",
                tier_required=SubscriptionTier.ENTERPRISE,
                probe_count=3,
                estimated_time="8-12 minutes",
                categories=["advanced_attacks", "xss"],
            ),
            TestSuite(
                name="comprehensive_toxicity",
                description="Enterprise-grade toxicity detection",
                tier_required=SubscriptionTier.ENTERPRISE,
                probe_count=4,
                estimated_time="12-18 minutes",
                categories=["toxicity", "bias"],
            ),
        ]

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
        test_suites: Optional[List[str]] = None,
        priority: str = "normal",
        wait_for_completion: bool = True,
        timeout_minutes: int = 60,
        progress_callback: Optional[callable] = None,
    ) -> AssessmentResult:
        """Run a security assessment on a model using test suites"""

        if not test_suites:
            test_suites = ["basic_security"]

        # Get available test suites to validate
        available_suites = await self.get_available_test_suites()
        available_suite_names = [suite.name for suite in available_suites]

        for suite in test_suites:
            if suite not in available_suite_names:
                raise ValidationError(
                    f"Invalid test suite: {suite}. Available suites: {available_suite_names}"
                )

        if priority not in ["low", "normal", "high", "critical"]:
            raise ValidationError(
                "Priority must be one of: low, normal, high, critical"
            )

        payload = {
            "model_id": model_id,
            "test_types": test_suites,  # Backend still expects test_types
            "priority": priority,
        }

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

        # Wait for completion with progress updates
        self.logger.info(
            f"Assessment {assessment_id} started. Waiting for completion..."
        )
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

                self.logger.info(f"Assessment progress: {progress}%")

                if status == AssessmentStatus.COMPLETED:
                    self.logger.info("Assessment completed successfully!")
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
            raw_results=data.get("raw_results", []),
        )

    async def list_assessments(self) -> List[Dict[str, Any]]:
        """List recent assessments"""
        response = await self._make_request("GET", "/assessments")
        return response.get("assessments", [])

    async def run_comprehensive_assessment(
        self,
        model_id: str,
        tier: Optional[SubscriptionTier] = None,
        priority: str = "normal",
        wait_for_completion: bool = True,
        timeout_minutes: int = 120,
        progress_callback: Optional[callable] = None,
    ) -> AssessmentResult:
        """Run a comprehensive assessment based on subscription tier"""

        if not tier:
            # Auto-detect tier based on usage stats
            usage = await self.get_usage_stats()
            tier_map = {
                "Free Tier": SubscriptionTier.FREE,
                "Starter Plan": SubscriptionTier.STARTER,
                "Pro Plan": SubscriptionTier.PRO,
                "Enterprise Plan": SubscriptionTier.ENTERPRISE,
            }
            tier = tier_map.get(usage.tier, SubscriptionTier.FREE)

        # Get all available test suites for the tier
        available_suites = await self.get_available_test_suites()
        tier_suites = [
            suite.name
            for suite in available_suites
            if suite.tier_required.value == tier.value
        ]

        if not tier_suites:
            raise ValidationError(f"No test suites available for tier: {tier.value}")

        self.logger.info(
            f"Running comprehensive assessment with {len(tier_suites)} test suites for {tier.value} tier"
        )

        return await self.run_assessment(
            model_id=model_id,
            test_suites=tier_suites,
            priority=priority,
            wait_for_completion=wait_for_completion,
            timeout_minutes=timeout_minutes,
            progress_callback=progress_callback,
        )


# Convenience functions
def create_client(api_key: Optional[str] = None) -> ModelRed:
    """Create a ModelRed client instance"""
    return ModelRed(api_key=api_key)


async def quick_assessment(
    model_id: str,
    provider: Union[str, ModelProvider],
    api_key: str,
    test_suites: Optional[List[str]] = None,
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
            test_suites=test_suites or ["basic_security"],
            wait_for_completion=True,
            timeout_minutes=30,
        )

        return result


async def comprehensive_security_audit(
    model_id: str,
    provider: Union[str, ModelProvider],
    api_key: str,
    model_name: Optional[str] = None,
    modelred_api_key: Optional[str] = None,
    progress_callback: Optional[callable] = None,
) -> AssessmentResult:
    """Run a comprehensive security audit using all available test suites"""

    async with ModelRed(api_key=modelred_api_key) as client:
        # Register model
        await client.register_model(
            model_id=model_id, provider=provider, model_name=model_name, api_key=api_key
        )

        # Run comprehensive assessment
        result = await client.run_comprehensive_assessment(
            model_id=model_id,
            wait_for_completion=True,
            timeout_minutes=120,
            progress_callback=progress_callback,
        )

        return result


# Synchronous wrapper for backwards compatibility
class SyncModelRed:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._loop = None

    def _get_loop(self):
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def _run_async(self, coro):
        loop = self._get_loop()
        if loop.is_running():
            # If loop is already running, we need to use a different approach
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)

    def register_model(self, **kwargs) -> bool:
        """Synchronous version of register_model"""

        async def _register():
            async with ModelRed(api_key=self.api_key) as client:
                return await client.register_model(**kwargs)

        return self._run_async(_register())

    def run_assessment(self, **kwargs) -> AssessmentResult:
        """Synchronous version of run_assessment"""

        async def _assess():
            async with ModelRed(api_key=self.api_key) as client:
                return await client.run_assessment(**kwargs)

        return self._run_async(_assess())

    def get_usage_stats(self) -> UsageStats:
        """Synchronous version of get_usage_stats"""

        async def _stats():
            async with ModelRed(api_key=self.api_key) as client:
                return await client.get_usage_stats()

        return self._run_async(_stats())

    def list_models(self) -> List[Dict[str, Any]]:
        """Synchronous version of list_models"""

        async def _list():
            async with ModelRed(api_key=self.api_key) as client:
                return await client.list_models()

        return self._run_async(_list())
