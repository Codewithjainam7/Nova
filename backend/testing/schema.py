from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class TestCategory(str, Enum):
    UNIT = "UNIT"
    INTEGRATION = "INTEGRATION"
    E2E = "E2E"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    STRESS = "STRESS"
    REGRESSION = "REGRESSION"

class TestStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class TestResult(BaseModel):
    test_id: str
    name: str
    category: TestCategory
    status: TestStatus = TestStatus.PENDING
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

class TestSuiteResult(BaseModel):
    suite_name: str
    results: List[TestResult] = []
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    total_duration_ms: float = 0.0

class QualityMetrics(BaseModel):
    total_suites_run: int = 0
    overall_pass_rate: float = 0.0
    coverage_percentage: float = 0.0
    memory_leaks_detected: int = 0
    security_vulnerabilities_found: int = 0
