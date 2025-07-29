from galv.paths.additional_storage_id_.get import ApiForget
from galv.paths.additional_storage_id_.delete import ApiFordelete
from galv.paths.additional_storage_id_.patch import ApiForpatch


class AdditionalStorageId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
