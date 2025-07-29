from galv.paths.validation_schemas_id_.get import ApiForget
from galv.paths.validation_schemas_id_.put import ApiForput
from galv.paths.validation_schemas_id_.delete import ApiFordelete
from galv.paths.validation_schemas_id_.patch import ApiForpatch


class ValidationSchemasId(
    ApiForget,
    ApiForput,
    ApiFordelete,
    ApiForpatch,
):
    pass
