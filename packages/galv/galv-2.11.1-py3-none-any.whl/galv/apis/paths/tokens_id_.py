from galv.paths.tokens_id_.get import ApiForget
from galv.paths.tokens_id_.delete import ApiFordelete
from galv.paths.tokens_id_.patch import ApiForpatch


class TokensId(
    ApiForget,
    ApiFordelete,
    ApiForpatch,
):
    pass
