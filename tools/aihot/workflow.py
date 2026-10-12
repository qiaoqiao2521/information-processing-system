#!/usr/bin/env python3
"""Run the bounded information-processing workflow with the existing local CLI bridge."""
import sys
from local_mcode import main

if __name__ == '__main__':
    if '--workflow-next' not in sys.argv:
        sys.argv[1:1] = ['--workflow-next', '2']
    if '--max-calls' not in sys.argv:
        sys.argv[1:1] = ['--max-calls', '30']
    raise SystemExit(main(engine='opencode'))
