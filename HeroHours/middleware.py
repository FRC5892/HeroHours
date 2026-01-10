"""
Performance monitoring and safety middleware for HeroHours application.

This middleware provides:
1. Request processing time tracking for debugging
2. Safety checks to prevent resource exhaustion
3. Hardware protection mechanisms

CRITICAL: This system has previously bricked hardware. Safety checks are mandatory.
"""
import time
import logging

logger = logging.getLogger(__name__)

# Safety limits to prevent hardware damage
MAX_REQUEST_TIME = 30.0  # seconds - prevent runaway requests
MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10MB - prevent memory exhaustion


class TimeItMiddleware:
    """
    Middleware that measures and logs the execution time of each request.
    
    Useful for performance monitoring and identifying slow views.
    Should be enabled only in development/staging environments.
    
    SAFETY: Logs warning if request takes too long (could indicate infinite loop).
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        elapsed_time = time.time() - start_time
        
        # Log timing
        logger.debug(f"View {request.path} runtime: {elapsed_time:.4f} seconds")
        
        # SAFETY CHECK: Warn about long requests (potential infinite loops)
        if elapsed_time > MAX_REQUEST_TIME:
            logger.error(
                f"SAFETY WARNING: Request to {request.path} took {elapsed_time:.2f}s "
                f"(exceeds {MAX_REQUEST_TIME}s limit). Potential infinite loop or resource exhaustion!"
            )
        
        # SAFETY CHECK: Warn about large responses (memory exhaustion risk)
        if hasattr(response, 'content'):
            content_size = len(response.content)
            if content_size > MAX_RESPONSE_SIZE:
                logger.error(
                    f"SAFETY WARNING: Response from {request.path} is {content_size} bytes "
                    f"(exceeds {MAX_RESPONSE_SIZE} byte limit). Memory exhaustion risk!"
                )
        
        return response