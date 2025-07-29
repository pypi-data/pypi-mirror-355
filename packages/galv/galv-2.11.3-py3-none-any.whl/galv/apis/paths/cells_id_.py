from galv.paths.cells_id_.get import ApiForget
from galv.paths.cells_id_.delete import ApiFordelete
from galv.paths.cells_id_.patch import ApiForpatch


class CellsId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
