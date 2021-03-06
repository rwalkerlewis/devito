from devito import memoized_meth
from examples.seismic import Receiver
from examples.seismic.poroelastic.operators import (ForwardOperator, stress_fields,
                                                particle_velocity_fields,
                                                relative_velocity_fields,
                                                pressure_fields)



class PoroelasticWaveSolver(object):
    """
    Solver object that provides operators for seismic inversion problems
    and encapsulates the time and space discretization for a given problem
    setup.

    :param model: Physical model with domain parameters
    :param source: Sparse point symbol providing the injected wave
    :param receiver: Sparse point symbol describing an array of receivers
    :param space_order: Order of the spatial stencil discretisation (default: 4)

    Note: This is an experimental staggered grid poroelastic modeling kernel.
    Only 2D supported
    """
    def __init__(self, model, geometry, space_order=4, **kwargs):
        self.model = model
        self.geometry = geometry

        self.space_order = space_order
        # Time step can be \sqrt{3}=1.73 bigger with 4th order
        self.dt = self.model.critical_dt
        # Cache compiler options
        self._kwargs = kwargs

    @memoized_meth
    def op_fwd(self, save=None):
        """Cached operator for forward runs with buffered wavefield"""
        return ForwardOperator(self.model, save=save, geometry=self.geometry,
                               space_order=self.space_order, **self._kwargs)

    def forward(self, src=None, rec1=None, rec2=None, rhos=None, rhof=None, phi=None,
                     prm=None, fvs=None, kdr=None, ksg=None, kfl=None, shm=None,
                     T=None, vx=None, vz=None, qx=None, qz=None, txx=None, tzz=None,
                     txz=None, p=None, save=None, **kwargs):
        """
        Forward modelling function that creates the necessary
        data objects for running a forward modelling operator.

        :param src: (Optional) Symbol with time series data for the injected source term
        :param rec1: (Optional) Symbol to store interpolated (txx) receiver data
        :param rec2: (Optional) Symbol to store interpolated (tzz) receiver data
        :param vx: (Optional) Symbol to store the computed horizontal particle velocity
        :param vz: (Optional) Symbol to store the computed vertical particle velocity
        :param qx: (Optional) Symbol to store the computed horizontal relative velocity        
        :param qz: (Optional) Symbol to store the computed vertical relative velocity        
        :param txx: (Optional) Symbol to store the computed horizontal stress
        :param tzz: (Optional) Symbol to store the computed vertical stress
        :param txz: (Optional) Symbol to store the computed diagonal stresss
        :param p: (Optional) Symbol to store the computed pore pressure        
        :param vp: (Optional) Symbol for the time-constant P-wave velocity (km/s)
        :param vs: (Optional) Symbol for the time-constant S-wave velocity (km/s)
        :param vs: (Optional) Symbol for the time-constant density (rho=1 for water)
        :param save: Option to store the entire (unrolled) wavefield

        :returns: Rec1 (txx), Rec2 (tzz), particle velocities vx and vz, stress txx,
                  tzz and txz and performance summary
        """
        # Source term is read-only, so re-use the default
        src = src or self.geometry.src
        # Create a new receiver object to store the result
        rec1 = rec1 or Receiver(name='rec1', grid=self.model.grid,
                                time_range=self.geometry.time_axis,
                                coordinates=self.geometry.rec_positions)
        rec2 = rec2 or Receiver(name='rec2', grid=self.model.grid,
                                time_range=self.geometry.time_axis,
                                coordinates=self.geometry.rec_positions)

        # Create all the fields; vx, vz, wx, wz, tau_xx, tau_zz, tau_xz, p
        save_t = src.nt if save else None

        vx, vy, vz = particle_velocity_fields(self.model, save_t, self.space_order)
        qx, qy, qz = relative_velocity_fields(self.model, save_t, self.space_order)
        txx, tyy, tzz, txy, txz, tyz = stress_fields(self.model, save_t, self.space_order)
        p = pressure_fields(self.model, save_t, self.space_order)

        kwargs['vx'] = vx
        kwargs['vz'] = vz
        kwargs['qx'] = qx
        kwargs['qz'] = qz        
        kwargs['txx'] = txx
        kwargs['tzz'] = tzz
        kwargs['txz'] = txz
        kwargs['p'] = p        
        if self.model.grid.dim == 3:
            kwargs['vy'] = vy
            kwargs['tyy'] = tyy
            kwargs['txy'] = txy
            kwargs['tyz'] = tyz
        # Pick m from model unless explicitly provided
        # Pick m from model unless explicitly provided
        rhos = rhos or self.model.rhos
        rhof = rhof or self.model.rhof
        phi  = phi  or self.model.phi
        prm  = prm  or self.model.prm
        fvs  = fvs  or self.model.fvs
        kdr  = kdr  or self.model.kdr
        ksg  = ksg  or self.model.ksg
        kfl  = kfl  or self.model.kfl
        shm  = shm  or self.model.shm
        T    = T    or self.model.T

        # Execute operator and return wavefield and receiver data
#        summary = self.op_fwd(save).apply(src=src, rec1=rec1, rec2=rec2,
#        rho_s=rho_s, rho_f=rho_f, phi=phi, k=k, mu_f=mu_f, K_dr=K_dr, K_s=K_s,
#        K_f=K_f, G=G, T=T, dt=kwargs.pop('dt', self.dt), **kwargs)
        summary = self.op_fwd(save).apply(src=src, rec1=rec1, rec2=rec2,
        dt=kwargs.pop('dt', self.dt), **kwargs)


        return rec1, rec2, vx, vz, qx, qz, txx, tzz, txz, p, summary
        
