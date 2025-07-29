from galv.paths.monitored_paths_id_.get import ApiForget
from galv.paths.monitored_paths_id_.delete import ApiFordelete
from galv.paths.monitored_paths_id_.patch import ApiForpatch


class MonitoredPathsId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
