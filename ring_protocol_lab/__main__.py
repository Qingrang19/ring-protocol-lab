"""Run with python -m ring_protocol_lab."""
import argparse
import csv
import io
import json
import sys
from dataclasses import asdict
from pathlib import Path
from .protocol import Config, FIELDS, generate, validate
from .svg import render


def main(argv=None):
    parser = argparse.ArgumentParser(description='Plan and inspect deterministic EIT electrode-ring protocols.')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('generate', 'svg', 'validate'):
        p = sub.add_parser(command)
        p.add_argument('-n', '--electrodes', type=int, default=16)
        p.add_argument('--drive-step', type=int, default=1, help='clockwise electrode distance: 1=adjacent, 2=skip one')
        p.add_argument('--index-base', type=int, choices=(0, 1), required=True)
        if command == 'generate':
            p.add_argument('--format', choices=('json', 'csv'), default='json')
        if command == 'svg':
            p.add_argument('--excitation', type=int, required=True)
        if command == 'validate':
            p.add_argument('input', type=Path)
        else:
            p.add_argument('-o', '--output', type=Path, help='default: stdout; existing files are replaced')
    args = parser.parse_args(argv)
    try:
        config = Config(args.electrodes, args.drive_step, args.index_base)
        if args.command == 'validate':
            data = json.loads(args.input.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or data.get('schema') != 'ring-protocol-lab/v1':
                raise ValueError('expected a ring-protocol-lab/v1 JSON document')
            saved_config = data.get('config')
            if (not isinstance(saved_config, dict)
                    or set(saved_config) != set(asdict(config))
                    or any(type(value) is not int for value in saved_config.values())
                    or saved_config != asdict(config)):
                raise ValueError('JSON config differs from command-line configuration')
            count = validate(data.get('rows'), config)
            print(f'Valid: {count} rows, {config.electrodes} excitations')
            return 0
        if args.command == 'svg':
            output = render(config, args.excitation)
        else:
            rows = generate(config)
            if args.format == 'json':
                output = json.dumps(dict(schema='ring-protocol-lab/v1', config=asdict(config), rows=rows), indent=2) + '\n'
            else:
                buffer = io.StringIO(newline='')
                writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator='\n')
                writer.writeheader(); writer.writerows(rows)
                output = buffer.getvalue()
        if args.output:
            args.output.write_text(output, encoding='utf-8')
        else:
            sys.stdout.write(output)
        return 0
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
