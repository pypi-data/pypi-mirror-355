"""
    Copyright (C) 2025  QUDORA GmbH

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.


Job interface to communicate with QUDORA Cloud Jobs endpoint.
"""

from qiskit.providers import JobV1 as Job
from qiskit.providers.jobstatus import JobStatus
from qiskit.providers.backend import BackendV2
from qiskit.result import Result
from typing import List, Union
from .util import raise_exception_from_response, convert_jobstatusapi_to_jobstatusqiskit
import json
import requests


class QUDORAJob(Job):
    """ Job that interacts with the QUDORA Cloud"""

    def __init__(self, backend: BackendV2,
                 job_id: int,
                 shots: Union[List[int], None] = None,
                 metadata: Union[List[dict], None] = None):
        """ Object referencing a Job in the QUDORA Cloud

        Args:
            backend (BackendV2): Backend on which the job runs
            job_id (int): id of the job in the QUDORA Cloud
            shots (List[int]): List of shots for each provided circuit
            metadata (List[dict]): List of metadata for each provided circuit
        """
        super().__init__(backend, job_id)
        if shots is None:
            self.shots = []
        else:
            self.shots = shots
        self._backend = backend
        self.metadata = metadata
    
    def result(self, return_raw_format=False, timeout=None, wait=5) -> Result:
        """Waits for result of job and returns it.

        Args:
            return_raw_format (bool, optional): Return unprocessed result. Defaults to False.
            timeout (int, optional): Maximum time [s] to wait for result. Defaults to 30.
            wait (int, optional): Rate [s] at which to query results. Defaults to 5.
        Raises:
            RuntimeError: Raised if job failed in QUDORA Cloud.
        Returns:
            Result: Results of job in Qiskit-format.
        """
        self.wait_for_final_state(timeout=timeout, wait=wait)
        response = self._query_job_from_api(include_data=True)
        response = response.json()[0]

        if return_raw_format:
            return response

        # Check status from results
        status = convert_jobstatusapi_to_jobstatusqiskit(response['status'])
        if status != JobStatus.DONE:
            raise RuntimeError(f"Job finished with status {status.name}: \n \t {response['user_error']}")

        # Set shots retrieved from API
        self.shots = response['shots']

        # Check provided metadata.
        if not self.metadata is None:
            assert len(response['result']) == len(self.metadata), 'Number of metadata does not match number of results'

        # Assemble results of the multiple programs that might have been run.
        results = []
        for i in range(len(response['result'])):
            counts = json.loads(response['result'][i])
            res_metadata = None if self.metadata is None else self.metadata[i]
            res = {'data': {'counts': counts},
                   'shots': self.shots[i],
                   'success': True,
                   'header': {'metadata' : res_metadata}}
            results.append(res)
        
        # Assemble result of the Job.
        return Result.from_dict({
            'results': results,
            'backend_name': str(self._backend),
            'backend_version': self._backend.version,
            'job_id': self._job_id,
            'qobj_id': self._job_id,
            'success': True,
        })
        
    def submit(self):
        print("Submission is handled via the backend.run() functionality.")
        raise NotImplementedError

    def status(self) -> JobStatus:
        """Queries the job status from QUDORA Cloud.

        Raises:
            RuntimeError: Raised when connection fails.

        Returns:
            JobStatus: Status in Qiskit-format.
        """
        response = self._query_job_from_api(include_data=False)
        raise_exception_from_response(response)

        api_content = json.loads(response.text)
        status = api_content[0]["status"]
        job_status = convert_jobstatusapi_to_jobstatusqiskit(status)
        return job_status

    def _query_job_from_api(self, include_data=True) -> requests.Response: 
        """Queries the job from the API

        Args:
            include_data (bool, optional): Should job data (input,results,errors) be included. Defaults to True.
        Returns:
            requests.Response: Response from QUDORA Cloud.
        """
        response = requests.get(self._backend.url,
                    params={'job_id': self._job_id,
                            'include_results': include_data,
                            'include_input_data': include_data,
                            'include_user_error': include_data},
                    headers=self._backend._provider.get_header(),
                    timeout=self._backend._provider.timeout)
        return response
 
    def cancel(self):
        """Tries to cancel a job"""
        response = requests.put(self._backend.url,
                                  params={'job_id': self._job_id,
                                          'status_name': "Canceled"}
                                  ,headers=self._backend._provider.get_header(),
                                  timeout=self._backend._provider.timeout)
        
        raise_exception_from_response(response)
