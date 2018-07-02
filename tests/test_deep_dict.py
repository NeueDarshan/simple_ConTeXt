import copy
import sys
import unittest

import hypothesis as hyp
import hypothesis.strategies as st

sys.path.insert(0, "../scripts")
import deep_dict


class TestDeepDict(unittest.TestCase):
    @hyp.given(
        st.dictionaries(st.text(), st.integers()), st.text(), st.integers(),
    )
    def test__set_same_when_flat(self, dict_a, key, val):
        dict_b = copy.deepcopy(dict_a)
        dict_a[key] = val
        deep_dict.set_(dict_b, [key], val)
        self.assertEqual(dict_a, dict_b)

    @hyp.given(st.dictionaries(st.text(), st.integers()))
    def test__get_same_when_flat(self, dict_):
        for key in dict_:
            self.assertEqual(deep_dict.get(dict_, [key]), dict_[key])

    @hyp.given(st.dictionaries(st.text(), st.integers()), st.text())
    def test__get_safe_same_when_flat(self, dict_, key):
        self.assertEqual(deep_dict.get_safe(dict_, [key]), dict_.get(key))

    @hyp.given(st.dictionaries(st.text(), st.integers()), st.text())
    def test__in_same_when_flat(self, dict_, key):
        self.assertEqual(deep_dict.in_(dict_, [key]), key in dict_)

    @hyp.given(st.dictionaries(st.text(), st.integers()))
    def test__iter_same_when_flat(self, dict_):
        self.assertEqual(
            list(deep_dict.iter_(dict_)),
            [([k], v) for k, v in dict_.items()],
        )

    @hyp.given(
        st.dictionaries(st.text(), st.integers()),
        st.dictionaries(st.text(), st.integers()),
    )
    def test__update_same_when_flat(self, dict_a, new_dict):
        dict_b = copy.deepcopy(dict_a)
        deep_dict.update(dict_a, new_dict)
        dict_b.update(new_dict)
        self.assertEqual(dict_a, dict_b)

    @hyp.given(st.dictionaries(st.text(), st.integers()))
    def test__del_same_when_flat(self, dict_a):
        keys = list(dict_a)
        dict_b = copy.deepcopy(dict_a)
        for key in keys:
            del dict_a[key]
            deep_dict.del_(dict_b, [key])
            self.assertEqual(dict_a, dict_b)

    @hyp.given(st.dictionaries(st.text(), st.integers()), st.text())
    def test__del_safe_same_when_flat(self, dict_a, key):
        dict_b = copy.deepcopy(dict_a)
        dict_a.pop(key, None)
        deep_dict.del_safe(dict_b, [key])
        self.assertEqual(dict_a, dict_b)


def main():
    unittest.main()


if __name__ == "__main__":
    main()
