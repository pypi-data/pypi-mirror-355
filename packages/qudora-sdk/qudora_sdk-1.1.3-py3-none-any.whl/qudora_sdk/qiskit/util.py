"""
    Copyright (C) 2025  QUDORA GmbH

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

    
Utility functions for the qiskit provider.
"""

from requests import Response
from qiskit.providers.jobstatus import JobStatus
from enum import Enum

def raise_exception_from_response(response : Response):
    """Handles exceptions contained in responses from QUDORA Cloud.

    Args:
        response (requests.Response): Response from requests package.

    Raises:
        RuntimeError: Raised when response contains an error.
    """
    if response.status_code != 200:
        raise RuntimeError(f"Error from QUDORA Cloud: {response.text}")
    

class JobStatusNameAPI(str, Enum):
    """ Jobstati defined by the API """
    SUBMITTED = 'Submitted'
    RUNNING = 'Running'
    COMPLETED = 'Completed'
    CANCELED = 'Canceled'
    FAILED = 'Failed'
    DELETED = 'Deleted'
    CANCELLING = 'Cancelling'
    UNCOMPILED = 'Uncompiled'

class JobStatusID(int, Enum):
    """ IDs for the Jobstati from above """
    SUBMITTED = 1
    RUNNING = 2
    COMPLETED = 3
    CANCELED = 4
    FAILED = 5
    DELETED = 6
    CANCELLING = 7
    UNCOMPILED = 8


def convert_jobstatusapi_to_jobstatusqiskit(status: JobStatusNameAPI) -> JobStatus:
    """ Converts from Status in QUDORA Cloud to Qiskit Status

    Args:
        status (JobStatusNameAPI): QUDORA Cloud Status

    Raises:
        RuntimeError: When QUDORA Cloud Status is unknown.

    Returns:
        JobStatus: Equivalent Qiskit JobStatus.
    """
    if status == JobStatusNameAPI.SUBMITTED or status == JobStatusNameAPI.UNCOMPILED:
        return JobStatus.QUEUED
    elif status == JobStatusNameAPI.RUNNING or status == JobStatusNameAPI.CANCELLING:
        return JobStatus.RUNNING
    elif status == JobStatusNameAPI.COMPLETED:
        return JobStatus.DONE
    elif status == JobStatusNameAPI.CANCELED:
        return JobStatus.CANCELLED
    elif status == JobStatusNameAPI.FAILED:
        return JobStatus.ERROR
    
    raise RuntimeError(f"Could not convert API-Status '{status}' to qiskit.JobStatus")