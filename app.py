#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entry point for iNaturalist -> MykIS GUI."""

# NACHHER:
from src.gui import App


def main() -> int:
    try:
        App().mainloop()
        return 0
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
