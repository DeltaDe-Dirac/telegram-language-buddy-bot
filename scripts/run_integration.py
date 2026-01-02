import os
from dotenv import dotenv_values
import sys
import pytest

def main():
    env = dotenv_values(os.path.join(os.path.dirname(__file__), '..', '.env'))
    for k, v in env.items():
        if v is not None and k not in os.environ:
            os.environ[k] = v

    # Ensure RUN_INTEGRATION is set
    os.environ['RUN_INTEGRATION'] = os.environ.get('RUN_INTEGRATION', '1')

    # Run all integration tests
    rc = pytest.main(['-m', 'integration', '-q'])
    sys.exit(rc)

if __name__ == '__main__':
    main()
