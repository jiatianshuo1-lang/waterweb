import logging
import time
import uuid

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.request_id = request_id

        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        logger.info(
            '[REQ] id=%s method=%s path=%s status=%s duration=%.3fs user=%s',
            request_id,
            request.method,
            request.get_full_path(),
            response.status_code,
            duration,
            getattr(request, 'user', 'anonymous'),
        )

        response['X-Request-ID'] = request_id
        return response
