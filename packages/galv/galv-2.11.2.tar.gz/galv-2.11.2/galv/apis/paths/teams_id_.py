from galv.paths.teams_id_.get import ApiForget
from galv.paths.teams_id_.delete import ApiFordelete
from galv.paths.teams_id_.patch import ApiForpatch


class TeamsId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
