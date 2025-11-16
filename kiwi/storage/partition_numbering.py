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

import logging
from typing import Dict, List, Tuple

from kiwi.exceptions import KiwiPartitionNumberingError
from kiwi.storage.disk import ptable_entry_type

log = logging.getLogger('kiwi')


class PartitionNumbering:
    """
    **Handles intelligent partition numbering and validation**

    This class provides functionality to:
    - Validate partition number configurations
    - Auto-assign partition numbers when not explicitly specified
    - Detect conflicts (duplicate numbers, invalid ranges)
    - Warn about edge cases and impossible configurations
    - Sort partitions respecting user-specified numbers
    """

    @staticmethod
    def validate_and_assign_numbers(
        partitions: Dict[str, ptable_entry_type],
        label_type: str = 'gpt'
    ) -> List[Tuple[str, ptable_entry_type]]:
        """
        Validate partition numbering and return sorted partition list.

        If no explicit numbers are specified, maintains alphabetical order
        (backward compatibility). If some or all partitions have explicit
        numbers, respects those and auto-assigns remaining numbers.

        :param partitions: Dictionary of partition_name -> ptable_entry_type
        :param label_type: Partition table type ('gpt' or 'msdos')
        :return: List of (partition_name, ptable_entry_type) tuples sorted by number
        :raises KiwiPartitionNumberingError: If invalid numbering configuration
        """
        if not partitions:
            return []

        # Check if any partition has explicit numbering
        has_explicit_numbers = any(
            entry.partition_number > 0 for entry in partitions.values()
        )

        if not has_explicit_numbers:
            # Backward compatibility: sort alphabetically
            return sorted(
                partitions.items(),
                key=lambda x: x[0]
            )

        # Validate explicit numbers and prepare assignment
        return PartitionNumbering._assign_with_validation(
            partitions, label_type
        )

    @staticmethod
    def _assign_with_validation(
        partitions: Dict[str, ptable_entry_type],
        label_type: str
    ) -> List[Tuple[str, ptable_entry_type]]:
        """
        Assign partition numbers with validation when explicit numbers exist.

        All partitions must either have explicit numbers OR have no explicit numbers.
        Mixed explicit and implicit numbering is not allowed.

        :param partitions: Dictionary of partition configurations
        :param label_type: Partition table type ('gpt' or 'msdos')
        :return: Sorted list of (name, config) tuples
        :raises KiwiPartitionNumberingError: On validation failure
        """
        # Separate partitions with explicit vs implicit numbers
        explicit_nums: Dict[int, str] = {}
        implicit_partitions: List[str] = []
        duplicate_numbers: Dict[int, List[str]] = {}

        for name, entry in partitions.items():
            if entry.partition_number > 0:
                if entry.partition_number in explicit_nums:
                    # Track duplicate
                    if entry.partition_number not in duplicate_numbers:
                        duplicate_numbers[entry.partition_number] = [
                            explicit_nums[entry.partition_number]
                        ]
                    duplicate_numbers[entry.partition_number].append(name)
                else:
                    explicit_nums[entry.partition_number] = name
            else:
                implicit_partitions.append(name)

        # Check for duplicates first
        if duplicate_numbers:
            for num, names in duplicate_numbers.items():
                log.error(
                    f'Duplicate partition number {num}: '
                    f'assigned to {", ".join(names)}'
                )
                raise KiwiPartitionNumberingError(
                    f'Duplicate partition number {num}: '
                    f'assigned to {", ".join(names)}'
                )

        # Check for mixed explicit/implicit numbering
        if explicit_nums and implicit_partitions:
            explicit_names = list(explicit_nums.values())
            log.error(
                f'Mixed partition numbering not allowed: '
                f'{", ".join(explicit_names)} have explicit numbers, but '
                f'{", ".join(implicit_partitions)} do not. '
                f'All partitions must specify numbers or none at all.'
            )
            raise KiwiPartitionNumberingError(
                f'Mixed partition numbering not allowed: '
                f'Either all partitions must have explicit numbers or none at all.'
            )

        # Validate explicit numbers
        PartitionNumbering._validate_explicit_numbers(
            explicit_nums, label_type, partitions
        )

        # Sort by assigned partition number
        result = []
        for name in sorted(partitions.keys()):
            result.append((name, partitions[name]))

        result.sort(
            key=lambda x: x[1].partition_number if x[1].partition_number > 0 else float('inf')
        )

        return result

    @staticmethod
    def _validate_explicit_numbers(
        explicit_nums: Dict[int, str],
        label_type: str,
        partitions: Dict[str, ptable_entry_type]
    ) -> None:
        """
        Validate explicit partition number assignments.

        Checks for:
        - Duplicate partition numbers
        - Out-of-range numbers for the label type
        - Reserved partition numbers (for system partitions)

        :param explicit_nums: Map of number -> partition_name
        :param label_type: Partition table type
        :param partitions: All partition configurations
        :raises KiwiPartitionNumberingError: If validation fails
        """
        # Validate range based on label type
        if label_type == 'gpt':
            max_num = 128
        elif label_type == 'msdos':
            max_num = 4
        else:
            max_num = 128

        for num, name in explicit_nums.items():
            if num < 1 or num > max_num:
                log.error(
                    f'Partition {name} assigned invalid number {num} '
                    f'(valid range: 1-{max_num} for {label_type})'
                )
                raise KiwiPartitionNumberingError(
                    f'Partition {name}: number {num} is out of valid range '
                    f'(1-{max_num}) for {label_type}'
                )

        # Warn about partitions that might need specific numbers
        reserved_names = {'root', 'boot', 'swap', 'efi', 'efi_csm', 'prep'}
        for num, name in explicit_nums.items():
            if name in reserved_names:
                log.warning(
                    f'System partition {name} has explicit number {num}. '
                    f'Ensure this does not conflict with required system partition layout.'
                )

    @staticmethod
    def warn_on_edge_cases(
        partitions: Dict[str, ptable_entry_type],
        label_type: str
    ) -> None:
        """
        Log warnings for edge cases in partition configuration.

        :param partitions: Dictionary of partition configurations
        :param label_type: Partition table type ('gpt' or 'msdos')
        """
        explicit_count = sum(
            1 for e in partitions.values() if e.partition_number > 0
        )
        implicit_count = len(partitions) - explicit_count

        if explicit_count > 0 and implicit_count > 0:
            log.info(
                f'Mixed partition numbering: {explicit_count} explicit, '
                f'{implicit_count} auto-assigned'
            )

        if label_type == 'msdos' and explicit_count + implicit_count > 4:
            log.warning(
                f'MBR partition table can only have 4 primary partitions, '
                f'but {explicit_count + implicit_count} configured. '
                f'Extended partitions may be required.'
            )

        # Check for gaps in explicit numbering
        explicit_nums = sorted(
            e.partition_number for e in partitions.values()
            if e.partition_number > 0
        )
        if len(explicit_nums) > 1:
            for i in range(len(explicit_nums) - 1):
                if explicit_nums[i + 1] - explicit_nums[i] > 1:
                    log.info(
                        f'Gap detected in partition numbering: '
                        f'{explicit_nums[i]} -> {explicit_nums[i + 1]}'
                    )
