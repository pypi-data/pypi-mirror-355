import logging
import json
import time
import azure.functions as func
from azpaddypy.mgmt.logging import create_function_logger

# Initialize the logger
logger = create_function_logger(
    function_app_name="test-function-app", function_name="test-function"
)


@logger.trace_function(log_args=True, log_result=True)
def process_request(req_body: dict) -> dict:
    """Process the request body and return a response"""
    # Simulate some processing time
    time.sleep(0.1)

    # Log the request processing
    logger.info(
        "Processing request",
        extra={
            "request_id": req_body.get("request_id", "unknown"),
            "action": req_body.get("action", "unknown"),
        },
    )

    return {
        "status": "success",
        "message": "Request processed successfully",
        "data": req_body,
    }


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function entry point"""
    try:
        # Start timing the request
        start_time = time.time()

        # Get request details
        method = req.method
        url = req.url
        headers = dict(req.headers)

        # Log the incoming request
        logger.log_request(
            method=method,
            url=url,
            status_code=200,  # We'll update this if there's an error
            duration_ms=0,  # We'll update this at the end
            extra={"headers": headers, "request_type": "http_trigger"},
        )

        # Create a span for the entire function execution
        with logger.create_span("function_execution") as span:
            # Add request metadata to the span
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", url)

            # Parse request body
            try:
                req_body = req.get_json()
            except ValueError:
                req_body = {}

            # Log the request body
            logger.info("Received request body", extra={"body": req_body})

            # Process the request
            result = process_request(req_body)

            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000

            # Log successful completion
            logger.log_function_execution(
                function_name="main",
                duration_ms=duration_ms,
                success=True,
                extra={"method": method, "url": url},
            )

            # Return the response
            return func.HttpResponse(
                json.dumps(result), mimetype="application/json", status_code=200
            )

    except Exception as e:
        # Calculate request duration
        duration_ms = (time.time() - start_time) * 1000

        # Log the error
        logger.error(
            f"Error processing request: {str(e)}",
            extra={"method": method, "url": url, "error_type": type(e).__name__},
        )

        # Log failed execution
        logger.log_function_execution(
            function_name="main",
            duration_ms=duration_ms,
            success=False,
            extra={"error": str(e), "error_type": type(e).__name__},
        )

        # Return error response
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500,
        )
