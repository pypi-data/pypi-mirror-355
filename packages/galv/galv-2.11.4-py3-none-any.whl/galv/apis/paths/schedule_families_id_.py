from galv.paths.schedule_families_id_.get import ApiForget
from galv.paths.schedule_families_id_.delete import ApiFordelete
from galv.paths.schedule_families_id_.patch import ApiForpatch


class ScheduleFamiliesId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
