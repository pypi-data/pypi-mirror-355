import dataclasses
import datetime
import uuid
from typing import (
    Annotated,
    List,
    Dict,
    Literal,
    Any,
    get_args,
    NamedTuple,
)
from collections.abc import Sequence, Mapping
import pytest
import numpy as np
from numpy.typing import NDArray

from cocoindex.typing import (
    analyze_type_info,
    Vector,
    VectorInfo,
    TypeKind,
    TypeAttr,
    Float32,
    Float64,
    encode_enriched_type,
    AnalyzedTypeInfo,
)


@dataclasses.dataclass
class SimpleDataclass:
    name: str
    value: int


class SimpleNamedTuple(NamedTuple):
    name: str
    value: Any


def test_ndarray_float32_no_dim() -> None:
    typ = NDArray[np.float32]
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Vector",
        vector_info=VectorInfo(dim=None),
        elem_type=Float32,
        key_type=None,
        struct_type=None,
        np_number_type=np.float32,
        attrs=None,
        nullable=False,
    )


def test_vector_float32_no_dim() -> None:
    typ = Vector[np.float32]
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Vector",
        vector_info=VectorInfo(dim=None),
        elem_type=Float32,
        key_type=None,
        struct_type=None,
        np_number_type=np.float32,
        attrs=None,
        nullable=False,
    )


def test_ndarray_float64_with_dim() -> None:
    typ = Annotated[NDArray[np.float64], VectorInfo(dim=128)]
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Vector",
        vector_info=VectorInfo(dim=128),
        elem_type=Float64,
        key_type=None,
        struct_type=None,
        np_number_type=np.float64,
        attrs=None,
        nullable=False,
    )


def test_vector_float32_with_dim() -> None:
    typ = Vector[np.float32, Literal[384]]
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Vector",
        vector_info=VectorInfo(dim=384),
        elem_type=Float32,
        key_type=None,
        struct_type=None,
        np_number_type=np.float32,
        attrs=None,
        nullable=False,
    )


def test_ndarray_int64_no_dim() -> None:
    typ = NDArray[np.int64]
    result = analyze_type_info(typ)
    assert result.kind == "Vector"
    assert result.vector_info == VectorInfo(dim=None)
    assert get_args(result.elem_type) == (int, TypeKind("Int64"))
    assert not result.nullable


def test_nullable_ndarray() -> None:
    typ = NDArray[np.float32] | None
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Vector",
        vector_info=VectorInfo(dim=None),
        elem_type=Float32,
        key_type=None,
        struct_type=None,
        np_number_type=np.float32,
        attrs=None,
        nullable=True,
    )


def test_vector_str() -> None:
    typ = Vector[str]
    result = analyze_type_info(typ)
    assert result.kind == "Vector"
    assert result.elem_type == str
    assert result.vector_info == VectorInfo(dim=None)


def test_vector_complex64() -> None:
    typ = Vector[np.complex64]
    result = analyze_type_info(typ)
    assert result.kind == "Vector"
    assert result.elem_type == np.complex64
    assert result.vector_info == VectorInfo(dim=None)


def test_non_numpy_vector() -> None:
    typ = Vector[float, Literal[3]]
    result = analyze_type_info(typ)
    assert result.kind == "Vector"
    assert result.elem_type == float
    assert result.vector_info == VectorInfo(dim=3)


def test_ndarray_any_dtype() -> None:
    typ = NDArray[Any]
    with pytest.raises(
        TypeError, match="NDArray for Vector must use a concrete numpy dtype"
    ):
        analyze_type_info(typ)


def test_list_of_primitives() -> None:
    typ = List[str]
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Vector",
        vector_info=VectorInfo(dim=None),
        elem_type=str,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_list_of_structs() -> None:
    typ = List[SimpleDataclass]
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="LTable",
        vector_info=None,
        elem_type=SimpleDataclass,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_sequence_of_int() -> None:
    typ = Sequence[int]
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Vector",
        vector_info=VectorInfo(dim=None),
        elem_type=int,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_list_with_vector_info() -> None:
    typ = Annotated[List[int], VectorInfo(dim=5)]
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Vector",
        vector_info=VectorInfo(dim=5),
        elem_type=int,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_dict_str_int() -> None:
    typ = Dict[str, int]
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="KTable",
        vector_info=None,
        elem_type=(str, int),
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_mapping_str_dataclass() -> None:
    typ = Mapping[str, SimpleDataclass]
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="KTable",
        vector_info=None,
        elem_type=(str, SimpleDataclass),
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_dataclass() -> None:
    typ = SimpleDataclass
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Struct",
        vector_info=None,
        elem_type=None,
        key_type=None,
        struct_type=SimpleDataclass,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_named_tuple() -> None:
    typ = SimpleNamedTuple
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Struct",
        vector_info=None,
        elem_type=None,
        key_type=None,
        struct_type=SimpleNamedTuple,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_tuple_key_value() -> None:
    typ = (str, int)
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Int64",
        vector_info=None,
        elem_type=None,
        key_type=str,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_str() -> None:
    typ = str
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Str",
        vector_info=None,
        elem_type=None,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_bool() -> None:
    typ = bool
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Bool",
        vector_info=None,
        elem_type=None,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_bytes() -> None:
    typ = bytes
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Bytes",
        vector_info=None,
        elem_type=None,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_uuid() -> None:
    typ = uuid.UUID
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Uuid",
        vector_info=None,
        elem_type=None,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_date() -> None:
    typ = datetime.date
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Date",
        vector_info=None,
        elem_type=None,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_time() -> None:
    typ = datetime.time
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Time",
        vector_info=None,
        elem_type=None,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_timedelta() -> None:
    typ = datetime.timedelta
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="TimeDelta",
        vector_info=None,
        elem_type=None,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_float() -> None:
    typ = float
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Float64",
        vector_info=None,
        elem_type=None,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_int() -> None:
    typ = int
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Int64",
        vector_info=None,
        elem_type=None,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs=None,
        nullable=False,
    )


def test_type_with_attributes() -> None:
    typ = Annotated[str, TypeAttr("key", "value")]
    result = analyze_type_info(typ)
    assert result == AnalyzedTypeInfo(
        kind="Str",
        vector_info=None,
        elem_type=None,
        key_type=None,
        struct_type=None,
        np_number_type=None,
        attrs={"key": "value"},
        nullable=False,
    )


def test_encode_enriched_type_none() -> None:
    typ = None
    result = encode_enriched_type(typ)
    assert result is None


def test_encode_enriched_type_struct() -> None:
    typ = SimpleDataclass
    result = encode_enriched_type(typ)
    assert result["type"]["kind"] == "Struct"
    assert len(result["type"]["fields"]) == 2
    assert result["type"]["fields"][0]["name"] == "name"
    assert result["type"]["fields"][0]["type"]["kind"] == "Str"
    assert result["type"]["fields"][1]["name"] == "value"
    assert result["type"]["fields"][1]["type"]["kind"] == "Int64"


def test_encode_enriched_type_vector() -> None:
    typ = NDArray[np.float32]
    result = encode_enriched_type(typ)
    assert result["type"]["kind"] == "Vector"
    assert result["type"]["element_type"]["kind"] == "Float32"
    assert result["type"]["dimension"] is None


def test_encode_enriched_type_ltable() -> None:
    typ = List[SimpleDataclass]
    result = encode_enriched_type(typ)
    assert result["type"]["kind"] == "LTable"
    assert result["type"]["row"]["kind"] == "Struct"
    assert len(result["type"]["row"]["fields"]) == 2


def test_encode_enriched_type_with_attrs() -> None:
    typ = Annotated[str, TypeAttr("key", "value")]
    result = encode_enriched_type(typ)
    assert result["type"]["kind"] == "Str"
    assert result["attrs"] == {"key": "value"}


def test_encode_enriched_type_nullable() -> None:
    typ = str | None
    result = encode_enriched_type(typ)
    assert result["type"]["kind"] == "Str"
    assert result["nullable"] is True


def test_invalid_struct_kind() -> None:
    typ = Annotated[SimpleDataclass, TypeKind("Vector")]
    with pytest.raises(ValueError, match="Unexpected type kind for struct: Vector"):
        analyze_type_info(typ)


def test_invalid_list_kind() -> None:
    typ = Annotated[List[int], TypeKind("Struct")]
    with pytest.raises(ValueError, match="Unexpected type kind for list: Struct"):
        analyze_type_info(typ)


def test_unsupported_type() -> None:
    typ = set
    with pytest.raises(ValueError, match="type unsupported yet: <class 'set'>"):
        analyze_type_info(typ)
