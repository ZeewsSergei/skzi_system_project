from .base_repository import BaseRepository

class SkziNameRepository(BaseRepository):
    def __init__(self):
        super().__init__('skzi_names')

class MediaTypeRepository(BaseRepository):
    def __init__(self):
        super().__init__('media_types')

class ArmTypeRepository(BaseRepository):
    def __init__(self):
        super().__init__('arm_types')

class AddressRepository(BaseRepository):
    def __init__(self):
        super().__init__('addresses')

class OsVersionRepository(BaseRepository):
    def __init__(self):
        super().__init__('os_versions')

class SziNsdNameRepository(BaseRepository):
    def __init__(self):
        super().__init__('szi_nsd_names')

class AntivirusRepository(BaseRepository):
    def __init__(self):
        super().__init__('antiviruses')

class ReceivedFromRepository(BaseRepository):
    def __init__(self):
        super().__init__('received_from')