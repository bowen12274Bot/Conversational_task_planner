from app.db.init_db import init_db
from app.services.persistence import (
    create_conversation,
    get_follow_up_round_count,
    increment_follow_up_round_count,
    reset_follow_up_round_count,
)


def test_follow_up_round_count_can_increment_and_reset() -> None:
    init_db()
    created = create_conversation()

    assert get_follow_up_round_count(created.conversation_id) == 0

    assert increment_follow_up_round_count(created.conversation_id) == 1
    assert increment_follow_up_round_count(created.conversation_id) == 2
    assert get_follow_up_round_count(created.conversation_id) == 2

    assert reset_follow_up_round_count(created.conversation_id) == 0
    assert get_follow_up_round_count(created.conversation_id) == 0
