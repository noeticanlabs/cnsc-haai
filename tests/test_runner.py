"""
Automated Test Execution and Reporting Framework

Provides comprehensive test execution, reporting, and automation
for the HAAI testing framework.
"""

import pytest
import asyncio
import time
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_framework import TestFramework, TestConfiguration
from tests.test_unit_components import (
    TestCoherenceEngine, TestHierarchicalAbstraction, TestNSCStack,
    TestAgentComponents, TestGovernanceSystem, TestPropertyBasedValidation,
    TestPerformanceRegression
)
from tests.test_coherence_validation import TestCoherenceValidation
from tests.test_hierarchical_reasoning_benchmarks import TestHierarchicalReasoningBenchmarks
from tests.test_safety_governance import TestSafetyGovernance
from tests.test_performance_benchmarking import TestPerformanceBenchmarking
from tests.test_integration_suite import TestIntegrationSuite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestSuiteResult:
    """Result of a test suite execution."""
    suite_name: str
    start_time: datetime
    end_time: Optional[datetime]
    tests_run: int
    tests_passed: int
    tests_failed: int
    tests_skipped: int
    success_rate: float
    execution_time: float
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class TestReporter:
    """Generates comprehensive test reports."""
    
    def __init__(self, output_dir: str = "test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.reports = []
    
    def add_suite_result(self, result: TestSuiteResult):
        """Add a test suite result."""
        self.reports.append(result)
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of all test results."""
        total_tests = sum(r.tests_run for r in self.reports)
        total_passed = sum(r.tests_passed for r in self.reports)
        total_failed = sum(r.tests_failed for r in self.reports)
        total_skipped = sum(r.tests_skipped for r in self.reports)
        
        execution_times = [r.execution_time for r in self.reports if r.execution_time > 0]
        
        summary = {
            "report_timestamp": datetime.now().isoformat(),
            "total_suites": len(self.reports),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "overall_success_rate": total_passed / total_tests if total_tests > 0 else 0,
            "total_execution_time": sum(execution_times),
            "average_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
            "suite_results": [
                {
                    "suite_name": r.suite_name,
                    "tests_run": r.tests_run,
                    "tests_passed": r.tests_passed,
                    "tests_failed": r.tests_failed,
                    "success_rate": r.success_rate,
                    "execution_time": r.execution_time,
                    "errors": r.errors[:5]  # Limit errors in summary
                }
                for r in self.reports
            ]
        }
        
        return summary
    
    def generate_html_report(self) -> str:
        """Generate an HTML report."""
        summary = self.generate_summary_report()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>HAAI Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; }}
        .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e0e0e0; border-radius: 3px; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .suite {{ margin: 20px 0; padding: 10px; border-left: 4px solid #333; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <h1>🤖 HAAI Testing Framework Report</h1>
    
    <div class="summary">
        <h2>📊 Summary</h2>
        <p><strong>Report Generated:</strong> {summary['report_timestamp']}</p>
        <p><strong>Total Test Suites:</strong> {summary['total_suites']}</p>
        <p><strong>Total Tests:</strong> {summary['total_tests']}</p>
        <p class="pass"><strong>Tests Passed:</strong> {summary['total_passed']}</p>
        <p class="fail"><strong>Tests Failed:</strong> {summary['total_failed']}</p>
        <p><strong>Tests Skipped:</strong> {summary['total_skipped']}</p>
        <p><strong>Overall Success Rate:</strong> {summary['overall_success_rate']:.2%}</p>
        <p><strong>Total Execution Time:</strong> {summary['total_execution_time']:.2f}s</p>
    </div>
    
    <h2>📋 Test Suite Results</h2>
    <table>
        <tr>
            <th>Suite Name</th>
            <th>Tests Run</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Success Rate</th>
            <th>Execution Time</th>
        </tr>
"""
        
        for suite in summary["suite_results"]:
            status_class = "pass" if suite["success_rate"] >= 0.8 else "fail"
            html += f"""
        <tr>
            <td>{suite['suite_name']}</td>
            <td>{suite['tests_run']}</td>
            <td class="pass">{suite['tests_passed']}</td>
            <td class="fail">{suite['tests_failed']}</td>
            <td class="{status_class}">{suite['success_rate']:.2%}</td>
            <td>{suite['execution_time']:.2f}s</td>
        </tr>
"""
        
        html += """
    </table>
    
    <h2>⚠️ Errors and Warnings</h2>
"""
        
        for suite in summary["suite_results"]:
            if suite["errors"]:
                html += f"<h3>{suite['suite_name']}</h3><ul>"
                for error in suite["errors"]:
                    html += f"<li class='fail'>{error}</li>"
                html += "</ul>"
        
        html += """
</body>
</html>
"""
        
        return html
    
    def save_reports(self):
        """Save all reports to files."""
        # Save JSON summary
        summary = self.generate_summary_report()
        json_path = self.output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save HTML report
        html_path = self.output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        html = self.generate_html_report()
        with open(html_path, 'w') as f:
            f.write(html)
        
        logger.info(f"Reports saved to {self.output_dir}")
        
        return {
            "json_report": str(json_path),
            "html_report": str(html_path)
        }


class AutomatedTestRunner:
    """Automated test execution framework."""
    
    def __init__(self, config: TestConfiguration = None):
        self.config = config or TestConfiguration()
        self.reporter = TestReporter()
        self.test_framework = TestFramework(self.config)
    
    async def run_test_suite(self, suite_name: str, test_module) -> TestSuiteResult:
        """Run a test suite."""
        start_time = datetime.now()
        errors = []
        warnings = []
        
        logger.info(f"🧪 Running test suite: {suite_name}")
        
        try:
            # Run pytest programmatically
            exit_code = pytest.main([
                f"--tb=short",
                "-v",
                "--no-header",
                "-q",
                str(test_module.__file__)
            ])
            
            tests_run = 1  # Placeholder - actual count would come from pytest
            tests_passed = 0 if exit_code != 0 else 1
            tests_failed = 0 if exit_code == 0 else 1
            tests_skipped = 0
            
        except Exception as e:
            errors.append(str(e))
            tests_run = 0
            tests_passed = 0
            tests_failed = 0
            tests_skipped = 0
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        result = TestSuiteResult(
            suite_name=suite_name,
            start_time=start_time,
            end_time=end_time,
            tests_run=tests_run,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            tests_skipped=tests_skipped,
            success_rate=tests_passed / tests_run if tests_run > 0 else 0,
            execution_time=execution_time,
            errors=errors,
            warnings=warnings
        )
        
        self.reporter.add_suite_result(result)
        
        logger.info(f"✅ Suite '{suite_name}' completed in {execution_time:.2f}s - " +
                   f"Passed: {tests_passed}, Failed: {tests_failed}")
        
        return result
    
    async def run_all_suites(self) -> Dict[str, Any]:
        """Run all test suites."""
        logger.info("🚀 Starting HAAI Test Framework")
        logger.info("=" * 50)
        
        suite_results = []
        
        # Define test suites
        test_suites = [
            ("Unit Components", "tests.test_unit_components"),
            ("Coherence Validation", "tests.test_coherence_validation"),
            ("Hierarchical Reasoning Benchmarks", "tests.test_hierarchical_reasoning_benchmarks"),
            ("Safety and Governance", "tests.test_safety_governance"),
            ("Performance Benchmarking", "tests.test_performance_benchmarking"),
            ("Integration Suite", "tests.test_integration_suite"),
            ("Existing Integration Tests", "tests.test_haai_integration"),
            ("Governance Integration Tests", "tests.test_governance_integration"),
        ]
        
        for suite_name, module_name in test_suites:
            try:
                # Import module
                import importlib
                module = importlib.import_module(module_name)
                
                # Run suite
                result = await self.run_test_suite(suite_name, module)
                suite_results.append(result)
                
            except Exception as e:
                logger.error(f"❌ Failed to run suite {suite_name}: {e}")
                suite_results.append(TestSuiteResult(
                    suite_name=suite_name,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    tests_run=0,
                    tests_passed=0,
                    tests_failed=0,
                    tests_skipped=0,
                    success_rate=0,
                    execution_time=0,
                    errors=[str(e)]
                ))
        
        # Generate and save reports
        report_files = self.reporter.save_reports()
        
        # Generate final summary
        summary = self.reporter.generate_summary_report()
        
        logger.info("=" * 50)
        logger.info("📊 Test Execution Complete")
        logger.info(f"Total Suites: {summary['total_suites']}")
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['total_passed']}")
        logger.info(f"Failed: {summary['total_failed']}")
        logger.info(f"Success Rate: {summary['overall_success_rate']:.2%}")
        logger.info(f"Total Time: {summary['total_execution_time']:.2f}s")
        logger.info(f"Reports saved to: {report_files['json_report']}")
        
        return {
            "summary": summary,
            "suite_results": suite_results,
            "report_files": report_files
        }
    
    async def run_specific_tests(self, test_paths: List[str]) -> Dict[str, Any]:
        """Run specific tests by path."""
        logger.info(f"🎯 Running specific tests: {test_paths}")
        
        # Run pytest with specific test paths
        exit_code = pytest.main(["-v", "--tb=short"] + test_paths)
        
        return {
            "success": exit_code == 0,
            "exit_code": exit_code
        }


async def main():
    """Main entry point for test execution."""
    parser = argparse.ArgumentParser(description="HAAI Testing Framework")
    parser.add_argument("--suite", type=str, help="Specific test suite to run")
    parser.add_argument("--tests", nargs="+", help="Specific test paths to run")
    parser.add_argument("--output", type=str, default="test_reports", help="Output directory for reports")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Create test runner
    config = TestConfiguration(
        timeout_seconds=60,
        enable_profiling=True
    )
    
    runner = AutomatedTestRunner(config)
    
    if args.tests:
        # Run specific tests
        results = await runner.run_specific_tests(args.tests)
    elif args.suite:
        # Run specific suite (placeholder - would need module import)
        logger.info(f"Running specific suite: {args.suite}")
        results = {"message": f"Suite {args.suite} execution would go here"}
    else:
        # Run all suites
        results = await runner.run_all_suites()
    
    return results


# Test configuration for pytest
pytest_plugins = [
    "tests.test_framework",
]


if __name__ == "__main__":
    # Run test execution
    results = asyncio.run(main())
    
    # Print summary
    if "summary" in results:
        print(f"\n✅ Test execution complete!")
        print(f"Overall success rate: {results['summary']['overall_success_rate']:.2%}")
        print(f"Total tests: {results['summary']['total_tests']}")
        print(f"Reports: {results['report_files']}")
    else:
        print(f"Test execution: {results}")