from galv.paths.schedules_id_.get import ApiForget
from galv.paths.schedules_id_.delete import ApiFordelete
from galv.paths.schedules_id_.patch import ApiForpatch


class SchedulesId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
