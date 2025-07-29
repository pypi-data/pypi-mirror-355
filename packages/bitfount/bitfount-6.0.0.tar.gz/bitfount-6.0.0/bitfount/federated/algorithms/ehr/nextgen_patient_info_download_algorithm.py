"""NextGen Patient Info download algorithm to access patient data.

This module implements an algorithm for downloading all patient information
from NextGen's APIs. It provides functionality to:
- Authenticate with NextGen's FHIR, Enterprise, and SMART on FHIR APIs
- Look up and download relevant info and documents for a given list of patient_ids
"""

import os
from pathlib import Path
from typing import Any, ClassVar, List, Optional

from marshmallow import fields

from bitfount.data.datasources.base_source import BaseSource
from bitfount.data.datasplitters import DatasetSplitter
from bitfount.data.datastructure import DataStructure
from bitfount.externals.ehr.nextgen.api import NextGenEnterpriseAPI, NextGenFHIRAPI
from bitfount.externals.ehr.nextgen.authentication import NextGenAuthSession
from bitfount.externals.ehr.nextgen.querier import NextGenPatientQuerier
from bitfount.federated import _get_federated_logger
from bitfount.federated.algorithms.base import (
    BaseNonModelAlgorithmFactory,
    BaseWorkerAlgorithm,
    NoResultsModellerAlgorithm,
)

# if TYPE_CHECKING:
from bitfount.federated.privacy.differential import DPPodConfig
from bitfount.hub.api import (
    BitfountHub,
    SMARTOnFHIR,
)
from bitfount.hub.authentication_flow import (
    BitfountSession,
)
from bitfount.types import T_FIELDS_DICT

_logger = _get_federated_logger("bitfount.federated")


class _WorkerSide(BaseWorkerAlgorithm):
    """Worker side of the algorithm for downloading patient info using NextGen."""

    def __init__(
        self,
        fhir_url: str = NextGenFHIRAPI.DEFAULT_NEXT_GEN_FHIR_URL,
        enterprise_url: str = NextGenEnterpriseAPI.DEFAULT_NEXT_GEN_ENTERPRISE_URL,
        smart_on_fhir_url: Optional[str] = None,
        smart_on_fhir_resource_server_url: Optional[str] = None,
        session: Optional[BitfountSession] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the worker-side algorithm.

        Args:
            fhir_url: Base URL for the NextGen FHIR API.
            enterprise_url: Base URL for the NextGen Enterprise API.
            smart_on_fhir_url: Optional custom SMART on FHIR service URL.
            smart_on_fhir_resource_server_url: Optional custom SMART on FHIR resource
                server URL.
            session: BitfountSession object for use with SMARTOnFHIR service. Will be
                created if not provided.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)

        self.fhir_url = fhir_url
        self.enterprise_url = enterprise_url

        self.smart_on_fhir_url = smart_on_fhir_url
        self.smart_on_fhir_resource_server_url = smart_on_fhir_resource_server_url

        self.session = session if session else BitfountSession()
        if not self.session.authenticated:
            self.session.authenticate()

    def initialise(
        self,
        datasource: BaseSource,
        data_splitter: Optional[DatasetSplitter] = None,
        pod_dp: Optional[DPPodConfig] = None,
        pod_identifier: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Sets Datasource."""
        self.initialise_data(datasource=datasource, data_splitter=data_splitter)

    def run(
        self,
        patient_ids: List[str],
        download_path: Path,
        run_document_download: bool = True,
        run_json_dump: bool = True,
    ) -> None:
        """Download relevant info and documents related to supplied list of patients.

        Args:
            patient_ids: List of patient ids to download data for.
            download_path: Local path to save the downloaded patient info.
            run_document_download: Boolean flag to turn on/off document downloads,
                downloads documents by default.
            run_json_dump: Boolean flag to turn on/off patient info JSON dump,
                does the JSON dump by default.
        """
        # Get SMART on FHIR bearer token
        smart_auth = SMARTOnFHIR(
            session=self.session,
            smart_on_fhir_url=self.smart_on_fhir_url,
            resource_server_url=self.smart_on_fhir_resource_server_url,
        )
        nextgen_session = NextGenAuthSession(smart_auth)

        # Process each patient
        for patient_id in patient_ids:
            nextgen_querier = NextGenPatientQuerier.from_nextgen_session(
                patient_id=patient_id,
                nextgen_session=nextgen_session,
                fhir_url=self.fhir_url,
                enterprise_url=self.enterprise_url,
            )

            # Create directory for patient document download
            patient_folder_path = download_path / patient_id
            if not os.path.exists(patient_folder_path):
                os.mkdir(patient_folder_path)

            if run_document_download:
                nextgen_querier.download_all_documents(save_path=patient_folder_path)

            if run_json_dump:
                nextgen_querier.produce_json_dump(
                    save_path=patient_folder_path / "patient_info.json"
                )

        return


class NextGenPatientInfoDownloadAlgorithm(BaseNonModelAlgorithmFactory):
    """Algorithm for downloading patient info and documents from NextGen FHIR API."""

    fields_dict: ClassVar[T_FIELDS_DICT] = {
        "fhir_url": fields.Str(),
        "enterprise_url": fields.Str(),
        "smart_on_fhir_url": fields.Str(allow_none=True),
        "smart_on_fhir_resource_server_url": fields.Str(allow_none=True),
    }

    def __init__(
        self,
        datastructure: DataStructure,
        fhir_url: str = NextGenFHIRAPI.DEFAULT_NEXT_GEN_FHIR_URL,
        enterprise_url: str = NextGenEnterpriseAPI.DEFAULT_NEXT_GEN_ENTERPRISE_URL,
        smart_on_fhir_url: Optional[str] = None,
        smart_on_fhir_resource_server_url: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the algorithm.

        Args:
            datastructure: The data structure definition
            fhir_url: Optional custom FHIR API URL
            enterprise_url: Optional custom Enterprise API URL
            smart_on_fhir_url: Optional custom SMART on FHIR service URL
            smart_on_fhir_resource_server_url: Optional custom SMART on FHIR resource
                server URL
            **kwargs: Additional keyword arguments.
        """
        super().__init__(datastructure=datastructure, **kwargs)

        # Technically we won't need to use the fhir url
        #    but this is needed to instantiate the NextGenPatientQuerier
        self.fhir_url = fhir_url
        self.enterprise_url = enterprise_url
        self.smart_on_fhir_url = smart_on_fhir_url
        self.smart_on_fhir_resource_server_url = smart_on_fhir_resource_server_url

    def modeller(self, **kwargs: Any) -> NoResultsModellerAlgorithm:
        """Modeller-side of the algorithm."""
        return NoResultsModellerAlgorithm(
            log_message="Running NextGen Patient Info Download Algorithm",
            **kwargs,
        )

    def worker(
        self,
        hub: Optional[BitfountHub] = None,
        session: Optional[BitfountSession] = None,
        **kwargs: Any,
    ) -> _WorkerSide:
        """Worker-side of the algorithm."""
        if hub is None and session is None:
            raise ValueError("One of hub or session must be provided.")

        session_: BitfountSession
        if hub is not None and session is not None:
            _logger.warning(
                "Both hub and session were provided;"
                " using provided session in preference to hub session."
            )
            session_ = session
        elif hub is not None:
            session_ = hub.session
        else:  # session is not None
            assert session is not None  # nosec[assert_used]: Previous checks guarantee this is not None here # noqa: E501
            session_ = session

        return _WorkerSide(
            fhir_url=self.fhir_url,
            enterprise_url=self.enterprise_url,
            smart_on_fhir_url=self.smart_on_fhir_url,
            smart_on_fhir_resource_server_url=self.smart_on_fhir_resource_server_url,
            session=session_,
            **kwargs,
        )
