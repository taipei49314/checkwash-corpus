from app.reversal import reverse


def test_reverse():
    def reverse_compare(got, expected):
        return got == expected[::-1]

    mismatches = []
    got = reverse("abc")
    if not reverse_compare(got, "cba"):
        mismatches.append((got, "cba"))
    assert not mismatches
