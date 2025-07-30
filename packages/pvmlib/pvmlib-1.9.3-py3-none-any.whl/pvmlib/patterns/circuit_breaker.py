from pybreaker import CircuitBreaker, CircuitMemoryStorage
import os

fail_max = int(os.getenv("CIRCUIT_BREAKER_FAIL_MAX", 5))
reset_timeout = int(os.getenv("CIRCUIT_BREAKER_RESET_TIMEOUT", 60))

memory_storage = CircuitMemoryStorage(state="half-open")

circuit_breaker = CircuitBreaker(
    fail_max=fail_max,
    reset_timeout=reset_timeout,
    state_storage=memory_storage
)

"""
Configures a Circuit Breaker to handle potential service failures.

This code sets up a Circuit Breaker using the 'pybreaker' library.  The Circuit Breaker
monitors calls to a potentially failing service and prevents the application from
overloading the failing service.

Configuration:
    - fail_max: The number of consecutive failures before the circuit opens.  Defaults to 5,
      and can be overridden by the environment variable 'CIRCUIT_BREAKER_FAIL_MAX'.
    - reset_timeout: The time in seconds the circuit remains open before attempting a
      half-open state. Defaults to 60, and can be overridden by the environment
      variable 'CIRCUIT_BREAKER_RESET_TIMEOUT'.
    - state_storage:  The storage mechanism for the Circuit Breaker's state. Here,
      'CircuitMemoryStorage' is used, initialized in the half-open state.
"""