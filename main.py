"""
Main FastAPI application for Webhook Validator Service.
Simple implementation that meets test specification requirements.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

from app.routes import router

# Simple logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="Webhook Validator Service",
    description="A FastAPI service for validating payment, SMS, and email webhooks",
    version="1.0.0"
)

# Include webhook routes
app.include_router(router)

# Global exception handler for validation errors
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors with clear error messages."""
    logger.warning(f"Validation error on {request.url}: {exc}")
    
    return JSONResponse(
        status_code=400,  # Test specification requires 400 for validation errors
        content={
            "success": False,
            "message": "Validation failed",
            "errors": [
                {
                    "field": ".".join(str(loc) for loc in error.get("loc", ["unknown"])),
                    "message": error.get("msg", "Invalid value"),
                    "value": str(error.get("input", "unknown"))
                }
                for error in exc.errors()
            ]
        }
    )

# Handle FastAPI's RequestValidationError (422 -> 400)
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI request validation errors and convert to 400."""
    logger.warning(f"Request validation error on {request.url}: {exc}")
    
    return JSONResponse(
        status_code=400,  # Convert 422 to 400 as per test specification
        content={
            "success": False,
            "message": "Validation failed",
            "errors": [
                {
                    "field": ".".join(str(loc) for loc in error.get("loc", ["unknown"])),
                    "message": error.get("msg", "Invalid value"),
                    "value": str(error.get("input", "unknown"))
                }
                for error in exc.errors()
            ]
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Webhook Validator Service",
        "version": "1.0.0",
        "status": "running",
        "docs_url": "/docs",
        "endpoints": {
            "payment": "/webhook/payment",
            "sms": "/webhook/sms",
            "email": "/webhook/email"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "webhook-validator-service"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Webhook Validator Service")
    uvicorn.run(app, host="0.0.0.0", port=8000)
