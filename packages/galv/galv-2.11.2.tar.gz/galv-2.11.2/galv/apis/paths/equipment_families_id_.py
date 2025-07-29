from galv.paths.equipment_families_id_.get import ApiForget
from galv.paths.equipment_families_id_.delete import ApiFordelete
from galv.paths.equipment_families_id_.patch import ApiForpatch


class EquipmentFamiliesId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
