"""synth_env namespace package

This file re-exports the existing modules in the *Environments* repository
under the ``synth_env`` namespace so that they can be imported as, e.g.,
``import synth_env.stateful.core``.

Since this is installed as a package, we directly import the modules
from their installed locations.
"""

# Import the actual modules that exist in the package
from . import environment
from . import stateful
from . import service
from . import examples
from . import tasks
from . import reproducibility
from . import v0_observability

# Make them available at the package level
__all__ = [
    "environment",
    "stateful",
    "service",
    "examples",
    "tasks",
    "reproducibility",
    "v0_observability",
]
