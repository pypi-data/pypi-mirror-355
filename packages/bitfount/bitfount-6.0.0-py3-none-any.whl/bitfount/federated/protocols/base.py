"""Pod communication protocols.

These classes take an algorithm and are responsible for organising the communication
between Pods and Modeller.

Attributes:
    registry: A read-only dictionary of protocol factory names to their
        implementation classes.

Current message flow between the workers with 2 batches
 and modeller for streaming batched execution:

    1. Workers send `NUM_BATCHES`=-1 to Modeller.
    2. Workers send `CURRENT_BATCH_ID`=1 to Modeller.
    3. Modeller states it's processing batch 1, Worker send a `TASK_START` to Modeller.
    4. Modeller waits for all Pods to be ready.
    5. Modeller sends `TASK_START` to Worker.
    6. Workers run batch 1.
    7. Workers send `EVALUATION_RESULTS` to Modeller.
    8. Workers send `CURRENT_BATCH_ID`=2 to Modeller.
    9. Workers run batch 2 (final), Modeller states it's processing batch 2.
    10. Workers send `EVALUATION_RESULTS` to Modeller.
    11. Workers send `BATCHES_COMPLETE` to Modeller, modeller exits steaming loop.
    12. Modeller sends `TASK_COMPLETE` to Workers.

Batched execution is currently only supported for single worker cases, but for
future reference, in the case where multiple workers are expected to execute
the current task, the modeller will choose to display to the user the current
batch id corresponding to the slowest user.
"""

from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
import asyncio
from collections.abc import Callable, Collection, Mapping, Sequence
from datetime import datetime
from functools import wraps
import inspect
import os
from pathlib import Path
import types
from types import FunctionType, MappingProxyType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Final,
    Generic,
    NamedTuple,
    NoReturn,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
)

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
import more_itertools

from bitfount import config
from bitfount.data.datasources.base_source import (
    BaseSource,
    FileSystemIterableSource,
)
from bitfount.data.datasplitters import (
    DatasetSplitter,
    PercentageSplitter,
    SplitterDefinedInData,
)
from bitfount.data.types import DataSplit
import bitfount.federated.algorithms.base as algorithms
from bitfount.federated.algorithms.base import InitialSetupAlgorithm
from bitfount.federated.algorithms.model_algorithms.base import (
    _BaseModelAlgorithmFactory,
)
from bitfount.federated.algorithms.model_algorithms.inference import (
    _WorkerSide as ModelInferenceWorkerSideAlgorithm,
)
from bitfount.federated.authorisation_checkers import (
    IdentityVerificationMethod,
    InferenceLimits,
    ProtocolContext,
)
from bitfount.federated.exceptions import (
    AlgorithmError,
    BitfountTaskStartError,
    NoNewDataError,
    ProtocolError,
    TaskAbortError,
)
from bitfount.federated.helper import (
    TaskContext,
    _check_and_update_pod_ids,
    _create_message_service,
    _get_idp_url,
)
from bitfount.federated.logging import _get_federated_logger
from bitfount.federated.modeller import _Modeller
from bitfount.federated.privacy.differential import DPPodConfig
from bitfount.federated.roles import _RolesMixIn
from bitfount.federated.transport.base_transport import _BaseMailbox
from bitfount.federated.transport.config import MessageServiceConfig
from bitfount.federated.transport.message_service import (
    ResourceConsumed,
    ResourceType,
    _MessageService,
)
from bitfount.federated.transport.modeller_transport import _ModellerMailbox
from bitfount.federated.transport.types import Reason
from bitfount.federated.transport.utils import compute_backoff
from bitfount.federated.transport.worker_transport import _WorkerMailbox
from bitfount.federated.types import ProtocolType, SerializedProtocol
from bitfount.hooks import (
    _HOOK_DECORATED_ATTRIBUTE,
    BaseDecoratorMetaClass,
    HookType,
    get_hooks,
)
from bitfount.hub.helper import _default_bitfounthub
from bitfount.schemas.utils import bf_dump
from bitfount.types import (
    T_FIELDS_DICT,
    T_NESTED_FIELDS,
    _BaseSerializableObjectMixIn,
    _StrAnyDict,
)

if TYPE_CHECKING:
    from bitfount.federated.pod_vitals import _PodVitals
    from bitfount.hub.api import BitfountHub
    from bitfount.hub.authentication_flow import BitfountSession


logger = _get_federated_logger(__name__)

MAXIMUM_SLEEP_TIME: Final = 10
MAXIMUM_RETRIES: Final = 60


class ProtocolDecoratorMetaClass(BaseDecoratorMetaClass, type):
    """Decorates the `__init__` and `run` protocol methods."""

    @staticmethod
    def decorator(f: Callable) -> Callable:
        """Hook decorator which logs before and after the hook it decorates."""
        method_name = f.__name__
        if method_name == "__init__":

            @wraps(f)
            def init_wrapper(
                self: _BaseProtocol,
                hook_kwargs: Optional[_StrAnyDict] = None,
                *args: Any,
                **kwargs: Any,
            ) -> None:
                """Wraps __init__ method of protocol.

                Calls relevant hooks before and after the protocol is initialised.

                Args:
                    self: The protocol instance.
                    hook_kwargs: Keyword arguments to pass to the hooks.
                    *args: Positional arguments to pass to the protocol.
                    **kwargs: Keyword arguments to pass to the protocol.
                """
                hook_kwargs = hook_kwargs or {}
                for hook in get_hooks(HookType.PROTOCOL):
                    hook.on_init_start(self, **hook_kwargs)
                logger.debug(f"Calling method {method_name} from protocol")
                f(self, *args, **kwargs)
                for hook in get_hooks(HookType.PROTOCOL):
                    hook.on_init_end(self, **hook_kwargs)

            return init_wrapper

        elif method_name == "run":

            @wraps(f)
            async def run_wrapper(
                self: _BaseProtocol,
                *,
                context: Optional[ProtocolContext] = None,
                batched_execution: Optional[bool] = None,
                hook_kwargs: Optional[_StrAnyDict] = None,
                processed_files_cache: Optional[dict[str, datetime]] = None,
                test_run: bool = False,
                **kwargs: Any,
            ) -> Union[Any, list[Any]]:
                """Wraps run method of protocol.

                Calls hooks before and after the run method is called and also
                orchestrates batched execution if set to True.

                Args:
                   self: Protocol instance.
                   context: Context in which the protocol is being run. Only required
                       if batched_execution is True.
                   batched_execution: Whether to run the protocol in batched mode.
                   hook_kwargs: Keyword arguments to pass to the hooks.
                   processed_files_cache: Optional. A dictionary of processed file
                        names to their last modified dates. Defaults to None.
                   test_run: Whether this is a test run. Defaults to False.
                   **kwargs: Keyword arguments to pass to the run method.

                Returns:
                   Return value of the run method. Or a list of return values if
                   batched_execution is True.

                Raises:
                   BitfountTaskStartError: If batched_execution is True but the
                       datasource does not support batched execution.
                   AlgorithmError: This is caught and re-raised.
                   ProtocolError: Any error that is raised in the protocol run that
                       is not an AlgorithmError is raised as a ProtocolError.
                """
                executor = ProtocolExecution(
                    protocol=self,
                    run_method=f,
                    context=context,
                    batched_execution=batched_execution,
                    processed_files_cache=processed_files_cache,
                    test_run=test_run,
                    hook_kwargs=hook_kwargs,
                    **kwargs,
                )
                return await executor.execute()

            return run_wrapper

        raise ValueError(f"Method {method_name} cannot be decorated.")

    @classmethod
    def do_decorate(cls, attr: str, value: Any) -> bool:
        """Checks if an object should be decorated.

        Only the __init__ and run methods should be decorated.
        """
        return (
            attr in ("__init__", "run")
            and isinstance(value, FunctionType)
            and getattr(value, _HOOK_DECORATED_ATTRIBUTE, True)
        )


MB = TypeVar("MB", bound=_BaseMailbox)

# The metaclass for the BaseProtocol must also have all the same classes in its own
# inheritance chain so we need to create a thin wrapper around it.
AbstractProtocolDecoratorMetaClass = types.new_class(
    "AbstractProtocolDecoratorMetaClass",
    (Generic[MB], ABCMeta, ProtocolDecoratorMetaClass),
    {},
)


class BatchConfig:
    """Holds batch configuration and state.

    Args:
        batch_size: The size of each batch.
        data_splitter: The dataset splitter to use for splitting the data.
        datasource: The datasource from which to read the data.
        original_file_names_override: Optional. Override for the original file names
            used in the datasource. Used for restoring `selected_file_names_override`
             on the datasource the at the end of the task.
        is_final_batch: Whether this is the final batch. Defaults to False.

    Attributes:
        batch_size: The size of each batch.
        data_splitter: The dataset splitter to use for splitting the data.
        datasource: The datasource from which to read the data.
        original_file_names_override: Optional. Override for the original file names
            used in the datasource. Used for restoring `selected_file_names_override`
            on the datasource at the end of the task.
        current_batch: The current batch number.
        current_files_iterator: An iterator over the filenames for the current batch.
        is_final_batch: Whether this is the final batch.
        current_batch_files: The list of files in the current batch.
    """

    def __init__(
        self,
        batch_size: int,
        data_splitter: DatasetSplitter,
        datasource: FileSystemIterableSource,
        original_file_names_override: Optional[list[str]],
        is_final_batch: bool = False,
    ):
        self.batch_size = batch_size
        self.data_splitter = data_splitter
        self.datasource = datasource
        self.original_file_names_override = original_file_names_override
        self.current_batch = 0
        self.current_files_iterator = more_itertools.peekable(
            self.data_splitter.iter_filenames(
                datasource=datasource, split=DataSplit.TEST
            )
        )
        self.is_final_batch = is_final_batch
        self.current_batch_files: list[str] = []
        # Track if any new files have been found
        # (for tasks with run_on_new_data_only set to True)
        self.has_new_files = False
        self.total_files_checked = 0


class ProtocolExecution:
    """Handles protocol execution with proper context management.

    Args:
        protocol: The protocol instance to run.
        run_method: The method to execute on the protocol.
        context: Optional. The context in which the protocol is being run.
        batched_execution: Whether to run the protocol in batched mode.
        hook_kwargs: Optional. Keyword arguments to pass to the hooks.
        processed_files_cache: Optional. A dictionary of processed files
            with their last modified dates. Defaults to None.
        test_run: Whether this is a test run. Defaults to False.
        **kwargs: Additional keyword arguments for the run method.
    """

    def __init__(
        self,
        protocol: _BaseProtocol,
        run_method: Callable,
        context: Optional[ProtocolContext],
        batched_execution: Optional[bool],
        hook_kwargs: Optional[_StrAnyDict],
        processed_files_cache: Optional[dict[str, datetime]] = None,
        test_run: bool = False,
        **kwargs: Any,
    ):
        self.protocol = protocol
        self.run_method = run_method
        self.context = context
        self.task_context = context.task_context if context else None
        self.batched_execution = (
            config.settings.default_batched_execution
            if batched_execution is None
            else batched_execution
        )
        self.processed_files_cache = processed_files_cache
        self.test_run = test_run

        # Check for context when batched execution is enabled
        if self.batched_execution and not context:
            raise BitfountTaskStartError(
                "Context must be provided for batched execution."
            )

        self.hook_kwargs = hook_kwargs or {}
        self.hook_kwargs["context"] = self.task_context
        self.kwargs = kwargs

    async def execute(self) -> Union[Any, list[Any]]:
        """Main execution entry point."""
        try:
            if self.task_context == TaskContext.WORKER:
                return await self._execute_worker()
            elif self.task_context == TaskContext.MODELLER:
                return await self._execute_modeller()
            else:
                return await self._run_single()
        except BitfountTaskStartError:
            raise
        except Exception as e:
            logger.exception(e)
            raise

    async def _execute_worker(self) -> Union[Any, list[Any]]:
        """Handles worker-side execution."""
        protocol = cast(BaseWorkerProtocol, self.protocol)
        datasource = self._validate_worker_datasource(protocol)
        batch_config: Optional[BatchConfig] = None
        try:
            if not isinstance(datasource, FileSystemIterableSource):
                logger.warning(
                    "Batched execution not compatible with non-iterable sources. "
                    "Running in non-batched mode."
                )
                self.batched_execution = False
            if not self.batched_execution:
                if self.test_run:
                    self.test_run = False
                    logger.warning("Test run is not supported in non-batched mode.")
                # Inform modeller we're running in non-batched mode
                await protocol.mailbox.send_num_batches_message(1)
                return await self._run_single()

            batch_config = self._setup_worker_batches(
                protocol=protocol, datasource=datasource
            )

            # Signal batches coming in by streaming by sending -1 as num_batches
            await protocol.mailbox.send_num_batches_message(-1)
            return await self._run_worker_batches(protocol, batch_config)
        finally:
            self._restore_worker_datasource(
                datasource=datasource, batch_config=batch_config
            )

    async def _execute_modeller(self) -> Union[Any, list[Any]]:
        """Handles modeller-side execution."""
        mailbox = cast(_ModellerMailbox, self.protocol.mailbox)
        # Always wait for batch information from worker
        num_batches = await mailbox.get_num_batches_message()
        logger.debug(f"Modeller received num_batches: {num_batches}")
        if not self.batched_execution or num_batches == 1:
            logger.debug("Modeller: Running in non-batched mode")
            result = await self._run_single()
        elif num_batches == -1:
            logger.debug("Modeller: Running in streaming mode")
            # In streaming mode, we don't know the number of batches upfront.
            # We will run batches until the worker signals completion.
            result = await self._run_modeller_streaming_batches()
        else:
            logger.error(
                "Modeller and worker are incompatible. "
                "Please ensure that they are both running the same bitfount version."
            )
            raise BitfountTaskStartError(
                "Modeller and worker are incompatible. "
                "Please ensure that they are both running the same bitfount version."
            )
        return result

    def _load_new_data_for_single_batch(self) -> None:
        """Loads new data only for a single batch run."""

        if self.processed_files_cache is not None:
            run_records_filenames = list(self.processed_files_cache)
            if (
                not hasattr(self.protocol, "datasource")
                or not self.protocol.datasource
                or not hasattr(self.protocol, "data_splitter")
            ):
                raise BitfountTaskStartError(
                    "Protocol has not been initialised with a datasource."
                )

            if isinstance(self.protocol.data_splitter, SplitterDefinedInData):
                datasource_file_names = self.protocol.data_splitter.get_filenames(
                    self.protocol.datasource, split=DataSplit.TEST
                )
            else:
                datasource_file_names = self.protocol.datasource.file_names
            new_records = [
                # [non_iterable_file_names]
                i
                for i in datasource_file_names
                if i not in run_records_filenames
            ]
            for run_record in run_records_filenames:
                # Check if the file is still present in the datasource
                # [non_iterable_file_names]
                if run_record in datasource_file_names:
                    original_last_modified = self.processed_files_cache[run_record]
                    new_last_modified = datetime.fromtimestamp(
                        os.path.getmtime(run_record)
                    )
                    # Check if the file has been modified since the last run
                    if new_last_modified > original_last_modified:
                        logger.debug(
                            f"File {run_record} has been modified since last run. "
                            f"Adding to new records."
                        )
                        new_records.append(run_record)
            new_records_set = set(new_records)
            if len(new_records) == 0:
                msg = "No new data available. Aborting task."
                logger.info(msg)
                raise NoNewDataError(msg)
            if len(new_records_set) != len(new_records):
                logger.warning(
                    "There are duplicate filenames in the new records. "
                    "These have been removed but this may indicate an issue."
                )

            logger.info(
                f"Found {len(new_records_set)} new record(s) to run the task on."
            )

            # We explicitly only set the file names that are new, ignoring any other
            # data in new_records
            self.protocol.datasource.new_file_names_only_set = new_records_set

    async def _run_single(self) -> Any:
        """Executes a single non-batched run."""
        await self._ensure_parties_ready()
        if self.task_context == TaskContext.WORKER:
            self._load_new_data_for_single_batch()
        for hook in get_hooks(HookType.PROTOCOL):
            hook.on_run_start(self.protocol, **self.hook_kwargs)

        try:
            return_val = await self._execute_run(final_batch=True)
            self.hook_kwargs["results"] = return_val

            for hook in get_hooks(HookType.PROTOCOL):
                hook.on_run_end(self.protocol, **self.hook_kwargs)

            return return_val
        except (AlgorithmError, TaskAbortError):
            raise
        except Exception as e:
            raise ProtocolError(
                f"Protocol {self.protocol.__class__.__name__} "
                f"raised the following exception: {e}"
            ) from e

    def _validate_worker_datasource(self, protocol: BaseWorkerProtocol) -> BaseSource:
        """Validates and returns the worker datasource.

        Args:
            protocol: The worker protocol instance.

        Raises:
            BitfountTaskStartError: If the protocol has not been initialised with a
                datasource or if the datasource is not a FileSystemIterableSource.

        Returns:
           The datasource to use for the worker.
        """
        try:
            datasource = protocol.datasource
        except Exception as e:
            raise BitfountTaskStartError(
                "Protocol has not been initialised with a datasource."
            ) from e
        return datasource

    def _get_data_splitter(self, protocol: BaseWorkerProtocol) -> DatasetSplitter:
        """Gets the data splitter, using default if none set.

        Args:
            protocol: The worker protocol instance.

        Returns:
            The data splitter to use for the protocol.
        """
        try:
            data_splitter = (
                protocol.data_splitter
                if protocol.data_splitter is not None
                else PercentageSplitter(iterative_splitting=True)
            )
        except Exception:
            logger.warning(
                "Protocol has not been initialised with "
                "a data splitter. Using default PercentageSplitter."
            )
            data_splitter = PercentageSplitter(iterative_splitting=True)
        return data_splitter

    def _setup_worker_batches(
        self,
        datasource: BaseSource,
        protocol: BaseWorkerProtocol,
    ) -> BatchConfig:
        """Sets up batch configuration for worker execution.

        Args:
            datasource: The worker datasource to use.
            protocol: The worker protocol instance.

        Returns:
            The batch configuration for the worker.
        """
        if not isinstance(datasource, FileSystemIterableSource):
            raise BitfountTaskStartError(
                "Batched execution is not supported for non-filesystem "
                "iterable sources."
            )

        # Get the data splitter, don't retrieve all files upfront
        data_splitter = self._get_data_splitter(protocol)
        if self.test_run:
            batch_size = config.settings.test_run_number_of_files
        else:
            batch_size = config.settings.task_batch_size

        return BatchConfig(
            batch_size=batch_size,
            data_splitter=data_splitter,
            datasource=datasource,
            original_file_names_override=datasource.selected_file_names_override.copy(),
        )

    def _prepare_worker_batch(
        self,
        batch_config: BatchConfig,
        protocol: BaseWorkerProtocol,
    ) -> bool:
        """Prepares the worker datasource for the current batch.

        Args:
            batch_config: The batch configuration for the worker.
            protocol: The worker protocol instance.

        Returns:
            True if the batch was prepared successfully, False if no more batches
        """
        # If this was already marked as the final batch, don't try to prepare more
        if batch_config.is_final_batch:
            return False

        # Collect files for this batch using the iterator
        current_batch_files: list[str] = []
        try:
            while len(current_batch_files) < batch_config.batch_size:
                filename = next(batch_config.current_files_iterator)
                batch_config.total_files_checked += 1

                # Filter for new data if cache is not None
                if self.processed_files_cache is not None:
                    if self._is_file_new_from_cache(filename):
                        batch_config.has_new_files = (
                            True  # Mark that we found new files
                        )
                        current_batch_files.append(filename)
                    # If not new, skip this file (don't add to current_batch_files)
                else:
                    current_batch_files.append(filename)
        except StopIteration:
            if not current_batch_files:
                # This can happen if there are no files in the test set
                return False
            else:
                # This is the final batch with fewer files than batch_size
                batch_config.is_final_batch = True

        # If we collected a full batch, check if there are more files
        if (
            len(current_batch_files) == batch_config.batch_size
            and not batch_config.is_final_batch
        ):
            try:
                batch_config.current_files_iterator.peek()
            except StopIteration:
                batch_config.is_final_batch = True

        # Store the current batch files
        batch_config.current_batch_files = current_batch_files

        # Update datasource with current batch of files
        datasource = cast(FileSystemIterableSource, protocol.datasource)
        datasource.selected_file_names_override = current_batch_files

        # Reinitialize algorithms with updated datasource
        data_splitter = self._get_data_splitter(protocol)
        for algo in protocol.algorithms:
            algo = cast(BaseCompatibleWorkerAlgorithm, algo)
            algo.initialise_data(datasource=datasource, data_splitter=data_splitter)

        # Increment the batch counter
        batch_config.current_batch += 1

        return True

    def _restore_worker_datasource(
        self,
        datasource: BaseSource,
        batch_config: Optional[BatchConfig] = None,
    ) -> None:
        """Restores the worker datasource to its original state.

        Args:
            datasource: The worker datasource to restore.
            batch_config: Optional. The batch configuration used for the run.
        """
        if (
            isinstance(datasource, FileSystemIterableSource)
            and batch_config is not None
        ):
            datasource.selected_file_names_override = (
                batch_config.original_file_names_override or []
            )

    async def _run_worker_batches(
        self, protocol: BaseWorkerProtocol, batch_config: BatchConfig
    ) -> list[Any]:
        """Executes all batches for worker context.

        Args:
            protocol: The worker protocol instance.
            batch_config: The batch configuration for the worker.
        """
        return_values = []
        is_last_batch = False

        # Check if we have any new files when run_on_new_data_only is enabled
        if self.processed_files_cache is not None:
            batch_config.has_new_files = False  # Track if any new files are found
        # Process batches in streaming mode until there are no more batches
        while not is_last_batch:
            batch_prepared = self._prepare_worker_batch(
                batch_config=batch_config,
                protocol=protocol,
            )

            if not batch_prepared:
                break

            # If run_on_new_data_only is enabled and no new files found, abort
            if (
                self.processed_files_cache is not None
                and not batch_config.has_new_files
                and batch_config.total_files_checked > 0
            ):
                logger.info("No new data found after checking files. Aborting task.")
                await protocol.mailbox.send_task_abort_message(
                    "No new data available. Aborting task.", Reason.NO_NEW_DATA
                )
                break

            # Get current batch number
            batch_num = (
                batch_config.current_batch - 1
            )  # -1 because we already incremented

            # Send the current batch ID to the modeller
            await protocol.mailbox.send_current_batch_id_message(batch_num)
            if self.test_run:
                is_last_batch = True  # In test run, we only run one batch
            else:
                # Check if this is the final batch
                is_last_batch = batch_config.is_final_batch

            # Run the batch
            return_val = await self._run_batch(
                batch_num=batch_num, is_final=is_last_batch
            )

            return_values.append(return_val)

        # Signal to the modeller that all batches are complete
        await protocol.mailbox.send_batches_complete_message()

        return return_values

    async def _run_modeller_streaming_batches(self) -> list[Any]:
        """Executes modeller-side batches in streaming mode."""
        return_values = []
        mailbox = cast(_ModellerMailbox, self.protocol.mailbox)

        # Process batches until we receive BATCHES_COMPLETE
        while not mailbox.batches_complete_received:
            try:
                # Get the current batch ID from the worker
                batch_num = await mailbox.get_current_batch_id_message()

                # Check if worker signaled completion with -1
                if batch_num == -1:
                    logger.debug("Worker signaled completion with batch_num = -1")
                    break
                # We retry 3 times in the modeller transport to ensure we have
                # a valid batch number, if here it is still None, we raise an error.
                if batch_num is None:
                    raise ValueError("No current batch ID messages received.")
                logger.debug(f"Processing batch {batch_num} in streaming mode")

                # Run the batch
                return_val = await self._run_batch(batch_num=batch_num, is_final=False)

                # Store the result
                return_values.append(return_val)
            except Exception as e:
                logger.error(f"Error processing streaming batch: {e}")
                raise

        logger.debug(
            f"Completed streaming batches. Processed {len(return_values)} batches."
        )
        return return_values

    async def _ensure_parties_ready(self) -> None:
        """Ensures all parties are ready before proceeding."""
        retry_count = 0
        await self.protocol.mailbox.send_task_start_message()

        if self.task_context == TaskContext.WORKER:
            mailbox = cast(_WorkerMailbox, self.protocol.mailbox)
            while not mailbox.modeller_ready:
                retry_count += 1
                if retry_count >= MAXIMUM_RETRIES:
                    raise BitfountTaskStartError(
                        "Timed out while waiting for modeller to be ready"
                    )
                await asyncio.sleep(
                    compute_backoff(retry_count, max_backoff=MAXIMUM_SLEEP_TIME)
                )
                logger.info("Waiting for modeller to be ready...")
            logger.info("Modeller is ready. Starting task...")

        elif self.task_context == TaskContext.MODELLER:
            modeller_mailbox = cast(_ModellerMailbox, self.protocol.mailbox)
            while not modeller_mailbox.pods_ready and modeller_mailbox.abort is None:
                retry_count += 1
                await asyncio.sleep(
                    compute_backoff(retry_count, max_backoff=MAXIMUM_SLEEP_TIME)
                )
                logger.info("Waiting for pod(s) to be ready...")
            if modeller_mailbox.abort is not None:
                error_message, reason = modeller_mailbox.abort
                logger.error(error_message)
                raise TaskAbortError(error_message, reason)
            logger.info("Pod(s) are ready. Starting task...")

    async def _run_batch(
        self,
        batch_num: int,
        is_final: bool = False,
    ) -> Any:
        """Executes a single batch with proper hook handling."""
        logger.info(f"Running batch {batch_num + 1}...")

        hook_kwargs = self.hook_kwargs.copy()
        hook_kwargs.update({"batch_num": batch_num})

        for hook in get_hooks(HookType.PROTOCOL):
            hook.on_run_start(self.protocol, **hook_kwargs)

        if batch_num == 0:
            await self._ensure_parties_ready()

        return_val = await self._execute_run(batch_num=batch_num, final_batch=is_final)
        hook_kwargs["results"] = return_val
        for hook in get_hooks(HookType.PROTOCOL):
            hook.on_run_end(self.protocol, **hook_kwargs)

        return return_val

    async def _execute_run(
        self, batch_num: Optional[int] = None, final_batch: bool = False
    ) -> Any:
        """Executes the actual run method with error handling."""
        try:
            return await self.run_method(
                self.protocol,
                context=self.context,
                batch_num=batch_num,
                final_batch=final_batch,
                **self.kwargs,
            )
        except (AlgorithmError, TaskAbortError):
            raise
        except Exception as e:
            raise ProtocolError(
                f"Protocol {self.protocol.__class__.__name__} "
                f"raised the following exception: {e}"
            ) from e

    def _is_file_new_from_cache(
        self,
        filename: str,
    ) -> bool:
        """Check if a file is new using the cached processed files info.

        Args:
            filename: The filename to check

        Returns:
            True if the file is new or has been modified, False otherwise
        """
        if self.processed_files_cache is not None:
            if filename not in self.processed_files_cache:
                # File hasn't been processed before
                return True

            try:
                # Check if file has been modified since last processing
                stored_last_modified = self.processed_files_cache[filename]
                current_last_modified = datetime.fromtimestamp(
                    os.path.getmtime(filename)
                )

                if current_last_modified > stored_last_modified:
                    logger.debug(
                        f"File {filename} has been modified since last run. "
                        f"Including in batch."
                    )
                    return True

                return False

            except Exception:
                # If there's any error checking file modification time,
                # include the file to be safe
                logger.warning(
                    f"Error checking modification time for {filename}. Treating as new."
                )
                return True
        else:
            # We should not end up in this branch if the protocol is set up correctly,
            # but **if** we do, log error and treat all files as new.
            logger.error(
                "No processed files cache provided. Treating all files as new."
            )
            return True


# Mypy doesn't yet support metaclasses with generics
class _BaseProtocol(Generic[MB], ABC, metaclass=AbstractProtocolDecoratorMetaClass):  # type: ignore[misc] # Reason: see above # noqa: E501
    """Blueprint for modeller side or the worker side of BaseProtocolFactory."""

    def __init__(
        self,
        *,
        algorithm: Union[
            BaseCompatibleModellerAlgorithm,
            Sequence[BaseCompatibleModellerAlgorithm],
            BaseCompatibleWorkerAlgorithm,
            Sequence[BaseCompatibleWorkerAlgorithm],
        ],
        mailbox: MB,
        **kwargs: Any,
    ):
        self.algorithm = algorithm
        self.mailbox = mailbox
        self.class_name = module_registry.get(self.__class__.__module__, "")

        super().__init__(**kwargs)

    @property
    def algorithms(
        self,
    ) -> list[Union[BaseCompatibleModellerAlgorithm, BaseCompatibleWorkerAlgorithm]]:
        """Returns the algorithms in the protocol."""
        if isinstance(self.algorithm, Sequence):
            return list(self.algorithm)
        return [self.algorithm]


class BaseCompatibleModellerAlgorithm(Protocol):
    """Protocol defining base modeller-side algorithm compatibility."""

    def initialise(
        self,
        task_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialises the algorithm."""
        pass


class BaseModellerProtocol(_BaseProtocol[_ModellerMailbox], ABC):
    """Modeller side of the protocol.

    Calls the modeller side of the algorithm.
    """

    def __init__(
        self,
        *,
        algorithm: Union[
            BaseCompatibleModellerAlgorithm, Sequence[BaseCompatibleModellerAlgorithm]
        ],
        mailbox: _ModellerMailbox,
        **kwargs: Any,
    ):
        super().__init__(algorithm=algorithm, mailbox=mailbox, **kwargs)

    def initialise(
        self,
        task_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialises the component algorithms."""
        for algo in self.algorithms:
            algo.initialise(
                task_id=task_id,
                **kwargs,
            )

    @abstractmethod
    async def run(
        self, *, context: Optional[ProtocolContext] = None, **kwargs: Any
    ) -> Any:
        """Runs Modeller side of the protocol.

        Args:
            context: Optional. Run-time context for the protocol.
            **kwargs: Additional keyword arguments.
        """
        pass


class BaseCompatibleWorkerAlgorithm(Protocol):
    """Protocol defining base worker-side algorithm compatibility."""

    def initialise(
        self,
        datasource: BaseSource,
        data_splitter: Optional[DatasetSplitter] = None,
        pod_dp: Optional[DPPodConfig] = None,
        pod_identifier: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialises the algorithm."""
        pass

    def initialise_data(
        self,
        datasource: BaseSource,
        data_splitter: Optional[DatasetSplitter] = None,
    ) -> None:
        """Initialises the data for the algorithm."""
        pass


class BaseWorkerProtocol(_BaseProtocol[_WorkerMailbox], ABC):
    """Worker side of the protocol.

    Calls the worker side of the algorithm.
    """

    datasource: BaseSource
    mailbox: _WorkerMailbox
    project_id: Optional[str]

    def __init__(
        self,
        *,
        algorithm: Union[
            BaseCompatibleWorkerAlgorithm, Sequence[BaseCompatibleWorkerAlgorithm]
        ],
        mailbox: _WorkerMailbox,
        **kwargs: Any,
    ):
        super().__init__(algorithm=algorithm, mailbox=mailbox, **kwargs)

    def initialise(
        self,
        datasource: BaseSource,
        data_splitter: Optional[DatasetSplitter] = None,
        pod_dp: Optional[DPPodConfig] = None,
        pod_identifier: Optional[str] = None,
        project_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialises the component algorithms."""
        self.datasource = datasource
        self.data_splitter = data_splitter
        self.project_id = project_id
        for algo in self.algorithms:
            algo.initialise(
                datasource=datasource,
                data_splitter=data_splitter,
                pod_dp=pod_dp,
                pod_identifier=pod_identifier,
                task_id=self.mailbox.task_id,
                **kwargs,
            )

    @abstractmethod
    async def run(
        self,
        *,
        pod_vitals: Optional[_PodVitals] = None,
        context: Optional[ProtocolContext] = None,
        **kwargs: Any,
    ) -> Any:
        """Runs the worker-side of the algorithm.

        Args:
            pod_vitals: Optional. Pod vitals instance for recording run-time details
                from the protocol run.
            context: Optional. Run-time context for the protocol.
            **kwargs: Additional keyword arguments.
        """
        pass


# The mutable underlying dict that holds the registry information
_registry: dict[str, type[BaseProtocolFactory]] = {}
# The read-only version of the registry that is allowed to be imported
registry: Mapping[str, type[BaseProtocolFactory]] = MappingProxyType(_registry)

# The mutable underlying dict that holds the mapping of module name to class name
_module_registry: dict[str, str] = {}
# The read-only version of the module registry that is allowed to be imported
module_registry: Mapping[str, str] = MappingProxyType(_module_registry)


class BaseCompatibleAlgoFactory(Protocol):
    """Protocol defining base algorithm factory compatibility."""

    class_name: str
    _inference_algorithm: bool = True
    fields_dict: ClassVar[T_FIELDS_DICT] = {}
    nested_fields: ClassVar[T_NESTED_FIELDS] = {}


class BaseProtocolFactory(ABC, _RolesMixIn, _BaseSerializableObjectMixIn):
    """Base Protocol from which all other protocols must inherit."""

    fields_dict: ClassVar[T_FIELDS_DICT] = {}
    nested_fields: ClassVar[T_NESTED_FIELDS] = {"algorithm": algorithms.registry}

    def __init__(
        self,
        *,
        algorithm: Union[
            BaseCompatibleAlgoFactory, Sequence[BaseCompatibleAlgoFactory]
        ],
        **kwargs: Any,
    ) -> None:
        try:
            self.class_name = ProtocolType[type(self).__name__].value
        except KeyError:
            # Check if the protocol is a plug-in
            self.class_name = type(self).__name__

        super().__init__(**kwargs)
        self.algorithm = algorithm
        for algo in self.algorithms:
            self._validate_algorithm(algo)

    @classmethod
    def __init_subclass__(cls, **kwargs: Any):
        if not inspect.isabstract(cls):
            logger.debug(f"Adding {cls.__name__}: {cls} to Protocol registry")
            _registry[cls.__name__] = cls
            _module_registry[cls.__module__] = cls.__name__

    @property
    def algorithms(self) -> list[BaseCompatibleAlgoFactory]:
        """Returns the algorithms in the protocol."""
        if isinstance(self.algorithm, Sequence):
            return list(self.algorithm)
        return [self.algorithm]

    @classmethod
    @abstractmethod
    def _validate_algorithm(cls, algorithm: BaseCompatibleAlgoFactory) -> None:
        """Checks that `algorithm` is compatible with the protocol.

        Raises TypeError if `algorithm` is not compatible with the protocol.
        """
        pass

    @abstractmethod
    def modeller(
        self, mailbox: _ModellerMailbox, **kwargs: Any
    ) -> BaseModellerProtocol:
        """Creates an instance of the modeller-side for this protocol."""
        raise NotImplementedError

    @abstractmethod
    def worker(
        self,
        mailbox: _WorkerMailbox,
        hub: BitfountHub,
        context: Optional[ProtocolContext] = None,
        **kwargs: Any,
    ) -> BaseWorkerProtocol:
        """Creates an instance of the worker-side for this protocol."""
        raise NotImplementedError

    def dump(self) -> SerializedProtocol:
        """Returns the JSON-serializable representation of the protocol."""
        return cast(SerializedProtocol, bf_dump(self))

    def run(
        self,
        pod_identifiers: Collection[str],
        session: Optional[BitfountSession] = None,
        username: Optional[str] = None,
        hub: Optional[BitfountHub] = None,
        ms_config: Optional[MessageServiceConfig] = None,
        message_service: Optional[_MessageService] = None,
        pod_public_key_paths: Optional[Mapping[str, Path]] = None,
        identity_verification_method: IdentityVerificationMethod = IdentityVerificationMethod.DEFAULT,  # noqa: E501
        private_key_or_file: Optional[Union[RSAPrivateKey, Path]] = None,
        idp_url: Optional[str] = None,
        require_all_pods: bool = False,
        run_on_new_data_only: bool = False,
        model_out: Optional[Union[Path, str]] = None,
        project_id: Optional[str] = None,
        batched_execution: Optional[bool] = None,
    ) -> Optional[Any]:
        """Sets up a local Modeller instance and runs the protocol.

        Args:
            pod_identifiers: The BitfountHub pod identifiers to run against.
            session: Optional. Session to use for authenticated requests.
                 Created if needed.
            username: Username to run as. Defaults to logged in user.
            hub: BitfountHub instance. Default: hub.bitfount.com.
            ms_config: Message service config. Default: messaging.bitfount.com.
            message_service: Message service instance, created from ms_config if not
                provided. Defaults to "messaging.bitfount.com".
            pod_public_key_paths: Public keys of pods to be checked against.
            identity_verification_method: The identity verification method to use.
            private_key_or_file: Private key (to be removed).
            idp_url: The IDP URL.
            require_all_pods: If true raise PodResponseError if at least one pod
                identifier specified rejects or fails to respond to a task request.
            run_on_new_data_only: Whether to run the task on new datapoints only.
                Defaults to False.
            model_out: The path to save the model to.
            project_id: The project ID to run the task under.
            batched_execution: Whether to run the task in batched mode. Defaults to
                False.

        Returns:
            Results of the protocol.

        Raises:
            PodResponseError: If require_all_pods is true and at least one pod
                identifier specified rejects or fails to respond to a task request.
            ValueError: If attempting to train on multiple pods, and the
                `DataStructure` table name is given as a string.
        """
        hub = _default_bitfounthub(hub=hub, username=username)
        if batched_execution is None:
            batched_execution = config.settings.default_batched_execution
        if len(pod_identifiers) > 1 and batched_execution:
            logger.warning(
                "Batched execution is only supported for single pod tasks. "
                "Resuming task without batched execution."
            )
            batched_execution = False

        for algo in self.algorithms:
            if (
                isinstance(algo, _BaseModelAlgorithmFactory)
                and algo.model.datastructure is not None
            ):
                if (
                    len(pod_identifiers) > 1
                    and hasattr(algo.model.datastructure, "table")
                    and isinstance(algo.model.datastructure.table, str)
                ):
                    raise ValueError(
                        "You are attempting to train on multiple pods, and the "
                        "provided the DataStructure table name is a string. "
                        "Please make sure that the `table` argument to the "
                        "`DataStructure` is a mapping of Pod names to table names. "
                    )
                pod_identifiers = _check_and_update_pod_ids(pod_identifiers, hub)

        if not session:
            session = hub.session
        if not idp_url:
            idp_url = _get_idp_url()
        if not message_service:
            message_service = _create_message_service(
                session=session,
                ms_config=ms_config,
            )

        modeller = _Modeller(
            protocol=self,
            message_service=message_service,
            bitfounthub=hub,
            pod_public_key_paths=pod_public_key_paths,
            identity_verification_method=identity_verification_method,
            private_key=private_key_or_file,
            idp_url=idp_url,
        )

        name = type(self).__name__

        logger.info(f"Starting {name} Task...")

        result = modeller.run(
            pod_identifiers,
            require_all_pods=require_all_pods,
            project_id=project_id,
            model_out=model_out,
            run_on_new_data_only=run_on_new_data_only,
            batched_execution=batched_execution,
        )
        logger.info(f"Completed {name} Task.")
        return result


LimitsExceededInfo = NamedTuple(
    "LimitsExceededInfo", [("overrun", int), ("allowed", int)]
)


class ModelInferenceProtocolMixin:
    """Mixin class for protocols that may contain one or more model inference steps.

    These protocols will have to respect any model inference usage limits that are
    associated with the model(s) in use.
    """

    @staticmethod
    def check_usage_limits(
        limits: dict[str, InferenceLimits],
        inference_algorithm: ModelInferenceWorkerSideAlgorithm,
    ) -> Optional[LimitsExceededInfo]:
        """Check if the most recent inference run has exceeded the usage limits.

        Updates the total usage count associated with model in question, regardless
        of if the limits are exceeded or not.

        Args:
            limits: The inference usage limits as a mapping of model_id to usage
                limits.
            inference_algorithm: The inference algorithm instance that has just been
                run.

        Returns:
            If limits were not exceeded, returns None. Otherwise, returns a container
            with `.overrun` and `.allowed` attributes which indicate the number of
            predictions usage was exceeded by and the number of predictions actually
            allowed to be used respectively.
            e.g. for an initial total_usage of 10, a limit of 20, and an inference
            run that used 14 more inferences, will return `(4, 10)`. If limits are
            not exceeded, will return `None`.
        """
        # Extract model associated with inference algorithm, failing fast if no
        # model_id is found.
        model_id: Optional[str] = inference_algorithm.maybe_bitfount_model_slug
        if model_id is None:
            logger.debug(
                f"Inference algorithm {inference_algorithm} has no associated model ID."
            )
            return None

        # Find the usage limits associated with the model in question, failing fast
        # if no usage limits are found for that model.
        model_limits: InferenceLimits
        try:
            model_limits = limits[model_id]
        except KeyError:
            logger.debug(f"No limits specified for model {model_id}")
            return None

        # Calculate the new usages associated with the model in question and update
        # the total_usage counts in the limits.
        resources_consumed_for_model: list[ResourceConsumed] = [
            rc
            for rc in inference_algorithm.get_resources_consumed()
            if rc.resource_identifier == model_id
            and rc.resource_type == ResourceType.MODEL_INFERENCE
        ]

        if len(resources_consumed_for_model) > 1:
            raise ValueError(
                f"Multiple model inference resources consumed found for {model_id};"
                f" only one is supported."
            )

        new_usage: int = int(sum(rc.amount for rc in resources_consumed_for_model))
        model_limits.total_usage = model_limits.total_usage + new_usage

        # Check if we have exceeded the usage limits and return this information.
        if model_limits.total_usage >= model_limits.limit:
            if model_limits.total_usage > model_limits.limit:
                logger.warning(
                    f"Model usage limits exceeded for model {model_id};"
                    f" usage limit is {model_limits.limit},"
                    f" have performed {model_limits.total_usage} inferences."
                )
            else:  # model_limits.total_usage == model_limits.limits
                logger.warning(
                    f"Model usage limits reached for model {model_id};"
                    f" usage limit is {model_limits.limit},"
                    f" have performed {model_limits.total_usage} inferences."
                )
            overrun: int = model_limits.total_usage - model_limits.limit
            allowed: int = new_usage - overrun
            return LimitsExceededInfo(overrun, allowed)
        else:
            return None

    @staticmethod
    def apply_actual_usage_to_resources_consumed(
        inference_algorithm: ModelInferenceWorkerSideAlgorithm,
        limits_exceeded_info: LimitsExceededInfo | None,
    ) -> list[ResourceConsumed]:
        """Generate a resources consumed list from an algorithm that respects limits.

        Given information on the actual number of inferences that were allowed/used,
        updates resources consumed entries from the given algorithm to reflect this
        limit.

        If limits were not exceeded, just returns the resources consumed information
        unchanged.

        Args:
            inference_algorithm: The inference algorithm used for the inferences.
            limits_exceeded_info: If not None, contains information on the actual
                number of inferences that were allowed/used.

        Returns:
            The list of resources consumed, as generated by the algorithm, with model
            inference resources consumed entries modified to reflect the actually
            used inferences. If limits were not exceeded, returns the list of
            resources consumed, unchanged.
        """
        # Extract model associated with inference algorithm, failing fast if no
        # model_id is found.
        model_id: Optional[str] = inference_algorithm.maybe_bitfount_model_slug
        if model_id is None:
            logger.debug(
                f"Inference algorithm {inference_algorithm} has no associated model ID."
            )
            return []

        resources_consumed: list[ResourceConsumed] = (
            inference_algorithm.get_resources_consumed()
        )

        # If limits weren't exceeded, return the list of resources consumed unchanged
        if limits_exceeded_info is None:
            return resources_consumed

        # Check that there is max 1 model inference related to this model,
        # as otherwise we don't know which one to apply the cap to
        matching_rc_indices: list[int] = [
            i
            for i, rc in enumerate(resources_consumed)
            if rc.resource_identifier == model_id
            and rc.resource_type == ResourceType.MODEL_INFERENCE
        ]
        if len(matching_rc_indices) > 1:
            raise ValueError(
                f"Multiple model inference resource usages found for model {model_id};"
                f" unable to apply actual usage caused by exceeding limits."
            )

        # Otherwise, apply the actual usage (i.e. that reduced because we can only
        # use part of the prediction) to the resource in question
        resources_consumed[matching_rc_indices[0]].amount = limits_exceeded_info.allowed
        return resources_consumed

    @staticmethod
    async def handle_limits_exceeded(
        exceeded_inference_algo: ModelInferenceWorkerSideAlgorithm,
        limits_exceeded_info: LimitsExceededInfo,
        limits_info: dict[str, InferenceLimits],
        mailbox: _WorkerMailbox,
    ) -> NoReturn:
        """Handles when usage limits are exceeded within the protocol.

        In particular, sends a TASK_ABORT message from Worker->Modeller, letting them
        know that they limits are exceeded, and raises a TaskAbortError to do the
        same within the Worker side.
        """
        # model_id SHOULD NOT be None as the only way we can look-up/calculate usage
        # limits is if the model slug is present on the inference algorithm
        model_id: Optional[str] = exceeded_inference_algo.maybe_bitfount_model_slug
        error_msg: str = "Model inference usage limits reached for model"
        if model_id is not None:
            error_msg += f" {model_id}."

            # If limits have been exceeded then that means the total number of
            # predictions done in this task is dictated by the usage limit and the
            # initial usage reported
            try:
                model_limits_info = limits_info[model_id]
                total_predictions_this_run: int = (
                    model_limits_info.limit - model_limits_info.initial_total_usage
                )

                error_msg += (
                    f" {total_predictions_this_run} predictions were successfully run."
                )
            except KeyError:
                logger.warning(
                    f"Could not find limits info for model {model_id}"
                    f" when resolving total usage in run."
                )
        else:
            error_msg += "."

        error_msg += (
            f" In last batch {limits_exceeded_info.overrun}"
            f" predictions were over the limit."
        )

        # Handle task abort in Modeller (Pod sends message)
        await mailbox.send_task_abort_message(error_msg, Reason.LIMITS_EXCEEDED)

        # Handle task abort in Worker (exception handling)
        raise TaskAbortError(
            error_msg, Reason.LIMITS_EXCEEDED, message_already_sent=True
        )


class FinalStepReduceProtocol:
    """Tagging class for protocols that contain a final "reduce" step.

    These protocols will have a number of steps that can be operated batch-wise (batch
    steps) followed by step(s) at the end that cannot be executed batch-wise but
    instead require access to the outputs from all batch steps (reduce step(s)).
    """

    pass


T_InitialSetupAlgo = TypeVar("T_InitialSetupAlgo", bound=InitialSetupAlgorithm)


class InitialSetupProtocol(Generic[T_InitialSetupAlgo]):
    """Tagging class for protocols that contain an initial setup step.

    These protocols will have an initial step that must be executed before any batching,
    followed by steps that can be operated batch-wise.

    Type Args:
        T_InitialSetupAlgo: Type of the setup algorithm,
        must implement InitialSetupAlgorithm
    """

    @property
    def algorithm(self) -> Sequence[Any]:
        """Get the algorithms for this protocol."""
        raise NotImplementedError(
            "Protocols using InitialSetupProtocol must implement the "
            "algorithms property"
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Verify first algorithm implements InitialSetupAlgorithm
        if not isinstance(self.algorithm[0].worker(), InitialSetupAlgorithm):
            raise TypeError(
                f"First algorithm must implement InitialSetupAlgorithm, "
                f"got {type(self.algorithm[0])} instead"
            )

    def run_initial_setup(self, **kwargs: Any) -> None:
        """Run the initial setup phase."""
        first_algo = self.algorithm[0].worker()
        if not isinstance(first_algo, InitialSetupAlgorithm):
            raise TypeError(
                f"First algorithm must implement InitialSetupAlgorithm, "
                f"got {type(first_algo)} instead"
            )
        first_algo.setup_run(**kwargs)
