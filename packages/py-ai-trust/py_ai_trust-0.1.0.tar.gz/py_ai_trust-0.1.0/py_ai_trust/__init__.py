# This file makes 'py_ai_trust' a Python package.

# You can define the package version here
__version__ = "0.1.0"

# Import key classes and functions directly into the package namespace
# This allows users to do `from py_ai_trust import TrustAuditor` instead of
# `from py_ai_trust.auditor import TrustAuditor`.

from .fairness import FairnessAuditor
from .mitigation import BiasMitigator
from .robustness import RobustnessTester
from .privacy import PrivacyAuditor
from .explainability import ExplainabilityEnhancer
from .auditor import TrustAuditor # The main orchestrator
from .utils import set_random_seed, setup_device, calculate_performance_metric, check_input_data_type

# You can also set up a package-wide logger here if desired,
# but it's typically better to configure logging in the main application
# that uses the library, or within each module if it's simpler.
# import logging
# logging.getLogger(__name__).addHandler(logging.NullHandler()) # Prevent "No handlers could be found for logger" messages

