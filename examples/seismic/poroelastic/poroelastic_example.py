import numpy as np
from argparse import ArgumentParser

from devito.logger import info
from examples.seismic.poroelastic import PoroelasticWaveSolver, demo_model
from examples.seismic import AcquisitionGeometry


def poroelastic_setup(shape=(50, 50), spacing=(15.0, 15.0), tn=500., num=200, space_order=4, nbpml=10,
                  constant=False, **kwargs):

    nrec = 2*shape[0]
    preset = 'constant-poroelastic' if constant else 'layers-poroelastic'
    model = demo_model(preset, space_order=space_order, shape=shape, nbpml=nbpml,
                       dtype=kwargs.pop('dtype', np.float32), spacing=spacing)

    # Source and receiver geometries
    src_coordinates = np.empty((1, len(spacing)))
    src_coordinates[0, :] = np.array(model.domain_size) * .5
    if len(shape) > 1:
        src_coordinates[0, -1] = model.origin[-1] + 2 * spacing[-1]

    rec_coordinates = np.empty((nrec, len(spacing)))
    rec_coordinates[:, 0] = np.linspace(0., model.domain_size[0], num=nrec)
    if len(shape) > 1:
        rec_coordinates[:, 1] = np.array(model.domain_size)[1] * .5
        rec_coordinates[:, -1] = model.origin[-1] + 2 * spacing[-1]
        # Source frequency is in Hz
    geometry = AcquisitionGeometry(model, rec_coordinates, src_coordinates,
                                   t0=0.0, tn=tn, src_type='Ricker', f0=40)

    # Create solver object to provide relevant operators
    solver = PoroelasticWaveSolver(model, geometry, space_order=space_order, **kwargs)
    return solver


def run(shape=(50, 50), spacing=(20.0, 20.0), tn=1000.0, num=200,
        space_order=4, nbpml=40, autotune=False, constant=False, **kwargs):

    solver = poroelastic_setup(shape=shape, spacing=spacing, nbpml=nbpml, tn=tn,
                           num=num, space_order=space_order, constant=constant, **kwargs)
    info("Applying Forward")
    # Define receiver geometry (spread across x, just below surface)
    rec1, rec2, vx, vz, qx, qz, txx, tzz, txz, p, summary = solver.forward(autotune=autotune)

    # iPython debug option    
    #import matplotlib.pyplot as plt    
    #from IPython import embed;embed()
    return rec1, rec2, vx, vz, qx, qz, txx, tzz, txz, p, summary


if __name__ == "__main__":
    description = ("Example script for a set of poroelastic operators.")
    parser = ArgumentParser(description=description)
    parser.add_argument('--2d', dest='dim2', default=True, action='store_true',
                        help="Preset to determine the physical problem setup")
    parser.add_argument('-a', '--autotune', default=False, action='store_true',
                        help="Enable autotuning for block sizes")
    parser.add_argument("-so", "--space_order", default=4,
                        type=int, help="Space order of the simulation")
    parser.add_argument("--nbpml", default=40,
                        type=int, help="Number of PML layers around the domain")
    parser.add_argument("-dse", default="advanced",
                        choices=["noop", "basic", "advanced",
                                 "speculative", "aggressive"],
                        help="Devito symbolic engine (DSE) mode")
    parser.add_argument("-dle", default="advanced",
                        choices=["noop", "advanced", "speculative"],
                        help="Devito loop engine (DLEE) mode")
    parser.add_argument("--constant", default=True, action='store_true',
                        help="Constant velocity model, default is a constant velocity model")
    args = parser.parse_args()

    # 2D preset parameters
    if args.dim2:
        shape = (251, 641)
        spacing = (0.5, 0.5)
        num = 800
        dt = 1.0e-4
        tn = 0.05 #(num-1)*dt
    # 3D preset parameters
    else:
        shape = (150, 150, 150)
        spacing = (10.0, 10.0, 10.0)
        tn = 1250.0

    run(shape=shape, spacing=spacing, nbpml=args.nbpml, tn=tn, num=num, dle=args.dle,
        space_order=args.space_order, autotune=args.autotune, constant=args.constant,
        dse=args.dse)
