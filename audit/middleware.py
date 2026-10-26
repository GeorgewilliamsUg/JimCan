"""
Audit Context Middleware (Phase 3).
Extracts user identity, remote IP address, user agent, and request ID,
binding them to thread/coroutine contextvars for the duration of the request.
"""

import uuid
from audit.context import set_audit_context, reset_audit_context


class AuditContextMiddleware:
    """
    Middleware that establishes ambient audit context for every HTTP request.
    Extracts user, remote client IP (strictly from REMOTE_ADDR), user agent,
    and request UUID, resetting them upon request completion.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Resolve client IP (strictly REMOTE_ADDR)
        client_ip = request.META.get('REMOTE_ADDR')

        # 2. Extract user agent truncated to 255 chars
        user_agent = (request.META.get('HTTP_USER_AGENT') or "")[:255]

        # 3. Request ID (honor incoming X-Request-ID or generate new UUID4)
        incoming_req_id = request.headers.get('X-Request-ID', '').strip()
        request_id = incoming_req_id[:36] if incoming_req_id else str(uuid.uuid4())
        request.request_id = request_id

        # 4. Resolve authenticated user if available
        user = getattr(request, 'user', None)

        tokens = set_audit_context(
            actor=user,
            ip=client_ip,
            user_agent=user_agent,
            request_id=request_id
        )

        try:
            response = self.get_response(request)
            # Attach Request-ID header to response for audit cross-referencing
            response['X-Request-ID'] = request_id
            return response
        finally:
            reset_audit_context(tokens)
