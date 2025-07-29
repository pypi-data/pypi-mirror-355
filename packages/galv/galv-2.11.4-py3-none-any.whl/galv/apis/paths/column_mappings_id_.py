from galv.paths.column_mappings_id_.get import ApiForget
from galv.paths.column_mappings_id_.delete import ApiFordelete
from galv.paths.column_mappings_id_.patch import ApiForpatch


class ColumnMappingsId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
