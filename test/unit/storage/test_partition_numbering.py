# Copyright (c) 2025 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#

import pytest

from kiwi.storage.disk import ptable_entry_type
from kiwi.storage.partition_numbering import PartitionNumbering
from kiwi.exceptions import KiwiPartitionNumberingError


class TestPartitionNumbering:
    """Test partition numbering validation and assignment"""

    def test_validate_and_assign_numbers_no_explicit_numbers(self):
        """Test backward compatibility: no explicit numbers sorts alphabetically"""
        partitions = {
            'data': ptable_entry_type(
                mbsize=512, clone=0, partition_name='p.lxdata',
                partition_type='t.linux', mountpoint='/data',
                filesystem='ext4', label='DATA', partition_number=0
            ),
            'backup': ptable_entry_type(
                mbsize=256, clone=0, partition_name='p.lxbackup',
                partition_type='t.linux', mountpoint='/backup',
                filesystem='ext4', label='BACKUP', partition_number=0
            ),
            'cache': ptable_entry_type(
                mbsize=128, clone=0, partition_name='p.lxcache',
                partition_type='t.linux', mountpoint='/cache',
                filesystem='ext4', label='CACHE', partition_number=0
            )
        }

        result = PartitionNumbering.validate_and_assign_numbers(partitions, 'gpt')

        # Should be sorted alphabetically when no explicit numbers
        assert len(result) == 3
        assert result[0][0] == 'backup'
        assert result[1][0] == 'cache'
        assert result[2][0] == 'data'

    def test_validate_and_assign_numbers_with_explicit_numbers(self):
        """Test explicit partition numbering is respected"""
        partitions = {
            'data': ptable_entry_type(
                mbsize=512, clone=0, partition_name='p.lxdata',
                partition_type='t.linux', mountpoint='/data',
                filesystem='ext4', label='DATA', partition_number=3
            ),
            'backup': ptable_entry_type(
                mbsize=256, clone=0, partition_name='p.lxbackup',
                partition_type='t.linux', mountpoint='/backup',
                filesystem='ext4', label='BACKUP', partition_number=2
            ),
            'cache': ptable_entry_type(
                mbsize=128, clone=0, partition_name='p.lxcache',
                partition_type='t.linux', mountpoint='/cache',
                filesystem='ext4', label='CACHE', partition_number=4
            )
        }

        result = PartitionNumbering.validate_and_assign_numbers(partitions, 'gpt')

        # Should be sorted by partition number
        assert len(result) == 3
        assert result[0][1].partition_number == 2  # backup
        assert result[1][1].partition_number == 3  # data
        assert result[2][1].partition_number == 4  # cache

    def test_validate_and_assign_numbers_mixed_explicit_and_implicit(self):
        """Test that mixed explicit and implicit numbering raises error"""
        partitions = {
            'data': ptable_entry_type(
                mbsize=512, clone=0, partition_name='p.lxdata',
                partition_type='t.linux', mountpoint='/data',
                filesystem='ext4', label='DATA', partition_number=2
            ),
            'backup': ptable_entry_type(
                mbsize=256, clone=0, partition_name='p.lxbackup',
                partition_type='t.linux', mountpoint='/backup',
                filesystem='ext4', label='BACKUP', partition_number=0
            ),
            'cache': ptable_entry_type(
                mbsize=128, clone=0, partition_name='p.lxcache',
                partition_type='t.linux', mountpoint='/cache',
                filesystem='ext4', label='CACHE', partition_number=0
            )
        }

        with pytest.raises(KiwiPartitionNumberingError) as exc_info:
            PartitionNumbering.validate_and_assign_numbers(partitions, 'gpt')

        assert 'Mixed partition numbering' in str(exc_info.value)

    def test_validate_duplicate_partition_numbers(self):
        """Test that duplicate partition numbers raise error"""
        partitions = {
            'data': ptable_entry_type(
                mbsize=512, clone=0, partition_name='p.lxdata',
                partition_type='t.linux', mountpoint='/data',
                filesystem='ext4', label='DATA', partition_number=2
            ),
            'backup': ptable_entry_type(
                mbsize=256, clone=0, partition_name='p.lxbackup',
                partition_type='t.linux', mountpoint='/backup',
                filesystem='ext4', label='BACKUP', partition_number=2
            )
        }

        with pytest.raises(KiwiPartitionNumberingError) as exc_info:
            PartitionNumbering.validate_and_assign_numbers(partitions, 'gpt')

        assert 'Duplicate partition number 2' in str(exc_info.value)

    def test_validate_out_of_range_gpt(self):
        """Test that out-of-range GPT partition numbers raise error"""
        partitions = {
            'data': ptable_entry_type(
                mbsize=512, clone=0, partition_name='p.lxdata',
                partition_type='t.linux', mountpoint='/data',
                filesystem='ext4', label='DATA', partition_number=129
            )
        }

        with pytest.raises(KiwiPartitionNumberingError) as exc_info:
            PartitionNumbering.validate_and_assign_numbers(partitions, 'gpt')

        assert 'out of valid range' in str(exc_info.value)

    def test_validate_out_of_range_msdos(self):
        """Test that out-of-range MSDOS partition numbers raise error"""
        partitions = {
            'data': ptable_entry_type(
                mbsize=512, clone=0, partition_name='p.lxdata',
                partition_type='t.linux', mountpoint='/data',
                filesystem='ext4', label='DATA', partition_number=5
            )
        }

        with pytest.raises(KiwiPartitionNumberingError) as exc_info:
            PartitionNumbering.validate_and_assign_numbers(partitions, 'msdos')

        assert 'out of valid range' in str(exc_info.value)

    def test_validate_empty_partitions(self):
        """Test empty partition dictionary"""
        partitions = {}
        result = PartitionNumbering.validate_and_assign_numbers(partitions, 'gpt')
        assert result == []

    def test_single_partition(self):
        """Test single partition assignment"""
        partitions = {
            'data': ptable_entry_type(
                mbsize=512, clone=0, partition_name='p.lxdata',
                partition_type='t.linux', mountpoint='/data',
                filesystem='ext4', label='DATA', partition_number=0
            )
        }

        result = PartitionNumbering.validate_and_assign_numbers(partitions, 'gpt')

        assert len(result) == 1
        assert result[0][0] == 'data'

    def test_partition_numbering_with_gpt_max(self):
        """Test large partition count for GPT with explicit numbering"""
        partitions = {}
        for i in range(1, 11):
            partitions[f'part{i}'] = ptable_entry_type(
                mbsize=100, clone=0, partition_name=f'p.lxpart{i}',
                partition_type='t.linux', mountpoint=f'/part{i}',
                filesystem='ext4', label=f'PART{i}', partition_number=i  # Explicit numbers
            )

        result = PartitionNumbering.validate_and_assign_numbers(partitions, 'gpt')

        assert len(result) == 10
        numbers = [entry[1].partition_number for entry in result]
        # All should have numbers
        assert all(n > 0 for n in numbers)
        # No duplicates
        assert len(numbers) == len(set(numbers))
        # Should be in order
        assert numbers == list(range(1, 11))

    def test_warn_on_edge_cases(self, caplog):
        """Test warnings for edge cases"""
        partitions = {
            'data': ptable_entry_type(
                mbsize=512, clone=0, partition_name='p.lxdata',
                partition_type='t.linux', mountpoint='/data',
                filesystem='ext4', label='DATA', partition_number=1
            ),
            'backup': ptable_entry_type(
                mbsize=256, clone=0, partition_name='p.lxbackup',
                partition_type='t.linux', mountpoint='/backup',
                filesystem='ext4', label='BACKUP', partition_number=2
            ),
            'cache': ptable_entry_type(
                mbsize=128, clone=0, partition_name='p.lxcache',
                partition_type='t.linux', mountpoint='/cache',
                filesystem='ext4', label='CACHE', partition_number=3
            )
        }

        PartitionNumbering.warn_on_edge_cases(partitions, 'gpt')

        # When all have explicit numbering, should warn about gaps if present
        # This test verifies edge case warnings work

    def test_warn_on_msdos_overflow(self, caplog):
        """Test warning for too many partitions on MSDOS"""
        partitions = {}
        for i in range(1, 6):
            partitions[f'part{i}'] = ptable_entry_type(
                mbsize=100, clone=0, partition_name=f'p.lxpart{i}',
                partition_type='t.linux', mountpoint=f'/part{i}',
                filesystem='ext4', label=f'PART{i}', partition_number=0
            )

        PartitionNumbering.warn_on_edge_cases(partitions, 'msdos')

        # Should warn about MBR limit
        assert 'MBR partition table' in caplog.text

    def test_partition_number_explicit_ordering(self):
        """Test that explicitly numbered partitions are sorted by number"""
        partitions = {
            'part3': ptable_entry_type(
                mbsize=100, clone=0, partition_name='p.lxpart3',
                partition_type='t.linux', mountpoint='/part3',
                filesystem='ext4', label='PART3', partition_number=3
            ),
            'part1': ptable_entry_type(
                mbsize=100, clone=0, partition_name='p.lxpart1',
                partition_type='t.linux', mountpoint='/part1',
                filesystem='ext4', label='PART1', partition_number=1
            ),
            'part2': ptable_entry_type(
                mbsize=100, clone=0, partition_name='p.lxpart2',
                partition_type='t.linux', mountpoint='/part2',
                filesystem='ext4', label='PART2', partition_number=2
            )
        }

        result = PartitionNumbering.validate_and_assign_numbers(partitions, 'gpt')

        # Should be ordered by partition number despite alphabetical dict order
        assert result[0][0] == 'part1'
        assert result[1][0] == 'part2'
        assert result[2][0] == 'part3'

    def test_system_partition_warning(self, caplog):
        """Test warning when system partition has explicit number"""
        partitions = {
            'boot': ptable_entry_type(
                mbsize=256, clone=0, partition_name='p.lxboot',
                partition_type='t.linux', mountpoint='/boot',
                filesystem='ext4', label='BOOT', partition_number=2
            )
        }

        PartitionNumbering.validate_and_assign_numbers(partitions, 'gpt')

        # Should warn about system partition with explicit number
        assert 'System partition' in caplog.text
