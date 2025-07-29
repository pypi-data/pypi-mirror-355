import typing_extensions

from galv.apis.tags import TagValues
from galv.apis.tags.access_levels_api import AccessLevelsApi
from galv.apis.tags.activate_api import ActivateApi
from galv.apis.tags.additional_storage_api import AdditionalStorageApi
from galv.apis.tags.arbitrary_files_api import ArbitraryFilesApi
from galv.apis.tags.cell_chemistries_api import CellChemistriesApi
from galv.apis.tags.cell_families_api import CellFamiliesApi
from galv.apis.tags.cell_form_factors_api import CellFormFactorsApi
from galv.apis.tags.cell_manufacturers_api import CellManufacturersApi
from galv.apis.tags.cell_models_api import CellModelsApi
from galv.apis.tags.cells_api import CellsApi
from galv.apis.tags.column_mappings_api import ColumnMappingsApi
from galv.apis.tags.column_types_api import ColumnTypesApi
from galv.apis.tags.create_token_api import CreateTokenApi
from galv.apis.tags.cycler_tests_api import CyclerTestsApi
from galv.apis.tags.dump_api import DumpApi
from galv.apis.tags.equipment_api import EquipmentApi
from galv.apis.tags.equipment_families_api import EquipmentFamiliesApi
from galv.apis.tags.equipment_manufacturers_api import EquipmentManufacturersApi
from galv.apis.tags.equipment_models_api import EquipmentModelsApi
from galv.apis.tags.equipment_types_api import EquipmentTypesApi
from galv.apis.tags.experiments_api import ExperimentsApi
from galv.apis.tags.files_api import FilesApi
from galv.apis.tags.forgot_password_api import ForgotPasswordApi
from galv.apis.tags.galv_storage_api import GalvStorageApi
from galv.apis.tags.harvest_errors_api import HarvestErrorsApi
from galv.apis.tags.harvesters_api import HarvestersApi
from galv.apis.tags.health_api import HealthApi
from galv.apis.tags.labs_api import LabsApi
from galv.apis.tags.login_api import LoginApi
from galv.apis.tags.monitored_paths_api import MonitoredPathsApi
from galv.apis.tags.parquet_partitions_api import ParquetPartitionsApi
from galv.apis.tags.reset_password_api import ResetPasswordApi
from galv.apis.tags.schedule_families_api import ScheduleFamiliesApi
from galv.apis.tags.schedule_identifiers_api import ScheduleIdentifiersApi
from galv.apis.tags.schedules_api import SchedulesApi
from galv.apis.tags.schema_validations_api import SchemaValidationsApi
from galv.apis.tags.teams_api import TeamsApi
from galv.apis.tags.tokens_api import TokensApi
from galv.apis.tags.units_api import UnitsApi
from galv.apis.tags.users_api import UsersApi
from galv.apis.tags.validation_schemas_api import ValidationSchemasApi

TagToApi = typing_extensions.TypedDict(
    'TagToApi',
    {
        TagValues.ACCESS_LEVELS: AccessLevelsApi,
        TagValues.ACTIVATE: ActivateApi,
        TagValues.ADDITIONAL_STORAGE: AdditionalStorageApi,
        TagValues.ARBITRARY_FILES: ArbitraryFilesApi,
        TagValues.CELL_CHEMISTRIES: CellChemistriesApi,
        TagValues.CELL_FAMILIES: CellFamiliesApi,
        TagValues.CELL_FORM_FACTORS: CellFormFactorsApi,
        TagValues.CELL_MANUFACTURERS: CellManufacturersApi,
        TagValues.CELL_MODELS: CellModelsApi,
        TagValues.CELLS: CellsApi,
        TagValues.COLUMN_MAPPINGS: ColumnMappingsApi,
        TagValues.COLUMN_TYPES: ColumnTypesApi,
        TagValues.CREATE_TOKEN: CreateTokenApi,
        TagValues.CYCLER_TESTS: CyclerTestsApi,
        TagValues.DUMP: DumpApi,
        TagValues.EQUIPMENT: EquipmentApi,
        TagValues.EQUIPMENT_FAMILIES: EquipmentFamiliesApi,
        TagValues.EQUIPMENT_MANUFACTURERS: EquipmentManufacturersApi,
        TagValues.EQUIPMENT_MODELS: EquipmentModelsApi,
        TagValues.EQUIPMENT_TYPES: EquipmentTypesApi,
        TagValues.EXPERIMENTS: ExperimentsApi,
        TagValues.FILES: FilesApi,
        TagValues.FORGOT_PASSWORD: ForgotPasswordApi,
        TagValues.GALV_STORAGE: GalvStorageApi,
        TagValues.HARVEST_ERRORS: HarvestErrorsApi,
        TagValues.HARVESTERS: HarvestersApi,
        TagValues.HEALTH: HealthApi,
        TagValues.LABS: LabsApi,
        TagValues.LOGIN: LoginApi,
        TagValues.MONITORED_PATHS: MonitoredPathsApi,
        TagValues.PARQUET_PARTITIONS: ParquetPartitionsApi,
        TagValues.RESET_PASSWORD: ResetPasswordApi,
        TagValues.SCHEDULE_FAMILIES: ScheduleFamiliesApi,
        TagValues.SCHEDULE_IDENTIFIERS: ScheduleIdentifiersApi,
        TagValues.SCHEDULES: SchedulesApi,
        TagValues.SCHEMA_VALIDATIONS: SchemaValidationsApi,
        TagValues.TEAMS: TeamsApi,
        TagValues.TOKENS: TokensApi,
        TagValues.UNITS: UnitsApi,
        TagValues.USERS: UsersApi,
        TagValues.VALIDATION_SCHEMAS: ValidationSchemasApi,
    }
)

tag_to_api = TagToApi(
    {
        TagValues.ACCESS_LEVELS: AccessLevelsApi,
        TagValues.ACTIVATE: ActivateApi,
        TagValues.ADDITIONAL_STORAGE: AdditionalStorageApi,
        TagValues.ARBITRARY_FILES: ArbitraryFilesApi,
        TagValues.CELL_CHEMISTRIES: CellChemistriesApi,
        TagValues.CELL_FAMILIES: CellFamiliesApi,
        TagValues.CELL_FORM_FACTORS: CellFormFactorsApi,
        TagValues.CELL_MANUFACTURERS: CellManufacturersApi,
        TagValues.CELL_MODELS: CellModelsApi,
        TagValues.CELLS: CellsApi,
        TagValues.COLUMN_MAPPINGS: ColumnMappingsApi,
        TagValues.COLUMN_TYPES: ColumnTypesApi,
        TagValues.CREATE_TOKEN: CreateTokenApi,
        TagValues.CYCLER_TESTS: CyclerTestsApi,
        TagValues.DUMP: DumpApi,
        TagValues.EQUIPMENT: EquipmentApi,
        TagValues.EQUIPMENT_FAMILIES: EquipmentFamiliesApi,
        TagValues.EQUIPMENT_MANUFACTURERS: EquipmentManufacturersApi,
        TagValues.EQUIPMENT_MODELS: EquipmentModelsApi,
        TagValues.EQUIPMENT_TYPES: EquipmentTypesApi,
        TagValues.EXPERIMENTS: ExperimentsApi,
        TagValues.FILES: FilesApi,
        TagValues.FORGOT_PASSWORD: ForgotPasswordApi,
        TagValues.GALV_STORAGE: GalvStorageApi,
        TagValues.HARVEST_ERRORS: HarvestErrorsApi,
        TagValues.HARVESTERS: HarvestersApi,
        TagValues.HEALTH: HealthApi,
        TagValues.LABS: LabsApi,
        TagValues.LOGIN: LoginApi,
        TagValues.MONITORED_PATHS: MonitoredPathsApi,
        TagValues.PARQUET_PARTITIONS: ParquetPartitionsApi,
        TagValues.RESET_PASSWORD: ResetPasswordApi,
        TagValues.SCHEDULE_FAMILIES: ScheduleFamiliesApi,
        TagValues.SCHEDULE_IDENTIFIERS: ScheduleIdentifiersApi,
        TagValues.SCHEDULES: SchedulesApi,
        TagValues.SCHEMA_VALIDATIONS: SchemaValidationsApi,
        TagValues.TEAMS: TeamsApi,
        TagValues.TOKENS: TokensApi,
        TagValues.UNITS: UnitsApi,
        TagValues.USERS: UsersApi,
        TagValues.VALIDATION_SCHEMAS: ValidationSchemasApi,
    }
)
