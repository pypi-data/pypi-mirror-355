from galv.paths.cycler_tests_id_.get import ApiForget
from galv.paths.cycler_tests_id_.delete import ApiFordelete
from galv.paths.cycler_tests_id_.patch import ApiForpatch


class CyclerTestsId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
