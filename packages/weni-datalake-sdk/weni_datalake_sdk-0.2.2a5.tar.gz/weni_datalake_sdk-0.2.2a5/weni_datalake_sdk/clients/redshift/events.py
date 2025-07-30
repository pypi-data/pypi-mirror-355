import os

from weni_datalake_sdk.clients.redshift.redshift_client import query_dc_api


def get_events(
    project: str = None,
    date_start: str = None,
    date_end: str = None,
    query_params: dict = None,
) -> dict:
    metric = os.environ.get("EVENTS_METRIC_NAME")

    final_params = query_params.copy() if query_params else {}

    if project:
        final_params["project"] = project
    else:
        raise Exception("Project is required")

    if date_start:
        final_params["date_start"] = date_start
    else:
        raise Exception("Date start is required")

    if date_end:
        final_params["date_end"] = date_end
    else:
        raise Exception("Date end is required")

    try:
        print(f"final_params: {final_params}")
        result = query_dc_api(metric=metric, query_params=final_params)
        return result.json()

    except Exception as e:
        raise Exception(f"Error querying events: {e}")
