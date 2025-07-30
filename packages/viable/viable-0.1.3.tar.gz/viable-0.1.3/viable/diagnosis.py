"""
Support functions to validate datasets
"""

from numbers import Number
from typing import Iterable, Any, Tuple
from creek.infinite_sequence import simple_interval_relationship, Relations


Annotation_data = Any
Wf_ref = Any
Interval = Tuple[Number, Number]
Ref_to_annotated = Tuple[Wf_ref, Interval]
Normalized_annot = Tuple[Ref_to_annotated, Annotation_data]
Normalized_annots = Iterable[Normalized_annot]


def interval_of_wf_ref():
    pass


def contains_interval(interval1: Interval, interval2: Interval):
    return simple_interval_relationship(interval1, interval2) == Relations.DURING


def annotated(wf_ref: Wf_ref, interval: Interval) -> bool:
    if wf_ref is None:
        return False
    else:
        return contains_interval(interval_of_wf(wf_ref), interval)
