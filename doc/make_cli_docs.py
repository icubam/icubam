from pathlib import Path
from glob import glob
import os
import subprocess
import textwrap

BASE_DIR = Path(__file__).resolve().parent


def main():
  """This function auto-generates a list of CLI commands and their help

  We manually create _generated/cli-api.rst file that will be included in
  the documentation.
  """
  print('# Generating CLI API')
  os.makedirs(BASE_DIR / '_generated', exist_ok=True)
  out = []
  for fname in sorted(glob(str(BASE_DIR.parent / 'scripts' / '*.py'))):
    fname = Path(fname)
    name = f'{fname.stem}'
    if name in [
      '__init__',
    ]:
      continue
    out.append(name)
    out.append('-' * len(name))
    try:
      res = subprocess.run(['python', str(fname.name), '--help'],
                           encoding='utf-8',
                           capture_output=True,
                           cwd=str(BASE_DIR.parent / 'scripts'))
    except subprocess.CalledProcessError:
      # calling --help on absl scripts produces a non zero exist
      # status.
      if res.returncode == 1:
        pass
      else:
        raise
    out.append('.. code-block:: text\n')
    out.append(textwrap.indent(str(res.stdout), ' ' * 8))
    print(f'- Processed {name}')
  with open(BASE_DIR / '_generated' / 'cli-api.rst', 'wt') as fh:
    fh.write('\n'.join(out))


if __name__ == '__main__':
  main()
