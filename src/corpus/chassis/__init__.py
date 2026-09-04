"""Chassis arm: observe a CI harness the way universe-explorer gates do.

This is not a probe seed and not a stress mutant. Toy-seed `ci_green` stays
the exit-0 oracle. Silent-suite is an extra column.
"""

from corpus.chassis.observe import ChassisObservation, observe
from corpus.chassis.silent_suite import classify_pytest

__all__ = ["ChassisObservation", "classify_pytest", "observe"]
