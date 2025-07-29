import pytest
from paylink_tracing.trace import async_trace
from unittest.mock import MagicMock
import mongomock

@async_trace
async def dummy_func(phone_number, amount, account_reference, transaction_desc, transaction_type):
    return {"status": "success"}

@pytest.mark.asyncio
async def test_async_trace_logs_success(mocker):
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "abc123"

    mock_insert = mocker.patch(
        "paylink_tracing.trace.trace_collection.insert_one",
        return_value=mock_insert_result
    )

    mock_update = mocker.patch(
        "paylink_tracing.trace.trace_collection.update_one",
        return_value=None
    )

    result = await dummy_func("254712345678", 100, "ABC123", "Payment", "CustomerPayBillOnline")

    assert result["status"] == "success"
    mock_insert.assert_called_once()
    mock_update.assert_called()
