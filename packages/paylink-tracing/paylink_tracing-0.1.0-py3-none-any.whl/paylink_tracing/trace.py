import functools
import inspect
import time
from datetime import datetime, timezone
from typing import Any, Callable
from paylink_tracing.db import trace_collection
from paylink_tracing.config import ENV

def async_trace(func: Callable):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        func_name = func.__name__

        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        arguments = bound_args.arguments

        transaction_context = {
            "phone_number": arguments.get("phone_number"),
            "amount": arguments.get("amount"),
            "account_reference": arguments.get("account_reference"),
            "transaction_desc": arguments.get("transaction_desc"),
            "transaction_type": arguments.get("transaction_type"),
            "currency": "KES",
            "provider": "M-Pesa",
        }

        trace_log = {
            "function": func_name,
            "status": "started",
            "timestamp": datetime.now(timezone.utc),
            "transaction": transaction_context,
            "metadata": {
                "env": ENV,
            }
        }

        insert_result = trace_collection.insert_one(trace_log)
        trace_id = insert_result.inserted_id

        try:
            result = await func(*args, **kwargs)

            status = "error" if isinstance(result, dict) and "error" in result else "success"

            trace_collection.update_one(
                {"_id": trace_id},
                {"$set": {
                    "status": status,
                    "duration": round(time.time() - start_time, 3),
                    "timestamp": datetime.now(timezone.utc),
                    "result": result if isinstance(result, dict) else str(result),
                }}
            )
            return result
        except Exception as e:
            trace_collection.update_one(
                {"_id": trace_id},
                {"$set": {
                    "status": "error",
                    "duration": round(time.time() - start_time, 3),
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc),
                }}
            )
            raise
    return wrapper
