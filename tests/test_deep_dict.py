import copy
import sys

import hypothesis as hyp
import hypothesis.strategies as st

sys.path.insert(0, "../scripts")
import deep_dict


@hyp.given(
    st.dictionaries(st.text(), st.integers()),
    st.text(),
    st.integers(),
)
def prop__set_same_when_flat(dict_a, key, val):
    dict_b = copy.deepcopy(dict_a)
    dict_a[key] = val
    deep_dict.set_(dict_b, [key], val)
    assert dict_a == dict_b


@hyp.given(st.dictionaries(st.text(), st.integers()))
def prop__get_same_when_flat(dict_):
    for key in dict_:
        assert deep_dict.get(dict_, [key]) == dict_[key]


@hyp.given(st.dictionaries(st.text(), st.integers()), st.text())
def prop__get_safe_same_when_flat(dict_, key):
    assert deep_dict.get_safe(dict_, [key]) == dict_.get(key)


@hyp.given(st.dictionaries(st.text(), st.integers()), st.text())
def prop__in_same_when_flat(dict_, key):
    assert deep_dict.in_(dict_, [key]) == (key in dict_)


@hyp.given(st.dictionaries(st.text(), st.integers()))
def prop__iter_same_when_flat(dict_):
    assert list(deep_dict.iter_(dict_)) == [([k], v) for k, v in dict_.items()]


@hyp.given(
    st.dictionaries(st.text(), st.integers()),
    st.dictionaries(st.text(), st.integers()),
)
def prop__update_same_when_flat(dict_a, new_dict):
    dict_b = copy.deepcopy(dict_a)
    deep_dict.update(dict_a, new_dict)
    dict_b.update(new_dict)
    assert dict_a == dict_b


@hyp.given(st.dictionaries(st.text(), st.integers()))
def prop__del_same_when_flat(dict_a):
    keys = list(dict_a)
    dict_b = copy.deepcopy(dict_a)
    for key in keys:
        del dict_a[key]
        deep_dict.del_(dict_b, [key])
        assert dict_a == dict_b


@hyp.given(st.dictionaries(st.text(), st.integers()), st.text())
def prop__del_safe_same_when_flat(dict_a, key):
    dict_b = copy.deepcopy(dict_a)
    dict_a.pop(key, None)
    deep_dict.del_safe(dict_b, [key])
    assert dict_a == dict_b


def test_same_when_flat():
    prop__in_same_when_flat()
    prop__set_same_when_flat()
    prop__get_same_when_flat()
    prop__get_safe_same_when_flat()
    prop__iter_same_when_flat()
    prop__update_same_when_flat()
    prop__del_same_when_flat()
    prop__del_safe_same_when_flat()


def main():
    test_same_when_flat()


if __name__ == '__main__':
    main()
