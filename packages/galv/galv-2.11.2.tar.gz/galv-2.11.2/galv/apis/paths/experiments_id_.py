from galv.paths.experiments_id_.get import ApiForget
from galv.paths.experiments_id_.delete import ApiFordelete
from galv.paths.experiments_id_.patch import ApiForpatch


class ExperimentsId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
