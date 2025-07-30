# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: MIT

PATTERN = r"(BADGIE\s+TIME|BADGIE\s+ME)"

PATTERN_START = r"<!--\s+" + PATTERN + r"\s+-->"

PATTERN_END = r"<!--\s+END\s+" + PATTERN + r"\s+-->"
