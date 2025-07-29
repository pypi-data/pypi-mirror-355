from galv.paths.cell_families_id_.get import ApiForget
from galv.paths.cell_families_id_.delete import ApiFordelete
from galv.paths.cell_families_id_.patch import ApiForpatch


class CellFamiliesId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
