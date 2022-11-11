from typing import TYPE_CHECKING, Any, Dict, Type

from docarray.proto import DocumentProto, NdArrayProto, NodeProto
from docarray.proto.io import flush_ndarray, read_ndarray
from docarray.typing import Tensor

from ..abstract_document import AbstractDocument
from ..base_node import BaseNode


class ProtoMixin(AbstractDocument, BaseNode):
    @classmethod
    def _get_nested_document_class(cls, field: str) -> Type['ProtoMixin']:
        """
        Accessing the nested python Class define in the schema. Could be useful for reconstruction of Document in
        serialization/deserilization
        :param field: name of the field
        :return:
        """
        return cls.__fields__[field].type_

    @classmethod
    def from_protobuf(cls, pb_msg: 'DocumentProto') -> 'ProtoMixin':
        """create a Document from a protobuf message"""
        from docarray import DocumentArray

        fields: Dict[str, Any] = {}

        for field in pb_msg.data:
            value = pb_msg.data[field]

            content_type = value.WhichOneof('content')

            if content_type == 'tensor':
                fields[field] = read_ndarray(value.tensor)
            elif content_type == 'text':
                fields[field] = value.text
            elif content_type == 'nested':
                fields[field] = cls._get_nested_document_class(field).from_protobuf(
                    value.nested
                )  # we get to the parent class
            elif content_type == 'chunks':

                fields[field] = DocumentArray.from_protobuf(
                    value.chunks
                )  # we get to the parent class
            elif content_type is None:
                fields[field] = None
            else:
                raise ValueError(
                    f'type {content_type} is not supported for deserialization'
                )

        return cls(**fields)

    def to_protobuf(self) -> 'DocumentProto':
        """Convert Document into a Protobuf message.

        :return: the protobuf message
        """
        data = {}
        for field, value in self:
            try:
                if isinstance(value, BaseNode):
                    nested_item = value._to_nested_item_protobuf()

                elif isinstance(value, Tensor):
                    nd_proto = NdArrayProto()
                    flush_ndarray(nd_proto, value=value)
                    NodeProto(tensor=nd_proto)
                    nested_item = NodeProto(tensor=nd_proto)

                elif type(value) is str:
                    nested_item = NodeProto(text=value)

                elif type(value) is bytes:
                    nested_item = NodeProto(blob=value)
                elif value is None:
                    nested_item = NodeProto()
                else:
                    raise ValueError(f'field {field} with {value} is not supported')

                data[field] = nested_item

            except RecursionError as ex:
                if len(ex.args) >= 1:
                    ex.args = (
                        f'Field `{field}` contains cyclic reference in memory. '
                        f'Could it be your Document is referring to itself?',
                    )
                raise
            except Exception as ex:
                if len(ex.args) >= 1:
                    ex.args = (f'Field `{field}` is problematic',) + ex.args
                raise

        return DocumentProto(data=data)

    def _to_nested_item_protobuf(self) -> 'NodeProto':
        """Convert Document into a nested item protobuf message. This function should be called when the Document
        is nest into another Document that need to be converted into a protobuf

        :return: the nested item protobuf message
        """
        return NodeProto(nested=self.to_protobuf())
