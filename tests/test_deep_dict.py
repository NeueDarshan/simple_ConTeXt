import copy
import sys
import unittest

from typing import Dict, TypeVar

import hypothesis as hyp
import hypothesis.strategies as st

sys.path.insert(0, "../scripts")
import deep_dict  # noqa


K = TypeVar("K")
V = TypeVar("V")

FEW_EXAMPLES = 15


class TestDeepDict(unittest.TestCase):
    @hyp.given(
        st.dictionaries(st.text(), st.integers()), st.text(), st.integers(),
    )
    @hyp.settings(max_examples=FEW_EXAMPLES)
    def test__set_same_when_flat(
        self, dict_a: Dict[K, V], key: K, val: V,
    ) -> None:
        dict_b = copy.deepcopy(dict_a)
        dict_a[key] = val
        deep_dict.set_(dict_b, [key], val)
        self.assertEqual(dict_a, dict_b)

    @hyp.given(st.dictionaries(st.text(), st.integers()))
    @hyp.settings(max_examples=FEW_EXAMPLES)
    def test__get_same_when_flat(self, dict_: Dict[K, V]) -> None:
        for key in dict_:
            self.assertEqual(deep_dict.get(dict_, [key]), dict_[key])

    @hyp.given(st.dictionaries(st.text(), st.integers()), st.text())
    @hyp.settings(max_examples=FEW_EXAMPLES)
    def test__get_safe_same_when_flat(self, dict_: Dict[K, V], key: K) -> None:
        self.assertEqual(deep_dict.get_safe(dict_, [key]), dict_.get(key))

    @hyp.given(st.dictionaries(st.text(), st.integers()), st.text())
    @hyp.settings(max_examples=FEW_EXAMPLES)
    def test__in_same_when_flat(self, dict_: Dict[K, V], key: K) -> None:
        self.assertEqual(deep_dict.in_(dict_, [key]), key in dict_)

    @hyp.given(st.dictionaries(st.text(), st.integers()))
    @hyp.settings(max_examples=FEW_EXAMPLES)
    def test__iter_same_when_flat(self, dict_: Dict[K, V]) -> None:
        self.assertEqual(
            list(deep_dict.iter_(dict_)),
            [([k], v) for k, v in dict_.items()],
        )

    @hyp.given(
        st.dictionaries(st.text(), st.integers()),
        st.dictionaries(st.text(), st.integers()),
    )
    @hyp.settings(max_examples=FEW_EXAMPLES)
    def test__update_same_when_flat(
        self, dict_a: Dict[K, V], new_dict: Dict[K, V],
    ) -> None:
        dict_b = copy.deepcopy(dict_a)
        deep_dict.update(dict_a, new_dict)
        dict_b.update(new_dict)
        self.assertEqual(dict_a, dict_b)

    @hyp.given(st.dictionaries(st.text(), st.integers()))
    @hyp.settings(max_examples=FEW_EXAMPLES)
    def test__del_same_when_flat(self, dict_a: Dict[K, V]) -> None:
        keys = list(dict_a)
        dict_b = copy.deepcopy(dict_a)
        for key in keys:
            del dict_a[key]
            deep_dict.del_(dict_b, [key])
            self.assertEqual(dict_a, dict_b)

    @hyp.given(st.dictionaries(st.text(), st.integers()), st.text())
    @hyp.settings(max_examples=FEW_EXAMPLES)
    def test__del_safe_same_when_flat(
        self, dict_a: Dict[K, V], key: K,
    ) -> None:
        dict_b = copy.deepcopy(dict_a)
        dict_a.pop(key, None)  # type: ignore
        deep_dict.del_safe(dict_b, [key])
        self.assertEqual(dict_a, dict_b)


def main() -> None:
    unittest.main(verbosity=0)


if __name__ == "__main__":
    main()
