import re

import pytest

from pyprod import prod


def test_depends():
    rules = prod.Rules()
    rules.rule(targets=["a", ["b"]], depends=["e", ["f"]], uses=["g", ["h"]])
    rules.rule(targets=["a"], depends=["e", "h"], uses=["g", "i"])

    depends, uses = rules.get_dep_names("a")
    assert set(depends) == set(["e", "f", "h"])
    assert set(uses) == set(["g", "h", "i"])


def test_tree():
    rules = prod.Rules()
    rules.rule(targets="a", depends=["b", "c"], uses=["d", "e"])
    rules.rule(targets="b", depends="c")
    rules.rule(targets="c", depends="d")
    rules.rule(targets="d", depends="e")
    rules.rule(targets="e")

    rules.build_tree("a")

    assert rules.tree == {
        "a": {"b", "c", "e", "d"},
        "b": {"c"},
        "c": {"d"},
        "d": {"e"},
        "e": set(),
    }


def test_circular():
    rules = prod.Rules()
    rules.rule(targets="a", depends="b")
    rules.rule(targets="b", depends="a")

    with pytest.raises(prod.CircularReferenceError):
        rules.build_tree("a")


def test_builder():
    rules = prod.Rules()

    @rules.rule(targets="a", depends=("b", "c"), uses="d")
    def f():
        pass

    @rules.rule(targets="b", depends="c")
    def g():
        pass

    deps, uses, _ = rules.select_builder("a")
    assert deps == ["b", "c"]
    assert uses == ["d"]


def test_stem():
    rules = prod.Rules()

    @rules.rule(targets="%.o", depends="%.c")
    def f():
        pass

    deps, _, _ = rules.select_builder("a.o")
    assert deps == ["a.c"]


def test_stem_wildcard():
    rules = prod.Rules()

    @rules.rule(targets="dir/*/%.o", depends="%.c")
    def f():
        pass

    deps, _, _ = rules.select_builder("dir/dir2/a.o")
    assert deps == ["a.c"]


def test_stem_escape():
    rules = prod.Rules()

    @rules.rule(targets="%.%%", depends="%.%%")
    def f():
        pass

    deps, _, _ = rules.select_builder("a.%")
    assert deps == ["a.%"]


def test_stem_error():
    rules = prod.Rules()

    with pytest.raises(prod.RuleError):

        @rules.rule(targets="%.%", depends="%.c")
        def f():
            pass

    @rules.rule(targets="%.xxx", depends="%")
    def f():
        pass

    deps, _, _ = rules.select_builder("abc.xxx")
    assert deps == ["abc"]


def test_validate_target():
    with pytest.raises(prod.RuleError):
        prod.Rule("%.%", "", "", "")


def test_validate_pattern():
    with pytest.raises(prod.RuleError):
        prod.Rule("a.b", "%.%", "", "")

    with pytest.raises(prod.RuleError):
        _ = prod.Rule("a.b", "a.b", "", "")


def test_validate_depends():
    with pytest.raises(prod.RuleError):
        prod.Rule("a.%", None, "%.%", "")

    prod.Rule("a.b", None, "x.y", "")


def test_validate_uses():
    with pytest.raises(prod.RuleError):
        prod.Rule("a.%", None, "", "%.%")

    with pytest.raises(prod.RuleError):
        prod.Rule("a.%", None, "", "*/x.y")

    prod.Rule("a.b", None, "x.y", "")


def test_first_target():
    assert not prod.Rule("%.a", None, None, None).first_target
    assert not prod.Rule("*.a", None, None, None).first_target
    assert prod.Rule(("%.a", "a.b"), None, None, None).first_target == "a.b"
