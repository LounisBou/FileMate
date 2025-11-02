#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Fixtures and configuration for pytest. """
import os
import sys

# Ensure src/ is on sys.path for imports in tests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
