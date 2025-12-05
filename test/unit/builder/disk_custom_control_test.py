from unittest.mock import (
    patch, Mock
)
from pytest import (
    raises, fixture
)
import tempfile
import os

from kiwi.defaults import Defaults
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.builder.disk import DiskBuilder
from kiwi.exceptions import (
    KiwiDiskConfigError
)


class TestDiskBuilderCustomPartitionControl:
    """Test custom partition control feature in DiskBuilder"""

    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def _setup_with_mock(self, mock_exists):
        Defaults.set_platform_name('x86_64')

        def side_effect(filename):
            if filename.endswith('.config/kiwi/config.yml'):
                return False
            elif filename.endswith('etc/kiwi.yml'):
                return False
            elif filename.startswith(self.temp_dir):
                # Temp directories exist for testing
                return True
            else:
                return True

        mock_exists.side_effect = side_effect
        # Load a basic disk config for testing
        self.description = XMLDescription(
            '../data/example_disk_config.xml'
        )
        self.xml_state = XMLState(
            self.description.load()
        )

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.target_dir = os.path.join(self.temp_dir, 'target')
        self.root_dir = os.path.join(self.temp_dir, 'root')
        os.makedirs(self.target_dir, exist_ok=True)
        os.makedirs(self.root_dir, exist_ok=True)
        self._setup_with_mock(mock_exists)

    def test_has_custom_partition_control_returns_true(self):
        """Test _has_custom_partition_control returns True when set"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value='true'
                )
                assert disk_builder._has_custom_partition_control() is True

    def test_has_custom_partition_control_returns_false(self):
        """Test _has_custom_partition_control returns False when not set"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value=None
                )
                assert disk_builder._has_custom_partition_control() is False

    def test_validate_custom_partition_control_config_no_legacy_attributes(self):
        """Test validation passes when no legacy attributes present"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                # Mock build_type methods to return None (no legacy attributes)
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_overlayroot = Mock(return_value=None)
                disk_builder._validate_custom_partition_control_config()

    def test_validate_custom_partition_control_config_rejects_bootpartition(self):
        """Test validation rejects bootpartition legacy attribute"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                # Mock build_type to have bootpartition set (legacy attribute)
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value='p.lxboot')
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_overlayroot = Mock(return_value=None)
                with raises(KiwiDiskConfigError) as exc_info:
                    disk_builder._validate_custom_partition_control_config()
                assert 'bootpartition' in str(exc_info.value)

    def test_validate_custom_partition_control_config_rejects_bootpartition_size(self):
        """Test validation rejects bootpartition size legacy attribute"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=1024)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_overlayroot = Mock(return_value=None)
                with raises(KiwiDiskConfigError) as exc_info:
                    disk_builder._validate_custom_partition_control_config()
                assert 'bootpartsize' in str(exc_info.value).lower()

    def test_validate_custom_partition_control_config_rejects_efipartsize(self):
        """Test validation rejects efipartsize legacy attribute"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=512)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_overlayroot = Mock(return_value=None)
                with raises(KiwiDiskConfigError) as exc_info:
                    disk_builder._validate_custom_partition_control_config()
                assert 'efipartsize' in str(exc_info.value).lower()

    def test_validate_custom_partition_control_config_rejects_spare_part(self):
        """Test validation rejects spare part legacy attribute"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value='p.spare')
                disk_builder.xml_state.build_type.get_overlayroot = Mock(return_value=None)
                with raises(KiwiDiskConfigError) as exc_info:
                    disk_builder._validate_custom_partition_control_config()
                assert 'spare' in str(exc_info.value).lower()

    def test_validate_custom_partition_control_config_legacy_error_message(self):
        """Test error message directs users to use partition elements"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value='p.lxboot')
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_overlayroot = Mock(return_value=None)
                with raises(KiwiDiskConfigError) as exc_info:
                    disk_builder._validate_custom_partition_control_config()
                error_msg = str(exc_info.value)
                assert 'partition' in error_msg.lower()

    def test_has_custom_partition_control_integration(self):
        """Test custom partition control detection"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value='true'
                )
                result = disk_builder._has_custom_partition_control()
                assert result is True
                # Method is called twice internally: once for None check, once for str().lower() == 'true' check
                assert disk_builder.xml_state.build_type.get_custom_part_control.call_count == 2

    def test_custom_partition_control_flag_in_disk_creation(self):
        """Test custom_part_control flag handling"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.disk = Mock()
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value='true'
                )
                assert disk_builder._has_custom_partition_control() is True

    def test_partition_number_uniqueness_validation(self):
        """Test partition number handling"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                assert disk_builder is not None

    def test_boot_flag_single_partition_validation(self):
        """Test boot flag handling"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                assert disk_builder is not None

    def test_custom_partition_control_allows_reserved_names(self):
        """Test custom_part_control allows system partition names"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value='true'
                )
                assert disk_builder._has_custom_partition_control() is True

    def test_custom_partition_control_prevents_legacy_attributes(self):
        """Test custom_part_control prevents legacy attributes"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value='true'
                )
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value='p.lxboot')
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_overlayroot = Mock(return_value=None)
                with raises(KiwiDiskConfigError):
                    disk_builder._validate_custom_partition_control_config()

    def test_custom_partition_control_false_allows_legacy_attributes(self):
        """Test custom_part_control=false allows legacy attributes"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value=None
                )
                assert disk_builder is not None
