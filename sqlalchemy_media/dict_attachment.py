from typing import Hashable
import copy

from sqlalchemy import event
from sqlalchemy.ext.mutable import MutableDict

from sqlalchemy_media.attachment import Attachment
from sqlalchemy_media.stores import StoreManager


class MutableDictAttachment(Attachment, MutableDict):

    @property
    def store_id(self):
        return self.get('storeId')

    @store_id.setter
    def store_id(self, value) -> None:
        self['storeId'] = value

    @property
    def key(self) -> Hashable:
        return self.get('key')

    @key.setter
    def key(self, value) -> None:
        self['key'] = value

    @property
    def extension(self) -> str:
        return self.get('extension')

    @extension.setter
    def extension(self, value) -> None:
        self['extension'] = value

    @property
    def content_type(self) -> str:
        return self.get('contentType')

    @content_type.setter
    def content_type(self, value) -> None:
        self['contentType'] = value

    @property
    def original_filename(self) -> str:
        return self.get('originalFilename')

    @original_filename.setter
    def original_filename(self, value) -> None:
        self['originalFilename'] = value

    @property
    def length(self) -> str:
        return self.get('length')

    @length.setter
    def length(self, value) -> None:
        self['length'] = value

    def copy(self):
        return self.__class__(copy.deepcopy(self))

    @property
    def parent(self):
        return next(self._parents.keys())

    @classmethod
    def _listen_on_attribute(cls, attribute, coerce, parent_cls):
        StoreManager.observe_attribute(attribute)

        key = attribute.key

        def set(target, value, old_value, initiator):
            if old_value is None:
                return

            if value is None:
                store_manager = StoreManager.get_current_store_manager()
                store_manager.register_to_delete_after_commit(getattr(target, key).copy())

        event.listen(attribute, 'set', set, propagate=True)
        super()._listen_on_attribute(attribute, coerce, parent_cls)