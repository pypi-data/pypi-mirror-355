import sys
import configargparse

from .__about__ import __version__
from .tools import (
    firmware,
    test,
    info,
    serial
)

__all__ = [
    "_main"
]

def _main():
    parser = configargparse.ArgParser(
        description="aj090-hw-tools.py v%s - AJ090 hardware tools"
        % __version__,
        prog="aj090-hw-tools",
    )

    parser.add_argument(
        "--port",
        "-p",
        help="Serial port device",
        env_var="AJ090_HW_PORT",
    )

    parser.add_argument('-c', '--config', is_config_file=True, help='config file path')

    parser.add_argument('device', type=str, choices=['cell', 'shelf'], help='device')

    subparsers = parser.add_subparsers(title='Device tools', dest='tools', help='Run aj090-hw-tools {device} {tool} -h for additional help')

    # Firmware operations
    parser_firmware = subparsers.add_parser('firmware', help='device firmware operations group')
    parser_firmware.set_defaults(func=firmware)
    parser_firmware.add_argument('operation', type=str, choices=['write', 'erase'], help='firmware operations')
    parser_firmware.add_argument('-f', '--bin_file', type=str, help='firmware bin file')

    # Info
    parser_info = subparsers.add_parser('info', help='device info')
    parser_info.set_defaults(func=info)

    # Test
    parser_test = subparsers.add_parser('test', help='device tests')
    parser_test.set_defaults(func=test)

    # Serial
    parser_serial = subparsers.add_parser('serial', help='device serial number operations')
    parser_serial.set_defaults(func=serial)
    parser_serial.add_argument('operation', type=str, choices=['write', 'read'], help='serial operations')
    parser_serial.add_argument('-s', '--serial', type=str, required='write' in sys.argv, help='serial number')

    # Factory
    # parser_factory = subparsers.add_parser('factory_mode', help='device factory mode control')

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(-1)

    args = parser.parse_args()

    try:
        return args.func(args)
    except KeyboardInterrupt:
        sys.exit(-1)
    
if __name__ == '__main__':
    try:
        sys.exit(_main())
    except Exception as ex:
        print(ex)
        sys.exit(-1)