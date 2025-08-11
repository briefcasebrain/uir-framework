"""Tests for circuit breaker functionality"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.uir.core.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker:
    """Test circuit breaker implementation"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state allows calls"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        assert result == "success"
        assert cb.get_state() == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        async def failing_func():
            raise Exception("Test failure")
        
        # Fail 3 times to open circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await cb.call(failing_func)
        
        assert cb.get_state() == CircuitState.OPEN
        
        # Circuit should reject calls when open
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await cb.call(failing_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_state(self):
        """Test circuit breaker transitions to half-open state"""
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1,  # 1 second for quick testing
            half_open_max_calls=2
        )
        
        async def failing_func():
            raise Exception("Test failure")
        
        async def success_func():
            return "success"
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await cb.call(failing_func)
        
        assert cb.get_state() == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Circuit should allow test call in half-open state
        result = await cb.call(success_func)
        assert result == "success"
        
        # After successful calls, circuit should close
        result = await cb.call(success_func)
        assert cb.get_state() == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_to_open(self):
        """Test circuit breaker returns to open from half-open on failure"""
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1,
            half_open_max_calls=2
        )
        
        async def failing_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await cb.call(failing_func)
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Fail in half-open state
        with pytest.raises(Exception):
            await cb.call(failing_func)
        
        assert cb.get_state() == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_reset(self):
        """Test manual circuit breaker reset"""
        cb = CircuitBreaker(failure_threshold=2)
        
        async def failing_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await cb.call(failing_func)
        
        assert cb.get_state() == CircuitState.OPEN
        
        # Manual reset
        cb.reset()
        assert cb.get_state() == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_custom_exception(self):
        """Test circuit breaker with custom exception type"""
        
        class CustomException(Exception):
            pass
        
        cb = CircuitBreaker(
            failure_threshold=2,
            expected_exception=CustomException
        )
        
        async def custom_failing_func():
            raise CustomException("Custom failure")
        
        async def other_failing_func():
            raise ValueError("Other failure")
        
        # Custom exception should count as failure
        for _ in range(2):
            with pytest.raises(CustomException):
                await cb.call(custom_failing_func)
        
        assert cb.get_state() == CircuitState.OPEN
        
        # Reset for next test
        cb.reset()
        
        # Other exceptions should not count
        with pytest.raises(ValueError):
            await cb.call(other_failing_func)
        
        assert cb.get_state() == CircuitState.CLOSED
        assert cb.failure_count == 0