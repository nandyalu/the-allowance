"""What this deployment still needs before it can run.

One read-only route. It reports whether each requirement is met and never what
it is met with — no key, no secret, no account number appears in the response.
See backend/services/setup_check.py for why that is a security property rather
than a style choice.
"""
from fastapi import APIRouter

from backend.api.schemas import SetupStatusOut
from backend.services import setup_check

router = APIRouter(prefix="/api/setup", tags=["setup"])


@router.get("", response_model=SetupStatusOut)
def get_setup_status():
    """Whether this deployment can run, and what to paste if it cannot.

    Deliberately unauthenticated and safe to publish: the payload carries
    booleans, labels and example lines, so a reader learns what is missing and
    never what is configured.
    """
    return setup_check.status()
