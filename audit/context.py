"""
Audit Context Module (Phase 3).
Uses Python contextvars to track current request user, client IP,
user agent, and request ID across asynchronous or decoupled execution boundaries.
"""

import contextvars
import uuid
from typing import Dict, Any, Optional

_current_actor = contextvars.ContextVar('audit_current_actor', default=None)
_current_ip = contextvars.ContextVar('audit_current_ip', default=None)
_current_user_agent = contextvars.ContextVar('audit_current_user_agent', default=None)
_current_request_id = contextvars.ContextVar('audit_current_request_id', default=None)


def set_audit_context(
    actor=None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Sets audit context variables for the current execution thread/task."""
    token_actor = _current_actor.set(actor)
    token_ip = _current_ip.set(ip)
    token_ua = _current_user_agent.set(user_agent)
    token_req = _current_request_id.set(request_id or str(uuid.uuid4()))
    return {
        'actor': token_actor,
        'ip': token_ip,
        'user_agent': token_ua,
        'request_id': token_req,
    }


def reset_audit_context(tokens: Dict[str, Any]):
    """Resets audit context variables to their previous states using stored tokens."""
    if 'actor' in tokens:
        _current_actor.reset(tokens['actor'])
    if 'ip' in tokens:
        _current_ip.reset(tokens['ip'])
    if 'user_agent' in tokens:
        _current_user_agent.reset(tokens['user_agent'])
    if 'request_id' in tokens:
        _current_request_id.reset(tokens['request_id'])


def get_audit_context() -> Dict[str, Any]:
    """Retrieves current audit context variables, falling back to system defaults if none set."""
    actor = _current_actor.get()
    actor_username = "system"
    if actor and hasattr(actor, 'is_authenticated') and actor.is_authenticated:
        actor_username = actor.get_username()
    elif isinstance(actor, str) and actor:
        actor_username = actor

    return {
        'actor': actor if getattr(actor, 'is_authenticated', False) else None,
        'actor_username': actor_username,
        'client_ip': _current_ip.get(),
        'user_agent': _current_user_agent.get() or "",
        'request_id': _current_request_id.get() or "",
    }
