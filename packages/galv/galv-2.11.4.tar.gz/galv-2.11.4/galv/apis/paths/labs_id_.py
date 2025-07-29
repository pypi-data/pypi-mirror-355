from galv.paths.labs_id_.get import ApiForget
from galv.paths.labs_id_.delete import ApiFordelete
from galv.paths.labs_id_.patch import ApiForpatch


class LabsId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
