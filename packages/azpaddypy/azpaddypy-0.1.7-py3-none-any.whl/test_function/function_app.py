import logging
import json
import time
import asyncio
import azure.functions as func
from azpaddypy.mgmt.logging import create_function_logger

app = func.FunctionApp()

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


@logger.trace_function(log_args=True, log_result=True)
async def process_request_async(req_body: dict) -> dict:
    """Process the request body asynchronously and return a response"""
    # Simulate some async processing time
    await asyncio.sleep(0.1)

    # Log the request processing
    logger.info(
        "Processing async request",
        extra={
            "request_id": req_body.get("request_id", "unknown"),
            "action": req_body.get("action", "unknown"),
            "is_async": True,
        },
    )

    return {
        "status": "success",
        "message": "Async request processed successfully",
        "data": req_body,
    }


@app.function_name(name="test-function")
@app.route(route="test-function", auth_level=func.AuthLevel.ANONYMOUS)
async def test_function(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function HTTP trigger that processes requests both synchronously and asynchronously"""
    start_time = time.time()
    method = req.method
    url = str(req.url)

    try:
        # Get request body
        req_body = req.get_json()

        # Process request based on the action
        action = req_body.get("action", "").lower()

        if action == "async":
            # Process request asynchronously
            result = await process_request_async(req_body)
        else:
            # Process request synchronously
            result = process_request(req_body)

        # Calculate request duration
        duration_ms = (time.time() - start_time) * 1000

        # Log successful request
        logger.log_request(
            method=method,
            url=url,
            status_code=200,
            duration_ms=duration_ms,
            extra={
                "request_id": req_body.get("request_id", "unknown"),
                "action": action,
                "is_async": action == "async",
            },
        )

        # Return success response
        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200,
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
            function_name="test_function",
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
