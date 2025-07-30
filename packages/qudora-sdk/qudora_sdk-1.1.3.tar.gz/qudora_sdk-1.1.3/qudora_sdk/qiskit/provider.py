""" 
    Copyright (C) 2025  QUDORA GmbH

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.


Qiskit-Provider for QUDORA.
"""
import requests
import json
from collections.abc import Callable
from typing import Union
from qiskit.providers import ProviderV1 as Provider
from qiskit.providers.providerutils import filter_backends
from qiskit.providers.exceptions import QiskitBackendNotFoundError
from .backend import QUDORABackend
from .util import raise_exception_from_response


class QUDORAProvider(Provider):
    """Provider for backends from QUDORA.
    Typical usage is:
    .. code-block:: python
        from qudora_sdk.qiskit import QUDORAProvider
        provider = QUDORAProvider('MY_TOKEN')
    where `'MY_TOKEN'` is the API token provided by QUDORA.
    """

    def __init__(self, token: str, url: str = "https://api.qudora.com/", timeout: Union[int, None] = None):
        """Initializes a QUDORA-Qiskit-provider.

        Args:
            token (str): API-Token for authenticating with QUDORA Cloud.
            url (str, optional):URL to the API of the QUDORA Cloud. Defaults to "https://api.qudora.com/".
            timeout (int, optional): Timeout for Requests to cloud. Defaults to 10.
        """
        super().__init__()
        self.url = url
        self.token = token
        self.name = 'qudora_provider'

        self.timeout = timeout
        
        # Get backends from provided URL
        self._get_backends()

    def get_header(self) -> dict:
        """Creates the authentication header for the API

        Returns:
            dict: Authorization header for the API.
        """
        return {"Authorization": "Bearer "+ self.token}

    def _get_backends(self):
        """Sets the backends property of this object.

        Raises:
            RuntimeError: Raised when errors appear on connection to API.
        """
        # Clears the backends
        self._backends = []

        try:
            header = self.get_header()
        except RuntimeError:
            print("No API Token provided. Can not get backends from QUDORA Cloud.")
        
        try:
            response = requests.get(self.url + "backends/", headers=header, timeout=self.timeout)
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError("Could not connect to API. Did you provide the correct URL?") from exc
        
        raise_exception_from_response(response)
    
        for backend_info in json.loads(response.text):   
            self._backends.append(QUDORABackend(self.url + "jobs/", self, backend_info))


    def backends(self, name : str = None, filters : Callable = None, **kwargs) -> list[QUDORABackend]:
        """Returns backends filtered by names or other callable filters.
        For the name it is only checked if the provided string is included in the backend name.

        Args:
            name (str, optional): Name to filter the backends. Defaults to None.
            filters (Callable, optional): Callable filters. Defaults to None.

        Returns:
            list[Backend]: List of backends matching the filter.
        """
        backends = self._backends
        if name:
            backends = [backend for backend in backends if name in str(backend)]
        return filter_backends(backends, filters=filters, **kwargs)

    def __str__(self):
        return f"<QUDORAProvider(name={self.name})>"

    def __repr__(self):
        return self.__str__()

    def get_backend(self, name : str = None, **kwargs : dict) -> QUDORABackend:
        """Return a single backend matching the specified filtering.
        Args:
            name (str): name of the backend.
            **kwargs: dict used for filtering.
        Returns:
            Backend: a backend matching the filtering.
        Raises:
            QiskitBackendNotFoundError: if no backend could be found or
                more than one backend matches the filtering criteria.
        """
        backends = self.backends(name, **kwargs)
        if len(backends) > 1:
            raise QiskitBackendNotFoundError('More than one backend matches criteria.')
        if not backends:
            raise QiskitBackendNotFoundError('No backend matches criteria.')
        return backends[0]


    def __eq__(self, other: Provider) -> bool: 
        """Equality comparison. Two providers are considered equal if they are the same type and have the same token.
        Args:
            other (Provider): Other qiskit provider
        Returns:
            bool: Equality of providers
        """
        return (type(self).__name__ == type(other).__name__) and (self.token == other.token)
