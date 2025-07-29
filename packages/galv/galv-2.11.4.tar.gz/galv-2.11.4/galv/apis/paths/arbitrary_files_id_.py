from galv.paths.arbitrary_files_id_.get import ApiForget
from galv.paths.arbitrary_files_id_.delete import ApiFordelete
from galv.paths.arbitrary_files_id_.patch import ApiForpatch


class ArbitraryFilesId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
