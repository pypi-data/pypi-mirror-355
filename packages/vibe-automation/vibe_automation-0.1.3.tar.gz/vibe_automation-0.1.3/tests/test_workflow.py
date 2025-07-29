import logging
import os
import warnings
from unittest.mock import MagicMock, patch
from typing import Any

import pytest
from pydantic import BaseModel

from va.workflow import workflow, _process_function_arguments, _is_pydantic_model


class ContactModel(BaseModel):
    name: str
    phone: str


class TestWorkflowDecorator:
    """Test cases for the workflow decorator and its input/logging behavior."""

    def test_workflow_basic_functionality(self):
        """Test basic workflow decoration without managed execution."""
        called = False

        @workflow("test_workflow")
        def test_func():
            nonlocal called
            called = True

        test_func()
        assert called

    def test_workflow_with_args(self):
        """Test workflow with regular arguments in non-managed execution."""
        result = []

        @workflow("test_workflow_args")
        def test_func(name: str, age: int):
            result.extend([name, age])

        with (
            patch("va.workflow.get_store"),
            patch("va.workflow.Automation") as mock_automation_class,
        ):
            mock_automation = MagicMock()
            mock_automation_class.return_value = mock_automation

            test_func("John", 25)

        assert result == ["John", 25]

    @patch.dict(os.environ, {"VA_EXECUTION_ID": "test-execution-123"})
    def test_managed_execution_detection(self):
        """Test that managed execution is properly detected."""
        execution_started = False

        @workflow("test_workflow")
        def test_func():
            nonlocal execution_started
            execution_started = True

        with (
            patch("va.workflow.get_store"),
            patch("va.workflow.Automation") as mock_automation_class,
        ):
            mock_automation = MagicMock()
            mock_automation.execution_id = "test-execution-123"
            mock_automation_class.return_value = mock_automation

            test_func()

            # Verify automation was created with correct parameters
            mock_automation_class.assert_called_once()
            args, kwargs = mock_automation_class.call_args
            assert args[1] == "test_workflow"  # workflow_name
            assert args[2] == "test-execution-123"  # execution_id

            assert execution_started


class TestInputReplacement:
    """Test cases for input replacement behavior."""

    def test_input_replacement_with_pydantic_model(self):
        """Test input replacement with Pydantic model validation."""
        mock_automation = MagicMock()
        mock_automation.execution_id = "test-exec"
        mock_automation.execution.get_input.return_value = {
            "name": "Alice",
            "phone": "555-1234",
        }

        def test_func(input: ContactModel, other_param: str = "default"):
            return input, other_param

        modified_args, modified_kwargs = _process_function_arguments(
            test_func,
            (ContactModel(name="Original", phone="000-0000"), "original"),
            {},
            mock_automation,
            True,
        )

        # First argument should be replaced with validated input
        assert isinstance(modified_args[0], ContactModel)
        assert modified_args[0].name == "Alice"
        assert modified_args[0].phone == "555-1234"
        # Second argument should remain unchanged
        assert modified_args[1] == "original"

    def test_input_replacement_without_type_hint(self):
        """Test input replacement without Pydantic validation."""
        mock_automation = MagicMock()
        mock_automation.execution.get_input.return_value = {"key": "value"}

        def test_func(input, other_param: str = "default"):
            return input, other_param

        modified_args, modified_kwargs = _process_function_arguments(
            test_func, ("original_input", "original"), {}, mock_automation, True
        )

        # First argument should be replaced with raw input
        assert modified_args[0] == {"key": "value"}
        assert modified_args[1] == "original"

    def test_input_validation_failure(self):
        """Test behavior when Pydantic validation fails."""
        mock_automation = MagicMock()
        mock_automation.execution.get_input.return_value = {
            "name": "Alice"
            # Missing required 'phone' field
        }

        def test_func(input: ContactModel):
            return input

        with pytest.raises(ValueError, match="Input validation failed"):
            _process_function_arguments(
                test_func,
                (ContactModel(name="Original", phone="000-0000"),),
                {},
                mock_automation,
                True,
            )

    def test_no_input_replacement_in_local_execution(self):
        """Test that input is not replaced in local (non-managed) execution."""
        mock_automation = MagicMock()

        def test_func(input: ContactModel):
            return input

        original_contact = ContactModel(name="Original", phone="000-0000")
        modified_args, modified_kwargs = _process_function_arguments(
            test_func,
            (original_contact,),
            {},
            mock_automation,
            False,  # is_managed_execution = False
        )

        # Input should remain unchanged
        assert modified_args[0] is original_contact
        mock_automation.execution.get_input.assert_not_called()

    def test_warning_for_wrong_parameter_name(self):
        """Test warning when first parameter is not named 'input' in managed execution."""
        mock_automation = MagicMock()

        def test_func(data: ContactModel):
            return data

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            _process_function_arguments(
                test_func,
                (ContactModel(name="Test", phone="123"),),
                {},
                mock_automation,
                True,
            )

            assert len(w) == 1
            assert "first parameter is named 'data' instead of 'input'" in str(
                w[0].message
            )

    def test_warning_on_input_fetch_error(self):
        """Test warning when execution input cannot be retrieved."""
        mock_automation = MagicMock()
        mock_automation.execution.get_input.side_effect = Exception("Network error")

        def test_func(input: ContactModel):
            return input

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            original_contact = ContactModel(name="Original", phone="000")
            modified_args, modified_kwargs = _process_function_arguments(
                test_func, (original_contact,), {}, mock_automation, True
            )

            # Should use original argument and warn
            assert modified_args[0] is original_contact
            assert len(w) == 1
            assert "Failed to get execution input" in str(w[0].message)


class TestLoggerInjection:
    """Test cases for logger injection behavior."""

    def test_logger_injection(self):
        """Test that logger is automatically injected for logger parameters."""
        mock_automation = MagicMock()
        mock_automation.execution_id = "test-exec-456"

        def test_func(input: str, logger: logging.Logger):
            return input, logger

        modified_args, modified_kwargs = _process_function_arguments(
            test_func, ("test_input",), {}, mock_automation, False
        )

        # Logger should be injected as kwarg since not provided positionally
        assert len(modified_args) == 1
        assert modified_args[0] == "test_input"
        assert "logger" in modified_kwargs
        assert isinstance(modified_kwargs["logger"], logging.Logger)
        assert "test-exec-456" in modified_kwargs["logger"].name

    def test_logger_not_overridden_if_provided(self):
        """Test that provided logger is not overridden."""
        mock_automation = MagicMock()
        custom_logger = logging.getLogger("custom")

        def test_func(logger: logging.Logger):
            return logger

        modified_args, modified_kwargs = _process_function_arguments(
            test_func, (custom_logger,), {}, mock_automation, False
        )

        # Should keep the provided logger
        assert modified_args[0] is custom_logger

    def test_logger_injection_as_kwarg(self):
        """Test logger injection when logger is expected as keyword argument."""
        mock_automation = MagicMock()
        mock_automation.execution_id = "test-exec-789"

        def test_func(input: str, other_param: int = 5, logger: logging.Logger = None):
            return input, other_param, logger

        modified_args, modified_kwargs = _process_function_arguments(
            test_func, ("test_input",), {"other_param": 10}, mock_automation, False
        )

        # Logger should be in kwargs
        assert len(modified_args) == 1
        assert modified_args[0] == "test_input"
        assert "other_param" in modified_kwargs
        assert modified_kwargs["other_param"] == 10
        assert "logger" in modified_kwargs
        assert isinstance(modified_kwargs["logger"], logging.Logger)


class TestPydanticValidation:
    """Test cases for Pydantic model validation utilities."""

    def test_is_pydantic_model_detection(self):
        """Test detection of Pydantic models."""
        assert _is_pydantic_model(ContactModel) is True
        assert _is_pydantic_model(str) is False
        assert _is_pydantic_model(dict) is False
        assert _is_pydantic_model(Any) is False

    def test_is_pydantic_model_with_none(self):
        """Test Pydantic model detection with None."""
        assert _is_pydantic_model(None) is False


class TestIntegrationScenarios:
    """Integration test cases combining multiple features."""

    @patch.dict(os.environ, {"VA_EXECUTION_ID": "integration-test"})
    def test_full_managed_execution_workflow(self):
        """Test complete managed execution with input replacement and logging."""
        execution_result = {}

        @workflow("integration_test")
        def integration_func(input: ContactModel, logger: logging.Logger):
            execution_result["input"] = input
            execution_result["logger_name"] = logger.name
            logger.info("Test log message")

        mock_store = MagicMock()
        mock_automation = MagicMock()
        mock_automation.execution_id = "integration-test"
        mock_automation.execution.get_input.return_value = {
            "name": "Integration Test",
            "phone": "999-8888",
        }

        with (
            patch("va.workflow.get_store", return_value=mock_store),
            patch("va.workflow.Automation", return_value=mock_automation),
        ):
            # Call with original input argument that should be replaced
            # Don't provide logger so it gets injected
            integration_func(ContactModel(name="Original", phone="000-0000"))

            # Verify input was replaced
            assert isinstance(execution_result["input"], ContactModel)
            assert execution_result["input"].name == "Integration Test"
            assert execution_result["input"].phone == "999-8888"

            # Verify logger was injected
            assert "integration-test" in execution_result["logger_name"]

            # Verify automation lifecycle
            mock_automation.execution.mark_start.assert_called_once()
            mock_automation.execution.mark_stop.assert_called_once()

    def test_local_development_workflow(self):
        """Test workflow behavior during local development (no managed execution)."""
        execution_result = {}

        @workflow("local_test")
        def local_func(input: ContactModel, logger: logging.Logger):
            execution_result["input"] = input
            execution_result["logger"] = logger

        original_contact = ContactModel(name="Local", phone="123-4567")
        original_logger = logging.getLogger("local")

        mock_store = MagicMock()
        mock_automation = MagicMock()
        mock_automation.execution_id = "local-generated-id"

        with (
            patch("va.workflow.get_store", return_value=mock_store),
            patch("va.workflow.Automation", return_value=mock_automation),
            patch("uuid.uuid4") as mock_uuid,
        ):
            mock_uuid.return_value.hex = "local-generated-id"

            # Call with arguments that should NOT be replaced
            local_func(original_contact, original_logger)

            # Verify arguments were NOT replaced (local development mode)
            assert execution_result["input"] is original_contact
            assert execution_result["logger"] is original_logger

            # Verify execution lifecycle still works
            mock_automation.execution.mark_start.assert_called_once()
            mock_automation.execution.mark_stop.assert_called_once()
