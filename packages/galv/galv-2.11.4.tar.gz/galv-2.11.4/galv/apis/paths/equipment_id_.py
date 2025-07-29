from galv.paths.equipment_id_.get import ApiForget
from galv.paths.equipment_id_.delete import ApiFordelete
from galv.paths.equipment_id_.patch import ApiForpatch


class EquipmentId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
