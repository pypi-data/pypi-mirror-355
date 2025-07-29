import httpx
import logging
from pydantic import BaseModel

from .models import Workflow, CodeVersion, SystemInfo, Prompt, CodeResult
from .settings import settings, Settings


class CoDatascientistBackendResponse(BaseModel):
    workflow: Workflow
    code_to_run: CodeVersion | None = None


async def test_connection() -> str:
    return await _call_co_datascientist_client("/test_connection", {})


async def start_workflow(code: str, system_info: SystemInfo) -> CoDatascientistBackendResponse:
    response = await _call_co_datascientist_client("/start_workflow", {
        "prompt": Prompt(code=code).model_dump(),
        "system_info": system_info.model_dump()
    })
    return CoDatascientistBackendResponse.model_validate(response)


async def finished_running_code(workflow_id, code_version_id, result: CodeResult) -> CoDatascientistBackendResponse:
    response = await _call_co_datascientist_client(
        "/finished_running_code",
        {"workflow_id": workflow_id, "code_version_id": code_version_id, "result": result.model_dump()})
    return CoDatascientistBackendResponse.model_validate(response)


async def stop_workflow(workflow_id) -> None:
    await _call_co_datascientist_client("/stop_workflow", {"workflow_id": workflow_id})


# NEW COST TRACKING API METHODS
async def get_user_costs() -> dict:
    """Get detailed costs for the authenticated user"""
    return await _call_co_datascientist_client("/user/costs", {})


async def get_user_costs_summary() -> dict:
    """Get summary costs for the authenticated user"""
    return await _call_co_datascientist_client("/user/costs/summary", {})


async def get_workflow_costs(workflow_id: str) -> dict:
    """Get costs for a specific workflow"""
    return await _call_co_datascientist_client(f"/user/costs/workflow/{workflow_id}", {})


async def _call_co_datascientist_client(path, data):
    # Ensure API key is available before making the request
    if not settings.api_key.get_secret_value():
        settings.get_api_key()
    
    url = settings.backend_url + path
    logging.info(f"Dev mode (instance): {settings.dev_mode}")
    logging.info(f"Dev mode (class override): {Settings._dev_mode_override}")
    logging.info(f"Dev mode (effective): {settings.effective_dev_mode}")
    logging.info(f"Backend URL: {settings.backend_url}")
    logging.info(f"Making request to: {url}")
    logging.info(f"Request data keys: {list(data.keys()) if data else 'No data'}")
    
    try:
        async with httpx.AsyncClient(verify=settings.verify_ssl, timeout=None) as client:
            if data:
                # POST request
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {settings.api_key.get_secret_value()}"},
                    json=data)
            else:
                # GET request
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {settings.api_key.get_secret_value()}"})
            
            logging.info(f"Response status: {response.status_code}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.error(f"Request to {url} failed: {e}")
        raise

