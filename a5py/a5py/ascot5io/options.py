"""
Options IO.

File: options.py
"""
import h5py
import numpy as np
import textwrap
import copy

from . ascot5file import add_group, get_qid
from a5py.ascot5io.ascot5data import AscotData

def write_hdf5(fn, options, desc=None):
    """
    Write options.

    Unlike most other "write" functions, this one takes dictionary as an
    argument. The dictionary should have exactly the same format as given by
    the read_hdf5() or get_default() functions in this module.

    Args:
        fn : str <br>
            Full path to HDF5 file.
        options : dictionary <br>
            Options to be written in dictionary format.
        desc : str, optional <br>
            Description for this input.
    """

    parent = "options"
    group  = "opt"
    qid    = None

    with h5py.File(fn, "a") as f:
        g    = add_group(f, parent, group, desc=desc)
        name = g.name

        # Options might contain parameters unknown to default options
        for opt in options:
            if opt != "qid" and opt != "date" and opt != "description":
                data = options[opt]
                if type(data) is not np.array:
                    data = np.array(data)

                data =data.astype("f8")
                d = g.create_dataset(opt, (data.size,), data=data)

    return name


def read_hdf5(fn, qid, info=False):
    """
    Read options from HDF5 file.

    Args:
        fn : str <br>
            Full path to the HDF5 file.
        qid : str <br>
            qid of the options to be read.
        info : bool, optional <br>
            If true, default options are generated and the values read from HDF5
            are placed there so that parameter and its comments appear together
            in order they are defined in this module. If options contain
            parameters not found in default options, a "Unknown parameter"
            comment is used and they appear after known parameters.

    Returns:
        Dictionary containing options.
    """

    path = "options" + "/opt-" + qid

    # Read values from file
    with h5py.File(fn,"r") as f:
        out  = {}

        # Metadata.
        out["qid"]  = qid
        out["date"] = f[path].attrs["date"]
        out["description"] = f[path].attrs["description"]

        # Actual data.
        for opt in f[path]:
            out[opt]  = f[path][opt][:]

    if not info:
        return out

    # Parse
    defopt = get_default()
    info   = []
    for name in out:
        if name in ["qid", "date", "description"]:
            continue

        val = out[name]
        cmt = "Unknown parameter"
        for namecmtval in defopt:
            # A banner field
            if len(namecmtval) == 1 and (namecmtval[0],) not in info:
                info.append((namecmtval[0],))
                continue
            elif len(namecmtval) == 1:
                continue

            if name == namecmtval[0]:
                cmt = namecmtval[1]
                break

        info.append((name, cmt, val))

    # Sort
    unsorted = copy.deepcopy(info)

    i = 0
    for opt in defopt:
        for namecmtval in unsorted:
            if opt[0] == namecmtval[0]:
                info[i] = namecmtval
                i = i + 1
                break

    for namecmtval in unsorted:
        if len(namecmtval) > 1 and namecmtval[1] == "Unknown parameter":
            info[i] = namecmtval
            i = i + 1

    return out, info


def get_default():
    """
    Get default option parameters.

    Returns:
        A list containing default options in format (name, description, value).
        List is ordered and contains info banners as well (as tuples).
    """

    info = []

    info.append(("""\
    #**************************************************************************#
    #*                      SIMULATION MODE AND TIME-STEP                     *#
    #*                                                                        *#
    #**************************************************************************#
    """,))

    info.append(
        ("SIM_MODE",
         """\
         # Simulation mode (1, 2, 3, 4)
         # - 1 Gyro-orbit
         # - 2 Guiding center
         # - 3 Hybrid
         # - 4 Magnetic field lines
         """,
         3)
    )
    info.append(
        ("ENABLE_ADAPTIVE",
         """\
         # Use adaptive time-step (0, 1)
         # This option is used only if SIM_MODE = 2 or 3. Gyro-orbit
         # simulations are always done with fixed time-step and magnetic field line
         # simulations with adaptive time-step.
         # - 0 Use fixed time-step
         # - 1 Use adaptive time-step
         """,
         1)
    )
    info.append(
        ("RECORD_GO_AS_GC",
         """\
         # Record GOs as GCs in diagnostics (0, 1)
         # - 0 Record GOs as GOs
         # - 1 Record GOs as GCs
         """,
         0)
    )
    info.append(
        ("FIXEDSTEP_USE_USERDEFINED",
         """\
         # Define fixed time-step value explicitly (0,1)
         # Note: The adaptive scheme uses fixed time-step value as an initial step.
         # - 0 Calculate time-step from FIXEDSTEP_NSTEPS_PER_GYROTIME
         # - 1 Use opt.opt.FIXEDSTEP_USERDEFINED as a time-step
         """,
         0)
    )
    info.append(
        ("FIXEDSTEP_USERDEFINED",
         """\
         # User-defined time-step [s]
         """,
         1e-8)
    )
    info.append(
        ("FIXEDSTEP_NSTEPS_PER_GYROTIME",
         """\
         # Time-step is 2pi / ( gyrofrequency * N ) where N is this parameter
         """,
         20)
    )
    info.append(
        ("ADAPTIVE_TOL_ORBIT",
         """\
         # Relative error tolerance for orbit following in adaptive scheme
         """,
         1e-8)
    )
    info.append(
        ("ADAPTIVE_TOL_CCOL",
         """\
         # Relative error tolerance for Coulomb collisions in adaptive scheme
         """,
         1e-1)
    )
    info.append(
        ("ADAPTIVE_MAX_DRHO",
         """\
         # Maximum allowed change in rho during one time-step in adaptive scheme
         """,
         0.1)
    )
    info.append(
        ("ADAPTIVE_MAX_DPHI",
         """\
         # Maximum allowed change in phi during one time-step in adaptive scheme
         """,
         2)
    )

    info.append(("""\
    #**************************************************************************#
    #*                             END CONDITIONS                             *#
    #*                                                                        *#
    #**************************************************************************#
    """,))

    info.append(
        ("ENDCOND_SIMTIMELIM",
         """\
         # Terminate when marker's clock ("laboratory") time reaches a limit
         # The limit is set by ENDCOND_MAX_SIM_TIME
         """,
         1)
    )
    info.append(
        ("ENDCOND_CPUTIMELIM",
         """\
         # Terminate when marker's cpu time reaches a limit
         # The limit is set by ENDCOND_MAX_CPU_TIME
         """,
         1)
    )
    info.append(
        ("ENDCOND_RHOLIM",
         """\
         # Terminate if marker goes outside given rho boundaries
         # rho boundaries are defined by ENDCOND_MAX_RHO and ENDCOND_MAX_RHO.
         """,
         0)
    )
    info.append(
        ("ENDCOND_ENERGYLIM",
         """\
         # Terminate when marker energy is below a user-specified value
         # The user specified values are ENDCOND_MIN_ENERGY and
         # ENDCOND_MIN_ENERGY_TIMES_THERMAL. Marker is terminated when either
         # of these limits is reached.
         """,
         1)
    )
    info.append(
        ("ENDCOND_WALLHIT",
         """\
         # Terminate when marker impacts wall
         """,
         1)
    )
    info.append(
        ("ENDCOND_MAXORBS",
         """\
         # Terminate when marker has completed user-specified number of orbits
         # Limit ENDCOND_MAX_TOROIDALORBS is used for a number of toroidal
         # and ENDCOND_MAX_POLOIDALORBS for poloidal orbits. Marker is
         # terminated when either of these limits is reached.
         """,
         0)
    )
    info.append(
        ("ENDCOND_MAX_SIM_TIME",
         """\
         # Maximum simulation time [s]
         """,
         1)
    )
    info.append(
        ("ENDCOND_MAX_CPU_TIME",
         """\
         # Maximum cpu time [s]
         """,
         3600)
    )
    info.append(
        ("ENDCOND_MAX_RHO",
         """\
         # Maximum rho value
         """,
         2)
    )
    info.append(
        ("ENDCOND_MIN_RHO",
         """\
         # Minimum rho value
         """,
         0)
    )
    info.append(
        ("ENDCOND_MIN_ENERGY",
         """\
         # Minimum energy [eV]
         """,
         1e3)
    )
    info.append(
        ("ENDCOND_MIN_ENERGY_TIMES_THERMAL",
         """\
         # Minimum energy limit local electron thermal energy times this value
         """,
         2)
    )
    info.append(
        ("ENDCOND_MAX_TOROIDALORBS",
         """\
         # Maximum number of toroidal orbits
         """,
         100)
    )
    info.append(
        ("ENDCOND_MAX_POLOIDALORBS",
         """\
         # Maximum number of poloidal orbits
         """,
         100)
    )

    info.append(("""\
    #**************************************************************************#
    #*                               PHYSICS                                  *#
    #*                                                                        *#
    #**************************************************************************#
    """,))

    info.append(
        ("ENABLE_ORBIT_FOLLOWING",
         """\
         # Trace markers in an electromagnetic field
         """,
         1)
    )
    info.append(
        ("ENABLE_COULOMB_COLLISIONS",
         """\
         # Markers experience Coulomb collisions with background plasma
         """,
         1)
    )
    info.append(
        ("DISABLE_FIRSTORDER_GCTRANS",
         """\
         # Disable first order guiding center transformation in velocity space
         """,
         0)
    )
    info.append(
        ("DISABLE_ENERGY_CCOLL",
         """\
         # Disable guiding center energy collisions
         """,
         0)
    )
    info.append(
        ("DISABLE_PITCH_CCOLL",
         """\
         # Disable guiding center pitch collisions
         """,
         0)
    )
    info.append(
        ("DISABLE_GCDIFF_CCOLL",
         """\
         # Disable guiding center spatial diffusion
         """,
         0)
    )

    info.append(("""\
    #**************************************************************************#
    #*                            DISTRIBUTIONS                               *#
    #*                                                                        *#
    #**************************************************************************#
    """,))

    info.append(
        ("ENABLE_DIST_5D",
         """\
         # Collect distribution histogram in [R, phi, z, vpa, vpe, t, q]
         # The coordinates are
         #   - R   major radius
         #   - phi toroidal angle
         #   - z   z-coordinate
         #   - vpa velocity component parallel to magnetic field
         #   - vpe velocity component perpendicular to magnetic field
         #   - t   time
         #   - q   charge
         """,
         1)
    )
    info.append(
        ("ENABLE_DIST_6D",
         """\
         # Collect distribution histogram in [R, phi, z, vR, vphi, vz, t, q]
         # The coordinates are
         #    - R    major radius
         #    - phi  toroidal angle
         #    - z    z-coordinate
         #    - vR   velocity R-component
         #    - vphi velocity phi-component
         #    - vz   velocity z-component
         #    - t    time
         #    - q    charge
         """,
         1)
    )
    info.append(
        ("ENABLE_DIST_rho5D",
         """\
         # Collect distribution histogram in [rho, pol, phi, vpa, vpe, t, q]
         # The coordinates are
         #    - rho  flux surface
         #    - pol  poloidal angle
         #    - phi  toroidal angle
         #    - z    z-coordinate
         #    - vpa  velocity component parallel to magnetic field
         #    - vpe  velocity component perpendicular to magnetic field
         #    - t    time
         #    - q    charge
         """,
         1)
    )
    info.append(
        ("ENABLE_DIST_rho6D",
         """\
         # Collect distribution histogram in [rho, pol, phi, vR, vphi, vz, t, q]
         # The coordinates are
         #    - rho  flux surface
         #    - pol  poloidal angle
         #    - phi  toroidal angle
         #    - z    z-coordinate
         #    - vR   velocity R-component
         #    - vphi velocity phi-component
         #    - vz   velocity z-component
         #    - t    time
         #    - q    charge
         """,
         1)
    )
    info.append(
        ("DIST_MIN_R",
         """\
         # Minimum bin edge for major R coordinate [m]
         """,
         0.1)
    )
    info.append(
        ("DIST_MAX_R",
         """\
         # Maximum bin edge for R coordinate [m]
         """,
         10)
    )
    info.append(
        ("DIST_NBIN_R",
         """\
         # Number of bins the interval [DIST_MIN_R, DIST_MAX_R] is divided to
         """,
         10)
    )
    info.append(
        ("DIST_MIN_phi",
         """\
         # Minimum bin edge for phi coordinate [deg]
         """,
         0)
    )
    info.append(
        ("DIST_MAX_phi",
         """\
         # Maximum bin edge for phi coordinate [deg]
         """,
         360)
    )
    info.append(
        ("DIST_NBIN_phi",
         """\
         # Number of bins the interval [DIST_MIN_phi, DIST_MAX_phi] is divided to
         """,
         10)
    )
    info.append(
        ("DIST_MIN_z",
         """\
         # Minimum bin edge for z coordinate [m]
         """,
         -5)
    )
    info.append(
        ("DIST_MAX_z",
         """\
         # Maximum bin edge for z coordinate [m]
         """,
         5)
    )
    info.append(
        ("DIST_NBIN_z",
         """\
         # Number of bins the interval [DIST_MIN_z, DIST_MAX_z] is divided to
         """,
         10)
    )
    info.append(
        ("DIST_MIN_rho",
         """\
         # Minimum bin edge for rho coordinate
         """,
         0)
    )
    info.append(
        ("DIST_MAX_rho",
         """\
         # Maximum bin edge for rho coordinate
         """,
         2)
    )
    info.append(
        ("DIST_NBIN_rho",
         """\
         # Number of bins the interval [DIST_MIN_rho, DIST_MAX_rho] is divided to
         """,
         10)
    )
    info.append(
        ("DIST_MIN_pol",
         """\
         # Minimum bin edge for pol coordinate [deg]
         """,
         0)
    )
    info.append(
        ("DIST_MAX_pol",
         """\
         # Maximum bin edge for pol coordinate [deg]
         """,
         360)
    )
    info.append(
        ("DIST_NBIN_pol",
         """\
         # Number of bins the interval [DIST_MIN_pol, DIST_MAX_pol] is divided to
         """,
         10)
    )
    info.append(
        ("DIST_MIN_vpa",
         """\
         # Minimum bin edge for vpa coordinate [m/s]
         """,
         -3e8)
    )
    info.append(
        ("DIST_MAX_vpa",
         """\
         # Maximum bin edge for vpa coordinate [m/s]
         """,
         3e8)
    )
    info.append(
        ("DIST_NBIN_vpa",
         """\
         # Number of bins the interval [DIST_MIN_vpa, DIST_MAX_vpa] is divided to
         """,
         10)
    )
    info.append(
        ("DIST_MIN_vpe",
         """\
         # Minimum bin edge for vpe coordinate [m/s]
         """,
         0)
    )
    info.append(
        ("DIST_MAX_vpe",
         """\
         # Maximum bin edge for vpe coordinate [m/s]
         """,
         3e8)
    )
    info.append(
        ("DIST_NBIN_vpe",
         """\
         # Number of bins the interval [DIST_MIN_vpe, DIST_MAX_vpe] is divided to
         """,
         10)
    )
    info.append(
        ("DIST_MIN_vR",
         """\
         # Minimum bin edge for vR coordinate [m/s]
         """,
         0)
    )
    info.append(
        ("DIST_MAX_vR",
         """\
         # Maximum bin edge for vR coordinate [m/s]
         """,
         3e8)
    )
    info.append(
        ("DIST_NBIN_vR",
         """\
         # Number of bins the interval [DIST_MIN_vR, DIST_MAX_vR] is divided to
         """,
         10)
    )
    info.append(
        ("DIST_MIN_vphi",
         """\
         # Minimum bin edge for vphi coordinate [m/s]
         """,
         0)
    )
    info.append(
        ("DIST_MAX_vphi",
         """\
         # Maximum bin edge for vphi coordinate [m/s]
         """,
         3e8)
    )
    info.append(
        ("DIST_NBIN_vphi",
         """\
         # Number of bins the interval [DIST_MIN_vphi, DIST_MAX_vphi] is divided to
         """,
         10)
    )
    info.append(
        ("DIST_MIN_vz",
         """\
         # Minimum bin edge for vz coordinate [m/s]
         """,
         0)
    )
    info.append(
        ("DIST_MAX_vz",
         """\
         # Maximum bin edge for vz coordinate [m/s]
         """,
         3e8)
    )
    info.append(
        ("DIST_NBIN_vz",
         """\
         # Number of bins the interval [DIST_MIN_vz, DIST_MAX_vz] is divided to
         """,
         10)
    )
    info.append(
        ("DIST_MIN_t",
         """\
         # Minimum bin edge for t coordinate [s]
         """,
         0)
    )
    info.append(
        ("DIST_MAX_t",
         """\
         # Maximum bin edge for t coordinate [s]
         """,
         1)
    )
    info.append(
        ("DIST_NBIN_t",
         """\
         # Number of bins the interval [DIST_MIN_t, DIST_MAX_t] is divided to
         """,
         1)
    )
    info.append(
        ("DIST_MIN_q",
         """\
         # Minimum bin edge for q coordinate [e]
         """,
         -100)
    )
    info.append(
        ("DIST_MAX_q",
         """\
         # Maximum bin edge for q coordinate [e]
         """,
         100)
    )
    info.append(
        ("DIST_NBIN_q",
         """\
         # Number of bins the interval [DIST_MIN_q, DIST_MAX_q] is divided to
         """,
         1)
    )

    info.append(("""\
    #**************************************************************************#
    #*                             ORBIT WRITE                                *#
    #*                                                                        *#
    #**************************************************************************#
    """,))

    info.append(
        ("ENABLE_ORBITWRITE",
         """\
         # Enable diagnostics that store marker orbit
         #    - 0 Marker orbit diagnostics are not collected
         #    - 1 Marker orbit diagnostics are collected
         """,
         1)
    )
    info.append(
        ("ORBITWRITE_MODE",
         """\
         # What kind of marker orbit diagnostics are collected
         # These are only used if ENABLE_ORBITWRITE is active.
         #    - 0 When marker crosses a plane (Poincare-plot)
         #    - 1 Between given time intervals
         """,
         1)
    )
    info.append(
        ("ORBITWRITE_MAXPOINTS",
         """\
         # Maximum number of points (per marker) to be written
         # If this number is exceeded when marker is being simulated, the oldest
         # points will be replaced as long as the simulation continues. Thus, this
         # parameter is effectively the number of marker's last positions that are
         # stored.
         """,
         10)
    )
    info.append(
        ("ORBITWRITE_TOROIDALANGLES",
         """\
         # Poloidal angles of toroidal planes where toroidal plots are collected
         # Used when ENABLE_ORBITWRITE = 1 and ORBITWRITE_MODE = 0.
         """,
         [0, 180])
    )
    info.append(
        ("ORBITWRITE_POLOIDALANGLES",
         """\
         # Toroidal angles of poloidal planes where poloidal plots are collected
         # Used when ENABLE_ORBITWRITE = 1 and ORBITWRITE_MODE = 0.
         """,
         [0, 180])
    )
    info.append(
        ("ORBITWRITE_INTERVAL",
         """\
         # Time interval for writing marker state [s]
         # Used when ENABLE_ORBITWRITE = 1 and ORBITWRITE_MODE = 1.
         """,
         1e-8)
    )

    cleaned = []
    for namecmtval in info:
        if len(namecmtval) == 1:
            cleaned.append((textwrap.dedent(namecmtval[0]),))
            continue

        cleaned.append((namecmtval[0],
                        textwrap.dedent(namecmtval[1]),
                        namecmtval[2]))

    print(cleaned)
    return cleaned


class Opt(AscotData):

    def read(self):
        return read_hdf5(self._file, self.get_qid())
