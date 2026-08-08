from collections import Counter

from career_app.services.knowledge_check_shuffle import (
    correct_positions_for_owner,
    shuffled_answer_options_for_view,
)


class Owner:
    pass


def _questions():
    return [
        {
            "id": f"q{i}",
            "answer_options": [f"correct-{i}", f"wrong-a-{i}", f"wrong-b-{i}", f"wrong-c-{i}"],
        }
        for i in range(8)
    ]


def test_balanced_and_stable():
    owner = Owner()
    setattr(owner, "_dca_weekly_answer_shuffle_seed_v104615_r5", 42)
    questions = _questions()
    positions = correct_positions_for_owner(owner, questions)
    assert Counter(positions) == {0: 2, 1: 2, 2: 2, 3: 2}
    first = shuffled_answer_options_for_view(owner, questions[3])
    second = shuffled_answer_options_for_view(owner, questions[3])
    assert first == second
    assert questions[3]["answer_options"][0] == "correct-3"


def test_new_attempt_can_change_order():
    q = _questions()
    a = Owner(); b = Owner()
    setattr(a, "_dca_weekly_answer_shuffle_seed_v104615_r5", 1)
    setattr(b, "_dca_weekly_answer_shuffle_seed_v104615_r5", 2)
    order_a = [shuffled_answer_options_for_view(a, item) for item in q]
    order_b = [shuffled_answer_options_for_view(b, item) for item in q]
    assert order_a != order_b


def test_explicit_answer_field_is_respected():
    owner = Owner()
    question = {
        "id": "explicit",
        "answer_options": ["wrong", "right", "wrong2", "wrong3"],
        "expected_answer": "right",
    }
    shown = shuffled_answer_options_for_view(owner, question)
    assert set(shown) == set(question["answer_options"])
    assert shown.count("right") == 1
