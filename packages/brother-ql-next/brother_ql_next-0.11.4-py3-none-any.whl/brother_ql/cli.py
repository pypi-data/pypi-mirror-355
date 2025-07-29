#!/usr/bin/env python3

# Python standard library
from __future__ import print_function
import logging
import base64
import sys

# external dependencies
import click
import jsons

# imports from this very package
from brother_ql.models import ModelsManager
from brother_ql.labels import LabelsManager
from brother_ql.backends import available_backends


logger = logging.getLogger('brother_ql')


printer_help = "The identifier for the printer. This could be a string like tcp://192.168.1.21:9100 for a networked printer or usb://0x04f9:0x2015/000M6Z401370 for a printer connected via USB."
@click.group()
@click.option('-b', '--backend', type=click.Choice(available_backends), envvar='BROTHER_QL_BACKEND')
@click.option('-m', '--model', type=click.Choice(ModelsManager().identifiers()), envvar='BROTHER_QL_MODEL')
@click.option('-p', '--printer', metavar='PRINTER_IDENTIFIER', envvar='BROTHER_QL_PRINTER', help=printer_help)
@click.option('--debug', is_flag=True)
@click.version_option()
@click.pass_context
def cli(ctx: click.Context, *args, **kwargs):
    """ Command line interface for the brother_ql Python package. """

    backend = kwargs.get('backend')
    model = kwargs.get('model')
    printer = kwargs.get('printer')
    debug = kwargs.get('debug')

    # Store the general CLI options in the context meta dictionary.
    # The name corresponds to the second half of the respective envvar.
    #
    # Setting a dict value to None is distinct from not setting it at all
    # If we set it to None, get(val, default) will return None instead of default
    if model is not None: ctx.meta['MODEL'] = model
    if backend is not None: ctx.meta['BACKEND'] = backend
    if printer is not None: ctx.meta['PRINTER'] = printer

    logging.basicConfig(level='DEBUG' if debug else 'INFO')

@cli.command()
@click.pass_context
def discover(ctx: click.Context):
    """ find connected label printers """
    backend = ctx.meta.get('BACKEND', 'pyusb')
    discover_and_list_available_devices(backend)

def discover_and_list_available_devices(backend):
    from brother_ql.backends.helpers import discover
    available_devices = discover(backend_identifier=backend)
    from brother_ql.output_helpers import log_discovered_devices, textual_description_discovered_devices
    log_discovered_devices(available_devices)
    print(textual_description_discovered_devices(available_devices))

@cli.group()
@click.pass_context
def info(ctx: click.Context, *args, **kwargs):
    """ list available labels, models etc. """

@info.command(name='models')
@click.option("--json", is_flag=True)
@click.pass_context
def models_cmd(ctx: click.Context, *args, **kwargs):
    """
    List the choices for --model
    """
    if kwargs["json"]:
        import brother_ql.models as new_models
        print(jsons.dumps(new_models.ALL_MODELS))
    else:
        print('Supported models:')
        for model in ModelsManager().identifiers(): print(" " + model)

@info.command()
@click.option("--json", is_flag=True)
@click.pass_context
def labels(ctx: click.Context, *args, **kwargs):
    """
    List the choices for --label
    """
    if kwargs["json"]:
        import brother_ql.labels as new_labels
        print(jsons.dumps(new_labels.ALL_LABELS))
    else:
        from brother_ql.output_helpers import textual_label_description
        print(textual_label_description(LabelsManager().identifiers()))

@info.command()
@click.pass_context
def env(ctx: click.Context, *args, **kwargs):
    """
    print debug info about running environment
    """
    import sys, platform, os, shutil
    from pkg_resources import get_distribution, working_set
    print("\n##################\n")
    print("Information about the running environment of brother_ql.")
    print("(Please provide this information when reporting any issue.)\n")
    # computer
    print("About the computer:")
    for attr in ('platform', 'processor', 'release', 'system', 'machine', 'architecture'):
        print('  * '+attr.title()+':', getattr(platform, attr)())
    # Python
    print("About the installed Python version:")
    py_version = str(sys.version).replace('\n', ' ')
    print("  *", py_version)
    # brother_ql
    print("About the brother_ql package:")
    pkg = get_distribution('brother_ql')
    print("  * package location:", pkg.location)
    print("  * package version: ", pkg.version)
    try:
        cli_loc = shutil.which('brother_ql')
    except:
        cli_loc = 'unknown'
    print("  * brother_ql CLI path:", cli_loc)
    # brother_ql's requirements
    print("About the requirements of brother_ql:")
    fmt = "  {req:14s} | {spec:10s} | {ins_vers:17s}"
    print(fmt.format(req='requirement', spec='requested', ins_vers='installed version'))
    print(fmt.format(req='-' * 14, spec='-'*10, ins_vers='-'*17))
    requirements = list(pkg.requires())
    requirements.sort(key=lambda x: x.project_name)
    for req in requirements:
        proj = req.project_name
        req_pkg = get_distribution(proj)
        spec = ' '.join(req.specs[0]) if req.specs else 'any'
        print(fmt.format(req=proj, spec=spec, ins_vers=req_pkg.version))
    print("\n##################\n")

@cli.command('status', short_help='request status information from the printer')
@click.option('-f', '--format', type=click.Choice(('default', 'json', 'raw_bytes', 'raw_base64', 'raw_hex')), default='default', help='Output Format.')
@click.pass_context
def status_cmd(ctx: click.Context, *args, **kwargs):
    """ Prints status information from the chosen printer """
    from brother_ql.backends.helpers import status as status_fn
    try:
        status, raw = status_fn(printer_model=ctx.meta.get('MODEL'), printer_identifier=ctx.meta.get('PRINTER'), backend_identifier=ctx.meta.get('BACKEND'))
    except NotImplementedError as _:
        quit(1)

    # This should be a match, however, Python 3.9 support
    if kwargs["format"] == 'default':
        print("Printer Status:")
        print(f"* Status Type: {status['status_type']}")
        print(f"* Phase Type: {status['phase_type']}")
        print(f"* Model: {status['model_name']}")
        if status['identified_media'] is not None:
            print(f"* Identified Media: {status['identified_media'].name} (id: {status['identified_media'].identifier})")
        else:
            print(f"* Media Type: {status['media_type']}")
            print(f"* Media Width: {status['media_width']}")
            print(f"* Media Length: {status['media_length']}")
        if len(status["errors"]) > 0:
            print(f"* Errors: {status['media_length']}")
            for e in status["errors"]:
                print(f"  + {e}")
    elif kwargs["format"] == 'json':
        print(jsons.dumps(status))
    elif kwargs["format"] == 'raw_bytes':
        sys.stdout.buffer.write(raw)
    elif kwargs["format"] == 'raw_base64':
        sys.stdout.buffer.write(base64.encodebytes(raw))
    elif kwargs["format"] == 'raw_hex':
        print(raw.hex())

@cli.command('print', short_help='print a label')
@click.argument('images', nargs=-1, type=click.File('rb'), metavar='IMAGE [IMAGE] ...')
@click.option('-l', '--label', type=click.Choice(LabelsManager().identifiers()), envvar='BROTHER_QL_LABEL', help='The label (size, type - die-cut or endless). Run `brother_ql info labels` for a full list including ideal pixel dimensions.')
@click.option('-r', '--rotate', type=click.Choice(('auto', '0', '90', '180', '270')), default='auto', help='Rotate the image (counterclock-wise) by this amount of degrees.')
@click.option('-t', '--threshold', type=float, default=70.0, help='The threshold value (in percent) to discriminate between black and white pixels.')
@click.option('-d', '--dither', is_flag=True, help='Enable dithering when converting the image to b/w. If set, --threshold is meaningless.')
@click.option('-c', '--compress', is_flag=True, help='Enable compression (if available with the model). Label creation can take slightly longer but the resulting instruction size is normally considerably smaller.')
@click.option('--red', is_flag=True, help='Create a label to be printed on black/red/white tape (only with QL-8xx series on DK-22251 labels). You must use this option when printing on black/red tape, even when not printing red.')
@click.option('--600dpi', 'dpi_600', is_flag=True, help='Print with 600x300 dpi available on some models. Provide your image as 600x600 dpi; perpendicular to the feeding the image will be resized to 300dpi.')
@click.option('--lq', is_flag=True, help='Print with low quality (faster). Default is high quality.')
@click.option('--no-cut', is_flag=True, help="Don't cut the tape after printing the label.")
@click.pass_context
def print_cmd(ctx: click.Context, *args, **kwargs):
    """ Print a label of the provided IMAGE. """
    backend = ctx.meta.get('BACKEND')
    model = ctx.meta.get('MODEL')
    printer = ctx.meta.get('PRINTER')
    from brother_ql.conversion import convert
    from brother_ql.backends.helpers import send
    from brother_ql.raster import BrotherQLRaster
    qlr = BrotherQLRaster(model)
    qlr.exception_on_warning = True
    kwargs['cut'] = not kwargs['no_cut']
    del kwargs['no_cut']
    instructions = convert(qlr=qlr, **kwargs)
    send(instructions=instructions, printer_identifier=printer, backend_identifier=backend, blocking=True)

@cli.command(name='analyze', help='interpret a binary file containing raster instructions for the Brother QL-Series printers')
@click.argument('instructions', type=click.File('rb'))
@click.option('-f', '--filename-format', help="Filename format string. Default is: label{counter:04d}.png.")
@click.pass_context
def analyze_cmd(ctx: click.Context, *args, **kwargs):
    """ Interprets a binary file containing raster instructions for Brother QL-Series printers """
    from brother_ql.reader import BrotherQLReader
    reader = BrotherQLReader(kwargs['instructions'])
    filename_format = kwargs.get('filename_format')
    if filename_format is not None:
        reader.filename_fmt = filename_format
    reader.analyse()

@cli.command(name='send', short_help='send an instruction file to the printer')
@click.argument('instructions', type=click.File('rb'))
@click.pass_context
def send_cmd(ctx: click.Context, *args, **kwargs):
    """ Sends a raw instructions file to the printer """
    from brother_ql.backends.helpers import send
    send(instructions=kwargs['instructions'].read(), printer_identifier=ctx.meta.get('PRINTER'), backend_identifier=ctx.meta.get('BACKEND'), blocking=True)

if __name__ == '__main__':
    cli()
