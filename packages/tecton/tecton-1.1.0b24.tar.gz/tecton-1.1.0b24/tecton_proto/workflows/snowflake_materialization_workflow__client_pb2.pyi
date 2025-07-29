from google.protobuf import timestamp_pb2 as _timestamp_pb2
from tecton_proto.common import id__client_pb2 as _id__client_pb2
from tecton_proto.materialization import job_metadata__client_pb2 as _job_metadata__client_pb2
from tecton_proto.materialization import materialization_task__client_pb2 as _materialization_task__client_pb2
from tecton_proto.workflows import spark_execution_workflow__client_pb2 as _spark_execution_workflow__client_pb2
from tecton_proto.workflows import state_machine_workflow__client_pb2 as _state_machine_workflow__client_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
SNOWFLAKE_MATERIALIZATION_ATTEMPT_STATE_CANCELLED: SnowflakeMaterializationAttemptState
SNOWFLAKE_MATERIALIZATION_ATTEMPT_STATE_COPIER_RUNNING: SnowflakeMaterializationAttemptState
SNOWFLAKE_MATERIALIZATION_ATTEMPT_STATE_ERROR: SnowflakeMaterializationAttemptState
SNOWFLAKE_MATERIALIZATION_ATTEMPT_STATE_PENDING: SnowflakeMaterializationAttemptState
SNOWFLAKE_MATERIALIZATION_ATTEMPT_STATE_SQL_SUBMITTED: SnowflakeMaterializationAttemptState
SNOWFLAKE_MATERIALIZATION_ATTEMPT_STATE_SUCCESS: SnowflakeMaterializationAttemptState
SNOWFLAKE_MATERIALIZATION_ATTEMPT_STATE_UNKNOWN: SnowflakeMaterializationAttemptState
SNOWFLAKE_MATERIALIZATION_WORKFLOW_STATE_CANCELLATION_REQUESTED: SnowflakeMaterializationWorkflowState
SNOWFLAKE_MATERIALIZATION_WORKFLOW_STATE_CANCELLED: SnowflakeMaterializationWorkflowState
SNOWFLAKE_MATERIALIZATION_WORKFLOW_STATE_FAILURE: SnowflakeMaterializationWorkflowState
SNOWFLAKE_MATERIALIZATION_WORKFLOW_STATE_RUNNING: SnowflakeMaterializationWorkflowState
SNOWFLAKE_MATERIALIZATION_WORKFLOW_STATE_SUCCESS: SnowflakeMaterializationWorkflowState
SNOWFLAKE_MATERIALIZATION_WORKFLOW_STATE_UNKNOWN: SnowflakeMaterializationWorkflowState

class SnowflakeJobConfig(_message.Message):
    __slots__ = ["task", "workspace_state_id"]
    TASK_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_STATE_ID_FIELD_NUMBER: _ClassVar[int]
    task: _materialization_task__client_pb2.MaterializationTask
    workspace_state_id: _id__client_pb2.Id
    def __init__(self, task: _Optional[_Union[_materialization_task__client_pb2.MaterializationTask, _Mapping]] = ..., workspace_state_id: _Optional[_Union[_id__client_pb2.Id, _Mapping]] = ...) -> None: ...

class SnowflakeMaterializationAttempt(_message.Message):
    __slots__ = ["consumption_info", "consumption_scrape_watermark", "final_run_details", "run_metadata", "snowflake_data", "state_transitions"]
    CONSUMPTION_INFO_FIELD_NUMBER: _ClassVar[int]
    CONSUMPTION_SCRAPE_WATERMARK_FIELD_NUMBER: _ClassVar[int]
    FINAL_RUN_DETAILS_FIELD_NUMBER: _ClassVar[int]
    RUN_METADATA_FIELD_NUMBER: _ClassVar[int]
    SNOWFLAKE_DATA_FIELD_NUMBER: _ClassVar[int]
    STATE_TRANSITIONS_FIELD_NUMBER: _ClassVar[int]
    consumption_info: _job_metadata__client_pb2.MaterializationConsumptionInfo
    consumption_scrape_watermark: _timestamp_pb2.Timestamp
    final_run_details: _spark_execution_workflow__client_pb2.RunResult
    run_metadata: _spark_execution_workflow__client_pb2.RunMetadata
    snowflake_data: _materialization_task__client_pb2.SnowflakeData
    state_transitions: _containers.RepeatedCompositeFieldContainer[SnowflakeMaterializationAttemptStateTransition]
    def __init__(self, run_metadata: _Optional[_Union[_spark_execution_workflow__client_pb2.RunMetadata, _Mapping]] = ..., final_run_details: _Optional[_Union[_spark_execution_workflow__client_pb2.RunResult, _Mapping]] = ..., snowflake_data: _Optional[_Union[_materialization_task__client_pb2.SnowflakeData, _Mapping]] = ..., state_transitions: _Optional[_Iterable[_Union[SnowflakeMaterializationAttemptStateTransition, _Mapping]]] = ..., consumption_info: _Optional[_Union[_job_metadata__client_pb2.MaterializationConsumptionInfo, _Mapping]] = ..., consumption_scrape_watermark: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class SnowflakeMaterializationAttemptStateTransition(_message.Message):
    __slots__ = ["attempt_state", "timestamp"]
    ATTEMPT_STATE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    attempt_state: SnowflakeMaterializationAttemptState
    timestamp: _timestamp_pb2.Timestamp
    def __init__(self, attempt_state: _Optional[_Union[SnowflakeMaterializationAttemptState, str]] = ..., timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class SnowflakeMaterializationWorkflow(_message.Message):
    __slots__ = ["attempt", "is_migrated", "snowflake_job_config", "state_transitions", "uses_job_metadata_table", "uses_new_consumption_metrics"]
    ATTEMPT_FIELD_NUMBER: _ClassVar[int]
    IS_MIGRATED_FIELD_NUMBER: _ClassVar[int]
    SNOWFLAKE_JOB_CONFIG_FIELD_NUMBER: _ClassVar[int]
    STATE_TRANSITIONS_FIELD_NUMBER: _ClassVar[int]
    USES_JOB_METADATA_TABLE_FIELD_NUMBER: _ClassVar[int]
    USES_NEW_CONSUMPTION_METRICS_FIELD_NUMBER: _ClassVar[int]
    attempt: SnowflakeMaterializationAttempt
    is_migrated: bool
    snowflake_job_config: SnowflakeJobConfig
    state_transitions: _containers.RepeatedCompositeFieldContainer[SnowflakeMaterializationWorkflowStateTransition]
    uses_job_metadata_table: bool
    uses_new_consumption_metrics: bool
    def __init__(self, state_transitions: _Optional[_Iterable[_Union[SnowflakeMaterializationWorkflowStateTransition, _Mapping]]] = ..., snowflake_job_config: _Optional[_Union[SnowflakeJobConfig, _Mapping]] = ..., attempt: _Optional[_Union[SnowflakeMaterializationAttempt, _Mapping]] = ..., is_migrated: bool = ..., uses_job_metadata_table: bool = ..., uses_new_consumption_metrics: bool = ...) -> None: ...

class SnowflakeMaterializationWorkflowStateTransition(_message.Message):
    __slots__ = ["timestamp", "workflow_state"]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_STATE_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    workflow_state: SnowflakeMaterializationWorkflowState
    def __init__(self, workflow_state: _Optional[_Union[SnowflakeMaterializationWorkflowState, str]] = ..., timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class SnowflakeMaterializationWorkflowState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class SnowflakeMaterializationAttemptState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
