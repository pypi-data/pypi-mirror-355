from __future__ import print_function, absolute_import, division
import raffle._raffle as _raffle
import f90wrap.runtime
import logging
import numpy
import warnings
from ase import Atoms
import re
from collections import Counter
from ase.data import chemical_symbols


class Geom_Rw(f90wrap.runtime.FortranModule):
    """
    Code for handling geometry read/write operations.

    This module provides the necessary functionality to read, write, and
    store atomic geometries.
    In this module, and all of the codebase, element and species are used
    interchangeably.

    Defined in ../src/lib/mod_geom_rw.f90

    .. note::
        It is recommended not to use this module directly, but to handle
        atom objects through the ASE interface.
        This is provided mostly for compatibility with the existing codebase
        and Fortran code.
    """
    @f90wrap.runtime.register_class("raffle.species_type")
    class species_type(f90wrap.runtime.FortranDerivedType):
        def __init__(self, handle=None):
            """
            Create a ``species_type`` object.

            Returns
            -------
            Geom_Rw.species_type
                Object to be constructed
            """
            f90wrap.runtime.FortranDerivedType.__init__(self)
            result = _raffle.f90wrap_geom_rw__species_type_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result

        def __del__(self):
            """
            Destructor for ``species_type`` object.

            Automatically generated destructor for species_type
            """
            if self._alloc:
                _raffle.f90wrap_geom_rw__species_type_finalise(this=self._handle)

        @property
        def atom_idx(self):
            """
            Element atom_idx ftype=integer pytype=int
            """
            try:
                array_ndim, array_type, array_shape, array_handle = \
                    _raffle.f90wrap_species_type__array__atom_idx(self._handle)

                if array_handle == 0:  # Not allocated in Fortran
                    # Return sequential indices if array isn't allocated
                    return numpy.array([j+1 for j in range(self.num)], dtype=numpy.int32)

                shape = tuple(array_shape[:array_ndim])

                # Use composite key (handle + type identifier) to prevent collisions
                cache_key = (array_handle, 'atom_idx')

                # Validate expected dimensions
                if array_ndim != 1:
                    print(f"Warning: atom_idx has incorrect dimension from Fortran: {array_ndim}, expected 1")
                    return numpy.array([j+1 for j in range(self.num)], dtype=numpy.int32)


                if cache_key in self._arrays:
                    atom_idx = self._arrays[cache_key]
                else:
                    atom_idx = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                            self._handle,
                                            _raffle.f90wrap_species_type__array__atom_idx)
                    # Store a copy to avoid potential corruption from view operations
                    self._arrays[cache_key] = atom_idx.copy()

                # Convert to proper integer type but check for corruption first
                try:
                    atom_idx = atom_idx.view(numpy.int32).reshape(shape, order='A')

                    # Validate the integrity of the array
                    if atom_idx.ndim != 1:
                        print(f"Warning: atom_idx has incorrect shape after reshaping: {atom_idx.shape}")
                        return numpy.array([j+1 for j in range(self.num)], dtype=numpy.int32)

                    # Validate array length against num
                    if len(atom_idx) != self.num:
                        print(f"Warning: atom_idx length {len(atom_idx)} doesn't match num {self.num}")
                        return numpy.array([j+1 for j in range(self.num)], dtype=numpy.int32)

                    # Check for unreasonable values
                    if numpy.any(atom_idx <= 0):
                        print(f"Warning: atom_idx contains invalid values (min: {numpy.min(atom_idx)})")
                        return numpy.array([j+1 for j in range(self.num)], dtype=numpy.int32)

                    return atom_idx
                except Exception as e:
                    print(f"Warning: Failed to process atom_idx array: {e}")
                    return numpy.array([j+1 for j in range(self.num)], dtype=numpy.int32)
            except Exception as e:
                print(f"Error accessing atom_idx: {e}")
                return numpy.array([j+1 for j in range(self.num)], dtype=numpy.int32)

        @atom_idx.setter
        def atom_idx(self, atom_idx):
            self.atom_idx[...] = atom_idx

        @property
        def atom(self):
            """
            Derived type containing the atomic information of a crystal.
            """
            try:
                array_ndim, array_type, array_shape, array_handle = \
                    _raffle.f90wrap_species_type__array__atom(self._handle)

                if array_handle == 0:  # Not allocated in Fortran
                    raise ValueError("Atom array is not allocated in Fortran")

                # Validate expected dimensions
                if array_ndim != 2:
                    raise ValueError(f"Atom array has incorrect dimension from Fortran: {array_ndim}, expected 2")

                shape = tuple(array_shape[:array_ndim])

                # Use composite key (handle + type identifier) to prevent collisions
                cache_key = (array_handle, 'atom')

                if cache_key in self._arrays:
                    atom = self._arrays[cache_key]
                else:
                    atom = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                            self._handle,
                                            _raffle.f90wrap_species_type__array__atom)
                    # Store a copy to avoid potential corruption from view operations
                    self._arrays[cache_key] = atom.copy()

                # Convert to proper float type but check for corruption first
                try:
                    atom = atom.view(numpy.float32).reshape(shape, order='A')

                    # Validate the array - should be 2D float array with at least 3 columns
                    if atom.ndim != 2:
                        raise ValueError(f"Atom positions data has incorrect dimension: {atom.ndim}, expected 2")
                    if atom.shape[1] < 3:
                        raise ValueError(f"Atom positions data has insufficient columns: {atom.shape[1]}, expected at least 3")
                    if not numpy.issubdtype(atom.dtype, numpy.floating):
                        raise ValueError(f"Atom positions data has incorrect data type: {atom.dtype}, expected floating-point")

                    # Validate array row count against num
                    if atom.shape[0] != self.num:
                        raise ValueError(f"Atom positions count {atom.shape[0]} doesn't match num {self.num}")

                    # Check for NaN or infinity
                    if numpy.any(~numpy.isfinite(atom)):
                        raise ValueError("Atom positions contain NaN or infinity values")

                    return atom
                except Exception as e:
                    raise ValueError(f"Failed to process atom positions array: {e}")
            except Exception as e:
                raise ValueError(f"Error accessing atom positions: {e}")

        @atom.setter
        def atom(self, atom):
            self.atom[...] = atom

        @property
        def mass(self):
            """
            The mass of the element.
            """
            return _raffle.f90wrap_species_type__get__mass(self._handle)

        @mass.setter
        def mass(self, mass):
            _raffle.f90wrap_species_type__set__mass(self._handle, mass)

        @property
        def charge(self):
            """
            The charge of the element.
            """
            return _raffle.f90wrap_species_type__get__charge(self._handle)

        @property
        def radius(self):
            """
            The radius of the element.
            """
            return _raffle.f90wrap_species_type__get__radius(self._handle)

        @radius.setter
        def radius(self, radius):
            _raffle.f90wrap_species_type__set__radius(self._handle, radius)

        @charge.setter
        def charge(self, charge):
            _raffle.f90wrap_species_type__set__charge(self._handle, charge)

        @property
        def name(self):
            """
            The symbol of the element.
            """
            return _raffle.f90wrap_species_type__get__name(self._handle)

        @name.setter
        def name(self, name):
            _raffle.f90wrap_species_type__set__name(self._handle, name)

        @property
        def num(self):
            """
            The number of atoms of this species/element.
            """
            return _raffle.f90wrap_species_type__get__num(self._handle)

        @num.setter
        def num(self, num):
            _raffle.f90wrap_species_type__set__num(self._handle, num)

        def __str__(self):
            ret = ['<species_type>{\n']
            ret.append('    atom_idx : ')
            ret.append(repr(self.atom_idx))
            ret.append('\n     atom : ')
            ret.append(repr(self.atom))
            ret.append(',\n    mass : ')
            ret.append(repr(self.mass))
            ret.append(',\n    charge : ')
            ret.append(repr(self.charge))
            ret.append(',\n    radius : ')
            ret.append(repr(self.radius))
            ret.append(',\n    name : ')
            ret.append(repr(self.name))
            ret.append(',\n    num : ')
            ret.append(repr(self.num))
            ret.append('}')
            return ''.join(ret)

        _dt_array_initialisers = []


    @f90wrap.runtime.register_class("raffle.basis")
    class basis(f90wrap.runtime.FortranDerivedType):
        def __init__(self, atoms=None, handle=None):
            """
            Create a ``basis`` object.

            This object is used to store the atomic information of a crystal,
            including lattice and basis information.
            This is confusingly named as a crystal = lattice + basis.

            Returns
            -------
            Geom_Rw.basis
                Object to be constructed
            """
            f90wrap.runtime.FortranDerivedType.__init__(self)
            result = _raffle.f90wrap_geom_rw__basis_type_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result

            if atoms is not None:
                self.fromase(atoms)

        def __del__(self):
            """
            Destructor for ``basis`` object.

            Automatically generated destructor for basis
            """
            if self._alloc:
                _raffle.f90wrap_geom_rw__basis_type_finalise(this=self._handle)

        def allocate_species(self, num_species=None, species_symbols=None, species_count=None, \
            positions=None, atom_idx_list=None):
            """
            Allocate memory for the species list.

            Parameters
            ----------
            num_species : int
                Number of species
            species_symbols : list[str]
                List of species symbols
            species_count : list[int]
                List of species counts
            atoms : list[float]
                List of atomic positions
            atom_idx_list : list[int]
                List of atomic indices
            """
            _raffle.f90wrap_geom_rw__allocate_species__binding__basis_type(this=self._handle, \
                num_species=num_species, species_symbols=species_symbols, species_count=species_count, \
                atoms=positions, atom_idx_list=atom_idx_list)

        def _init_array_spec(self):
            """
            Initialise the species array.
            """
            self.spec = f90wrap.runtime.FortranDerivedTypeArray(self,
                                            _raffle.f90wrap_basis_type__array_getitem__spec,
                                            _raffle.f90wrap_basis_type__array_setitem__spec,
                                            _raffle.f90wrap_basis_type__array_len__spec,
                                            """
            Element spec ftype=type(species_type) pytype=species_type


            Defined at ../src/lib/mod_geom_rw.f90 line 35

            """, Geom_Rw.species_type)
            return self.spec

        def copy(self):
            """
            Create a copy of the basis object.

            Returns
            -------
            Geom_Rw.basis
                Copy of the basis object
            """

            # Create a new basis object
            new_basis = Geom_Rw.basis()

            # Copy the attributes
            new_basis.nspec = self.nspec
            new_basis.natom = self.natom
            new_basis.energy = self.energy
            new_basis.lat = numpy.copy(self.lat)
            new_basis.lcart = self.lcart
            new_basis.pbc = numpy.copy(self.pbc)
            new_basis.sysname = self.sysname

            # Copy the species list
            new_basis.allocate_species(
                num_species = self.nspec,
                species_symbols = [self.spec[i].name for i in range(self.nspec)],
                species_count = [self.spec[i].num for i in range(self.nspec)],
                positions = [self.spec[i].atom[j][:3] for i in range(self.nspec) for j in range(self.spec[i].num)]
            )
            for i in range(self.nspec):
                new_basis.spec[i].mass = self.spec[i].mass
                new_basis.spec[i].charge = self.spec[i].charge
                new_basis.spec[i].radius = self.spec[i].radius

            return new_basis

        def toase(self, calculator=None, return_none_on_failure : bool = True):
            """
            Convert the basis object to an ASE Atoms object.

            Parameters
            ----------
            calculator : ase.calculators.calculator.BaseCalculator
                ASE calculator object to be assigned to the Atoms object.
            return_none_on_failure: bool
                Boolean whether to return None on failure.
                If True, return None instead of raising an exception.
                If False, raise an exception on failure.
            """

            # Set the species list
            positions = []
            symbols = []
            idx_list = []
            for i in range(self.nspec):
                name = str(self.spec[i].name.decode()).strip()
                # Skip if no atoms in this species
                if not hasattr(self.spec[i], 'atom') or self.spec[i].num == 0:
                    continue
                # Check if .num is same length as .atom dimension 0
                if self.spec[i].num != self.spec[i].atom.shape[0]:
                    if return_none_on_failure:
                        print(f"Warning: Number of atoms in species {name} ({self.spec[i].num}) does not match the row count in atom array ({self.spec[i].atom.shape[0]}), returning None")
                        return None
                    else:
                        raise ValueError(f"Number of atoms in species {name} ({self.spec[i].num}) does not match the row count in atom array ({self.spec[i].atom.shape[0]})")

                # Process atom positions - require valid data, no fallbacks
                try:
                    atoms = numpy.asarray(self.spec[i].atom, dtype=numpy.float32)

                    # Validate shape and type
                    if atoms.ndim != 2:
                        if return_none_on_failure:
                            print(f"Warning: Atom positions data for species {name} has insufficient columns: {atoms.shape[1]}, expected at least 3")
                            return None
                        else:
                            raise ValueError(f"Atom positions data for species {name} has incorrect dimension: {atoms.ndim}, expected 2")
                    if atoms.shape[1] < 3:
                        if return_none_on_failure:
                            print(f"Warning: Atom positions data for species {name} has insufficient columns: {atoms.shape[1]}, expected at least 3")
                            return None
                        else:
                            raise ValueError(f"Atom positions data for species {name} has insufficient columns: {atoms.shape[1]}, expected at least 3")
                    if not numpy.issubdtype(atoms.dtype, numpy.floating):
                        if return_none_on_failure:
                            print(f"Warning: Atom positions data for species {name} has insufficient columns: {atoms.shape[1]}, expected at least 3")
                            return None
                        else:
                            raise ValueError(f"Atom positions data for species {name} has incorrect type: {atoms.dtype}, expected float")

                    # Check for NaN or infinity values
                    if numpy.any(~numpy.isfinite(atoms)):
                        if return_none_on_failure:
                            print(f"Warning: Atom positions for species {name} contain NaN or infinity values, returning None")
                            return None
                        else:
                            raise ValueError(f"Atom positions for species {name} contain NaN or infinity values")
                except Exception as e:
                    if return_none_on_failure:
                        print(f"Warning: Failed to process atom positions for species {name}, returning None: {e}")
                        return None
                    else:
                        raise ValueError(f"Failed to process atom positions for species {name}: {e}")

                # Process atom indices - allow fallbacks to sequential indices if needed
                try:
                    atom_indices = numpy.asarray(self.spec[i].atom_idx, dtype=numpy.int32)
                    if atom_indices.ndim != 1:
                        print(f"Warning: atom_indices for species {name} has wrong dimensions - using sequential indices")
                        atom_indices = numpy.array([j+1 for j in range(self.spec[i].num)], dtype=numpy.int32)
                    elif len(atom_indices) != self.spec[i].num:
                        print(f"Warning: atom_indices length mismatch for species {name} - using sequential indices")
                        atom_indices = numpy.array([j+1 for j in range(self.spec[i].num)], dtype=numpy.int32)

                    # Check for invalid values
                    if numpy.any(atom_indices <= 0):
                        print(f"Warning: atom_indices for species {name} contains non-positive values - using sequential indices")
                        atom_indices = numpy.array([j+1 for j in range(self.spec[i].num)], dtype=numpy.int32)
                except Exception as e:
                    print(f"Warning: Failed to process atom indices for species {name}, using sequential indices: {e}")
                    atom_indices = numpy.array([j+1 for j in range(self.spec[i].num)], dtype=numpy.int32)

                # Process each atom
                for j in range(self.spec[i].num):
                    pos = atoms[j]
                    if len(pos) < 3:
                        if return_none_on_failure:
                            print(f"Warning: Position vector for atom {j} in species {name} has insufficient dimensions: {len(pos)}, expected at least 3")
                            return None
                        else:
                            raise ValueError(f"Position vector for atom {j} in species {name} has insufficient dimensions: {len(pos)}, expected at least 3")

                    # Get index, with bounds checking
                    if j < len(atom_indices):
                        idx = int(atom_indices[j]) - 1  # Convert to zero-based index
                    else:
                        idx = j  # Fallback to sequential

                    # Add this atom to our lists
                    positions.append(pos[:3])
                    symbols.append(name)
                    idx_list.append(idx)

            # Convert to numpy arrays
            positions = numpy.array(positions, dtype=float)
            symbols = numpy.array(symbols, dtype=str)
            idx_list = numpy.array(idx_list, dtype=int)

            # Only attempt to reorder if there are elements
            if len(idx_list) > 0:
                # Try to reorder atoms based on indices, but with safeguards
                try:
                    # Check if the length of unique indices matches the number of atoms
                    unique_indices = numpy.unique(idx_list)
                    if len(unique_indices) == self.natom:
                        # Reorder if indices are valid
                        sort_indices = numpy.argsort(idx_list)
                        positions = positions[sort_indices]
                        symbols = symbols[sort_indices]
                except Exception as e:
                    # If reordering fails, continue with the original order
                    pass

            cell = numpy.reshape(self.lat, (3,3), order='A')

            pbc = numpy.reshape(self.pbc, (3,), order='A')

            # Create ASE Atoms object
            kwargs = {
                'symbols': symbols,
                'cell': cell,
                'pbc': pbc
            }
            kwargs['positions' if self.lcart else 'scaled_positions'] = positions

            atoms = Atoms(**kwargs)

            if calculator is not None:
                atoms.calc = calculator
            return atoms

        def fromase(self, atoms, verbose=False):
            """
            Convert the ASE Atoms object to a basis object.

            Parameters
            ----------
            atoms : ase.Atoms
                ASE Atoms object to be converted.
            verbose : bool
                Boolean whether to print warnings.
            """
            from ase.calculators.singlepoint import SinglePointCalculator

            # Get the species symbols
            species_symbols = atoms.get_chemical_symbols()
            species_symbols_unique = sorted(set(species_symbols))

            # Set the number of species
            self.nspec = len(species_symbols_unique)

            # Set the number of atoms
            self.natom = len(atoms)

            # check if calculator is present
            if atoms.calc is None:
                if verbose:
                    print("WARNING: No calculator present, setting energy to 0.0")
                atoms.calc = SinglePointCalculator(atoms, energy=0.0)
            self.energy = atoms.get_potential_energy()

            # # Set the lattice vectors
            self.lat = numpy.reshape(atoms.get_cell().flatten(), [3,3], order='A')
            self.pbc = atoms.pbc

            # Set the system name
            self.sysname = atoms.get_chemical_formula()

            # Set the species list
            species_count = []
            atom_positions = []
            atom_idx_list = []
            positions = atoms.get_scaled_positions()
            for species in species_symbols_unique:
                species_count.append(sum([1 for symbol in species_symbols if symbol == species]))
                for j, symbol in enumerate(species_symbols):
                    if symbol == species:
                        atom_positions.append(positions[j])
                        atom_idx_list.append(j + 1)

            # Allocate memory for the atom list
            self.lcart = False
            self.allocate_species(
                species_symbols = species_symbols_unique,
                species_count = species_count,
                positions = atom_positions,
                atom_idx_list = atom_idx_list
            )

        @property
        def nspec(self):
            """
            The number of species in the basis.
            """
            return _raffle.f90wrap_basis_type__get__nspec(self._handle)

        @nspec.setter
        def nspec(self, nspec):
            _raffle.f90wrap_basis_type__set__nspec(self._handle, nspec)

        @property
        def natom(self):
            """
            The number of atoms in the basis.
            """
            return _raffle.f90wrap_basis_type__get__natom(self._handle)

        @natom.setter
        def natom(self, natom):
            _raffle.f90wrap_basis_type__set__natom(self._handle, natom)

        @property
        def energy(self):
            """
            The energy associated with the basis (or crystal).
            """
            return _raffle.f90wrap_basis_type__get__energy(self._handle)

        @energy.setter
        def energy(self, energy):
            _raffle.f90wrap_basis_type__set__energy(self._handle, energy)

        @property
        def lat(self):
            """
            The lattice vectors of the basis.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_basis_type__array__lat(self._handle)

            shape = tuple(array_shape[:array_ndim])

            # Use composite key (handle + type identifier) to prevent collisions
            cache_key = (array_handle, 'lat')
            if cache_key in self._arrays:
                lat = self._arrays[cache_key]
            else:
                lat = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_basis_type__array__lat)

                lat = lat.view(numpy.float32).reshape(shape, order='A')

                # Store a copy to avoid potential corruption from view operations
                self._arrays[cache_key] = lat
            return lat

        @lat.setter
        def lat(self, lat):
            self.lat[...] = lat

        @property
        def lcart(self):
            """
            Boolean whether the atomic positions are in cartesian coordinates.
            """
            return _raffle.f90wrap_basis_type__get__lcart(self._handle)

        @lcart.setter
        def lcart(self, lcart):
            _raffle.f90wrap_basis_type__set__lcart(self._handle, lcart)

        @property
        def pbc(self):
            """
            Boolean array indicating the periodic boundary conditions.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_basis_type__array__pbc(self._handle)
            # Use composite key (handle + type identifier) to prevent collisions
            cache_key = (array_handle, 'pbc')
            if cache_key in self._arrays:
                pbc = self._arrays[cache_key]
            else:
                pbc = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_basis_type__array__pbc)
                # Store a copy to avoid potential corruption from view operations
                self._arrays[cache_key] = pbc
            return pbc

        @pbc.setter
        def pbc(self, pbc):
            self.pbc[...] = pbc

        @property
        def sysname(self):
            """
            The name of the system.
            """
            return _raffle.f90wrap_basis_type__get__sysname(self._handle)

        @sysname.setter
        def sysname(self, sysname):
            _raffle.f90wrap_basis_type__set__sysname(self._handle, sysname)

        def __str__(self):
            ret = ['<basis>{\n']
            ret.append('    nspec : ')
            ret.append(repr(self.nspec))
            ret.append(',\n    natom : ')
            ret.append(repr(self.natom))
            ret.append(',\n    energy : ')
            ret.append(repr(self.energy))
            ret.append(',\n    lat : ')
            ret.append(repr(self.lat))
            ret.append(',\n    lcart : ')
            ret.append(repr(self.lcart))
            ret.append(',\n    pbc : ')
            ret.append(repr(self.pbc))
            ret.append(',\n    sysname : ')
            ret.append(repr(self.sysname))
            ret.append('}')
            return ''.join(ret)

        _dt_array_initialisers = [_init_array_spec]



    @f90wrap.runtime.register_class("raffle.basis_array")
    class basis_array(f90wrap.runtime.FortranDerivedType):
        def __init__(self, atoms=None, handle=None):
            """
            Create a ``basis_array`` object.

            Returns
            -------
            Geom_Rw.basis_array
                Object to be constructed
            """

            f90wrap.runtime.FortranDerivedType.__init__(self)
            result = _raffle.f90wrap_geom_rw__basis_type_xnum_array_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result


            # check if atoms is an ASE Atoms object or a list of ASE Atoms objects
            if atoms:
                if isinstance(atoms, Atoms):
                    self.allocate(1)
                    self.items[0].fromase(atoms)
                elif isinstance(atoms, list):
                    self.allocate(len(atoms))
                    for i, atom in enumerate(atoms):
                        self.items[i].fromase(atom)

        def __del__(self):
            """
            Destructor for class basis_array

            Automatically generated destructor for basis_array
            """
            if self._alloc:
                _raffle.f90wrap_geom_rw__basis_type_xnum_array_finalise(this=self._handle)

        def _init_array_items(self):
            """
            Initialise the items array.
            """
            self.items = f90wrap.runtime.FortranDerivedTypeArray(self,
                                            _raffle.f90wrap_basis_type_xnum_array__array_getitem__items,
                                            _raffle.f90wrap_basis_type_xnum_array__array_setitem__items,
                                            _raffle.f90wrap_basis_type_xnum_array__array_len__items,
                                            """
            Element items ftype=type(basis_type) pytype=basis


            Defined at  line 0

            """, Geom_Rw.basis)
            return self.items

        def toase(self):
            """
            Convert the basis_array object to a list of ASE Atoms objects.
            """

            # Set the species list
            atoms = []
            for i in range(len(self.items)):
                atoms.append(self.items[i].toase())
            return atoms

        def allocate(self, size):
            """
            Allocate the items array with the given size.

            Parameters
            ----------
            size : int
                Size of the items array
            """
            _raffle.f90wrap_basis_type_xnum_array__array_alloc__items(self._handle, num=size)

        def deallocate(self):
            """
            Deallocate the items array
            """
            _raffle.f90wrap_basis_type_xnum_array__array_dealloc__items(self._handle)

        _dt_array_initialisers = [_init_array_items]

    _dt_array_initialisers = []


geom_rw = Geom_Rw()

class Raffle__Distribs_Container(f90wrap.runtime.FortranModule):
    """
    Code for handling distribution functions.

    This module provides the necessary functionality to create, update, and
    store distribution functions.
    The distribution functions are used as descriptors for the atomic
    environments in a crystal.
    The generalised distribution function (GDF) is a generalised descriptor
    for the atomic configurations that each species can adopt.

    Defined in ../src/fortran/lib/mod_distribs_container.f90

    """
    @f90wrap.runtime.register_class("raffle.distribs_container_type")
    class distribs_container_type(f90wrap.runtime.FortranDerivedType):
        def __init__(
                self, handle = None,
                kBT : float = 0.2,
                history_len = 10,
                weight_by_hull : bool = False,
                width : list[float] = None,
                sigma : list[float] = None,
                cutoff_min : list[float] = None,
                cutoff_max : list[float] = None,
                radius_distance_tol : list[float] = None,
                element_energies : dict[str, float] = None,
        ):
            """
            Create a ``Distribs_Container_Type`` object.

            Parameters
            ----------
            history_len : int
                Length of the history for checking convergence of descriptor.
            kBT : float
                Energy scale for the distribution functions.
            weight_by_hull : bool
                Whether to weight the distribution functions by the convex hull distance.
            width : list[float]
                List of distribution function widths.
                The first element is the 2-body distribution function width,
                the second element is the 3-body distribution function width,
                and the third element is the 4-body distribution function width.
            sigma : list[float]
                List of sigma values.
                The first element is the 2-body distribution function sigma,
                the second element is the 3-body distribution function sigma,
                and the third element is the 4-body distribution function sigma.
            cutoff_min : list[float]
                List of minimum cutoff values.
                The first element is the 2-body distribution function minimum cutoff,
                the second element is the 3-body distribution function minimum cutoff,
                and the third element is the 4-body distribution function minimum cutoff.
            cutoff_max : list[float]
                List of maximum cutoff values.
                The first element is the 2-body distribution function maximum cutoff,
                the second element is the 3-body distribution function maximum cutoff,
                and the third element is the 4-body distribution function maximum cutoff.
            radius_distance_tol : list[float]
                List of radius distance tolerance values.
                The first two values are the lower and upper fractional bounds for the
                3-body distribution function radius distance tolerance.
                The third and fourth values are the lower and upper fractional bounds for the
                4-body distribution function radius distance tolerance.
            element_energies : dict[str, float]
                Dictionary mapping element symbols to their formation energies.
                This is used to calculate the formation energies for the distribution functions.

            Returns
            -------
            Distribs_Container_Type
                Object to be constructed

            """
            f90wrap.runtime.FortranDerivedType.__init__(self)
            result = \
                _raffle.f90wrap_raffle__dc__dc_type_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result

            if history_len is not None:
                self.set_history_len(history_len)
            if kBT is not None:
                self.set_kBT(kBT)
            if weight_by_hull is not None:
                self.set_weight_method('energy_above_hull' if weight_by_hull else 'formation_energy')
            if width is not None:
                if not len(width) == 3:
                    raise ValueError("width must be a list of exactly three floats")
                self.set_width(width)
            if sigma is not None:
                if not len(sigma) == 3:
                    raise ValueError("sigma must be a list of exactly three floats")
                self.set_sigma(sigma)
            if cutoff_min is not None:
                if not len(cutoff_min) == 3:
                    raise ValueError("cutoff_min must be a list of exactly three floats")
                self.set_cutoff_min(cutoff_min)
            if cutoff_max is not None:
                if not len(cutoff_max) == 3:
                    raise ValueError("cutoff_max must be a list of exactly three floats")
                self.set_cutoff_max(cutoff_max)
            if radius_distance_tol is not None:
                if not len(radius_distance_tol) == 4:
                    raise ValueError("radius_distance_tol must be a list of exactly four floats")
                self.set_radius_distance_tol(radius_distance_tol)
            if element_energies is not None:
                self.set_element_energies(element_energies)

            self.agox_training_counter = 0

        def __del__(self):
            """
            Destructor for ``Distribs_Container_Type`` object.

            Automatically generated destructor for distribs_container_type
            """
            if self._alloc:
                _raffle.f90wrap_raffle__dc__dc_type_finalise(this=self._handle)

        def set_kBT(self, kBT : float):
            """
            Set the energy scale for the distribution functions.

            Parameters
            ----------
            kBT : float
                Energy scale for the distribution functions.

            """
            self.kBT = kBT

        def set_weight_method(self, method : str):
            """
            Set the weight method for combining the the distribution functions
            to form the generalised distribution function (GDF).

            Parameters
            ----------
            method : str
                Method to be used for weighting the distribution functions.
                Allowed values are:
                - 'formation_energy' or 'formation' or 'form' or 'e_form'
                - 'energy_above_hull' or 'hull_distance' or 'hull' or 'distance' or 'convex_hull'

            """

            if method in ['empirical', 'formation_energy', 'formation', 'form', 'e_form']:
                self.weight_by_hull = False
            elif method in ['energy_above_hull', 'hull_distance', 'hull', 'distance', 'convex_hull']:
                self.weight_by_hull = True
            else:
                raise ValueError("Invalid weight method: {}".format(method))

        def set_width(self, width : list[float]):
            """
            Set the distribution function widths.

            Parameters
            ----------
            width : list[float]
                List of distribution function widths.
                The first element is the 2-body distribution function width,
                the second element is the 3-body distribution function width,
                and the third element is the 4-body distribution function width.
            """
            if not len(width) == 3:
                raise ValueError("width must be a list of exactly three floats")

            _raffle.f90wrap_raffle__dc__set_width__binding__dc_type(this=self._handle, \
                width=width)

        def set_sigma(self, sigma : list[float]):
            """
            Set the sigma values of the Gaussians used to
            build the distribution functions.

            Parameters
            ----------
            sigma : list[float]
                List of sigma values.
                The first element is the 2-body distribution function sigma,
                the second element is the 3-body distribution function sigma,
                and the third element is the 4-body distribution function sigma.
            """
            if not len(sigma) == 3:
                raise ValueError("sigma must be a list of exactly three floats")

            _raffle.f90wrap_raffle__dc__set_sigma__binding__dc_type(this=self._handle, \
                sigma=sigma)

        def set_cutoff_min(self, cutoff_min : list[float]):
            """
            Set the minimum cutoff values for the distribution functions.

            Parameters
            ----------
            cutoff_min : list[float]
                List of minimum cutoff values.
                The first element is the 2-body distribution function minimum cutoff,
                the second element is the 3-body distribution function minimum cutoff,
                and the third element is the 4-body distribution function minimum cutoff.
            """
            if not len(cutoff_min) == 3:
                raise ValueError("cutoff_max must be a list of exactly three floats")

            _raffle.f90wrap_raffle__dc__set_cutoff_min__binding__dc_type(this=self._handle, \
                cutoff_min=cutoff_min)

        def set_cutoff_max(self, cutoff_max : list[float]):
            """
            Set the maximum cutoff values for the distribution functions.

            Parameters
            ----------
            cutoff_min : list[float]
                List of maximum cutoff values.
                The first element is the 2-body distribution function maximum cutoff,
                the second element is the 3-body distribution function maximum cutoff,
                and the third element is the 4-body distribution function maximum cutoff.
            """
            if not len(cutoff_max) == 3:
                raise ValueError("cutoff_max must be a list of exactly three floats")

            _raffle.f90wrap_raffle__dc__set_cutoff_max__binding__dc_type(this=self._handle, \
                cutoff_max=cutoff_max)

        def set_radius_distance_tol(self, radius_distance_tol : list[float]):
            """
            Set the radius distance tolerance for the distribution functions.

            The radius distance tolerance represents a multiplier to the bond radii to
            determine the cutoff distance for the distribution functions.

            Parameters
            ----------
            radius_distance_tol : list[float]
                List of radius distance tolerance values.
                The first two values are the lower and upper bounds for the
                3-body distribution function radius distance tolerance.
                The third and fourth values are the lower and upper bounds for the
                4-body distribution function radius distance tolerance.
            """
            if not len(radius_distance_tol) == 4:
                raise ValueError("radius_distance_tol must be a list of exactly four floats")

            _raffle.f90wrap_raffle__dc__set_radius_distance_tol__binding__dc_type(this=self._handle, \
                radius_distance_tol=radius_distance_tol)

        def set_history_len(self, history_len : int = None):
            """
            Set the history length for the convergence check of the RAFFLE descriptor.

            Parameters
            ----------
            history_len : int
                Length of the history for checking convergence of the descriptor.
            """
            _raffle.f90wrap_raffle__dc__set_history_len__binding__dc_type(this=self._handle, \
                history_len=history_len)

        def create(self,
                   basis_list : Atoms | Geom_Rw.basis_array | list[Atoms],
                   energy_above_hull_list : list[float] = None,
                   deallocate_systems : bool = True,
                   verbose : int = None
        ):
            """
            Create the distribution functions.

            Parameters
            ----------
            basis_list : geom_rw.basis_array or ase.Atoms or list[ase.Atoms]
                List of atomic configurations to be used to create the distribution functions.
            energy_above_hull_list : list[float]
                List of energy above hull values for the atomic configurations.
            deallocate_systems : bool
                Boolean whether to deallocate the atomic configurations after creating the distribution functions.
            verbose : int
                Verbosity level.
            """
            self.agox_training_counter = 0

            if isinstance(basis_list, Atoms):
                basis_list = geom_rw.basis_array(basis_list)
            elif isinstance(basis_list, list):
                atoms_list = [basis for basis in basis_list if isinstance(basis, Atoms)]
                if len(atoms_list) == 0:
                    print("Warning: No valid ASE Atoms objects found in the basis_list, using empty basis_array")
                    return
                basis_list = geom_rw.basis_array(atoms_list)

            _raffle.f90wrap_raffle__dc__create__binding__dc_type(this=self._handle, \
                basis_list=basis_list._handle, \
                energy_above_hull_list=energy_above_hull_list, \
                deallocate_systems=deallocate_systems, \
                verbose=verbose \
            )

        def update(self,
                   basis_list : Atoms | Geom_Rw.basis_array | list[Atoms],
                   energy_above_hull_list : list[float] = None,
                   from_host : bool = True,
                   deallocate_systems : bool = True,
                   agox_training : bool = False,
                   verbose : int = None
        ):
            """
            Update the distribution functions.

            Parameters
            ----------
            basis_list : geom_rw.basis_array or ase.Atoms or list[ase.Atoms]
                List of atomic configurations to be used to create the distribution functions.
            energy_above_hull_list : list[float]
                List of energy above hull values for the atomic configurations.
            deallocate_systems : bool
                Boolean whether to deallocate the atomic configurations after creating the distribution functions.
            from_host : bool
                Boolean whether the provided basis_list is based on the host.
            agox_training : bool
                AGOX INTERNAL USE ONLY: Boolean whether to use the AGOX training mode.
            verbose : int
                Verbosity level.
            """
            if isinstance(basis_list, Atoms):
                basis_list = geom_rw.basis_array(basis_list)
            elif isinstance(basis_list, list):
                if agox_training:
                    num_basis = len(basis_list)
                    if num_basis > self.agox_training_counter:
                        basis_list = basis_list[self.agox_training_counter:]
                        self.agox_training_counter = num_basis
                atoms_list = [basis for basis in basis_list if isinstance(basis, Atoms)]
                if len(atoms_list) == 0:
                    print("Warning: No valid ASE Atoms objects found in the basis_list, returning without updating")
                    return
                basis_list = geom_rw.basis_array(atoms_list)


            _raffle.f90wrap_raffle__dc__update__binding__dc_type(this=self._handle, \
                basis_list=basis_list._handle, \
                energy_above_hull_list=energy_above_hull_list, \
                from_host=from_host, \
                deallocate_systems=deallocate_systems, \
                verbose=verbose \
            )

        def deallocate_systems(self):
            """
            Deallocate the atomic configurations.
            """
            _raffle.f90wrap_raffle__dc__deallocate_systems__binding__dc_type(this=self._handle)

        def add_basis(self, basis):
            """
            Add a basis to the distribution functions.

            It is not recommended to use this function directly, but to use the
            create or update functions instead.

            Parameters
            ----------
            basis : Geom_Rw.basis
                Basis object to be added to the distribution functions.

            """
            _raffle.f90wrap_raffle__dc__add_basis__binding__dc_type(this=self._handle, \
                basis=basis._handle)

        def set_element_energies(self, element_energies : dict):
            """
            Set the element reference energies for the distribution functions.

            These energies are used to calculate the formation energies of the
            atomic configurations.

            Parameters
            ----------
            element_energies : dict
                Dictionary of element reference energies.
                The keys are the element symbols and the values are the reference energies.
            """

            element_list = list(element_energies.keys())
            energies = [element_energies[element] for element in element_list]
            _raffle.f90wrap_raffle__dc__set_element_energies__binding__dc_type(this=self._handle, \
                elements=element_list, energies=energies)

        def get_element_energies(self):
            """
            Get the element reference energies for the distribution functions.

            Returns
            -------
            dict
                Dictionary of element reference energies.
                The keys are the element symbols and the values are the reference energies
            """

            num_elements = _raffle.f90wrap_raffle__dc__get__num_elements(self._handle)
            elements = numpy.zeros((num_elements,), dtype='S3')
            energies = numpy.zeros((num_elements,), dtype=numpy.float32)

            _raffle.f90wrap_raffle__dc__get_element_energies_sm__binding__dc_type(this=self._handle, \
                elements=elements, energies=energies)

            # convert the fortran array to a python dictionary
            element_energies = {}
            for i, element in enumerate(elements):
                name = str(element.decode()).strip()
                element_energies[name] = energies[i]

            return element_energies

        def set_bond_info(self):
            """
            Allocate the bond information array.

            It is not recommended to use this function directly, but to use the
            set_bond_radius or set_bond_radii functions instead.
            """
            _raffle.f90wrap_raffle__dc__set_bond_info__binding__dc_type(this=self._handle)

        def set_bond_radius(self, radius_dict : dict):
            """
            Set the bond radius for the distribution functions.

            Parameters
            ----------
            radius_dict : dict
                Dictionary of bond radii.
                The keys are a tuple of the two element symbols and the values are the bond radii.
            """

            # convert radius_dict to elements and radius
            # radius_dict = {('C', 'C'): 1.5}
            elements = list(radius_dict.keys()[0])
            radius = radius_dict.values()[0]

            _raffle.f90wrap_raffle__dc__set_bond_radius__binding__dc_type(this=self._handle, \
                elements=elements, radius=radius)

        def set_bond_radii(self, radius_dict : dict):
            """
            Set the bond radii for the distribution functions.

            Parameters
            ----------
            radius_dict : dict
                Dictionary of bond radii.
                The keys are a tuple of the two element symbols and the values are the bond radii.
            """

            # convert radius_list to elements and radii
            # radius_list = {('C', 'C'): 1.5, ('C', 'H'): 1.1}
            elements = []
            radii = []
            for key, value in radius_dict.items():
                elements.append(list(key))
                radii.append(value)


            _raffle.f90wrap_raffle__dc__set_bond_radii__binding__dc_type(this=self._handle, \
                elements=elements, radii=radii)

        def get_bond_radii(self):
            """
            Get the bond radii for the distribution functions.

            Returns
            -------
            dict
                Dictionary of bond radii.
                The keys are a tuple of the two element symbols and the values are the bond radii.
            """

            num_elements = _raffle.f90wrap_raffle__dc__get__num_elements(self._handle)
            if num_elements == 0:
                return {}
            num_pairs = round(num_elements * ( num_elements + 1 ) / 2)
            elements = numpy.zeros((num_pairs,2,), dtype='S3', order='F')
            radii = numpy.zeros((num_pairs,), dtype=numpy.float32, order='F')

            _raffle.f90wrap_raffle__dc__get_bond_radii_staticmem__binding__dc_type(this=self._handle, \
                elements=elements, radii=radii)
            # _raffle.f90wrap_raffle__dc__get_bond_radii_staticmem__binding__dc_type(this=self._handle, \
            #     elements=elements, energies=energies)

            # convert the fortran array to a python dictionary
            bond_radii = {}
            for i, element in enumerate(elements):
                names = tuple([str(name.decode()).strip() for name in element])
                bond_radii[names] = radii[i]

            return bond_radii

        def initialise_gdfs(self):
            """
            Initialise the generalised distribution functions (GDFs).

            It is not recommended to use this function directly, but to use the
            create or update functions instead.
            """
            _raffle.f90wrap_raffle__dc__initialise_gdfs__binding__dc_type(this=self._handle)

        def evolve(self): #, system=None):
            """
            Evolve the distribution functions.

            It is not recommended to use this function directly, but to use the
            create or update functions instead.
            """
            _raffle.f90wrap_raffle__dc__evolve__binding__dc_type(this=self._handle)
            # _raffle.f90wrap_raffle__dc__evolve__binding__dc_type(this=self._handle, \
            #     system=None if system is None else system._handle)

        def is_converged(self, threshold : float = 1e-4):
            """
            Parameters
            ----------
            threshold : float
                Threshold for convergence.

            Returns
            -------
            bool
                Boolean indicating whether the distribution functions have converged.
            """
            converged = \
                _raffle.f90wrap_raffle__dc__is_converged__binding__dc_type(this=self._handle, \
                threshold=threshold)
            return converged

        def write_gdfs(self, file : str):
            """
            Write the generalised distribution functions (GDFs) to a file.

            Parameters
            ----------
            file : str
                Name of file to write the GDFs to.
            """
            _raffle.f90wrap_raffle__dc__write_gdfs__binding__dc_type(this=self._handle, \
                file=file)

        def read_gdfs(self, file : str):
            """
            Read the generalised distribution functions (GDFs) from a file.

            Parameters
            ----------
            file : str
                Name of file to read the GDFs from.
            """
            _raffle.f90wrap_raffle__dc__read_gdfs__binding__dc_type(this=self._handle, \
                file=file)

        def write_dfs(self, file : str):
            """
            Write the distribution functions (DFs) associated with all
            allocated systems to a file.

            Parameters
            ----------
            file : str
                Name of file to write the DFs to.
            """
            _raffle.f90wrap_raffle__dc__write_dfs__binding__dc_type(this=self._handle, \
                file=file)

        def read_dfs(self, file : str):
            """
            Read the distribution functions (DFs) associated with a set of
            systems from a file.

            Parameters
            ----------
            file : str
                Name of file to read the DFs from.
            """
            _raffle.f90wrap_raffle__dc__read_dfs__binding__dc_type(this=self._handle, \
                file=file)

        def write_2body(self, file: str):
            """
            Write the 2-body generalised distribution functions (GDFs) to a file.

            Parameters
            ----------
            file : str
                Name of file to write the 2-body GDFs to.
            """
            _raffle.f90wrap_raffle__dc__write_2body__binding__dc_type(this=self._handle, \
                file=file)

        def write_3body(self, file: str):
            """
            Write the 3-body generalised distribution functions (GDFs) to a file.

            Parameters
            ----------
            file : str
                Name of file to write the 3-body GDFs to.
            """
            _raffle.f90wrap_raffle__dc__write_3body__binding__dc_type(this=self._handle, \
                file=file)

        def write_4body(self, file: str):
            """
            Write the 4-body generalised distribution functions (GDFs) to a file.

            Parameters
            ----------
            file : str
                Name of file to write the 4-body GDFs to.
            """
            _raffle.f90wrap_raffle__dc__write_4body__binding__dc_type(this=self._handle, \
                file=file)

        def _get_pair_index(self, species1 : str, species2 : str):
            """
            Get the index of the pair of species in the distribution functions.

            This is meant as an internal function and not likely to be used directly.

            Parameters
            ----------
            species1 : str
                Name of the first species
            species2 : str
                Name of the second species

            Returns
            -------
            int
                Index of the pair of species in the distribution functions.
            """
            idx = \
                _raffle.f90wrap_raffle__dc__get_pair_index__binding__dc_type(this=self._handle, \
                species1=species1, species2=species2)
            return idx

        def _get_bin(self, value : float, dim : int):
            """
            Get the bin index for a value in the distribution functions.

            This is meant as an internal function and not likely to be used directly.

            Parameters
            ----------
            value : float
                Value to get the bin index for.
            dim : int
                Dimension of the distribution function.
                1 for 2-body, 2 for 3-body, and 3 for 4-body.

            Returns
            -------
            int
                Bin index for the value in the distribution functions.

            """
            bin = \
                _raffle.f90wrap_raffle__dc__get_bin__binding__dc_type(this=self._handle, \
                value=value, dim=dim)
            return bin

        def get_2body(self):
            """
            Get the 2-body distribution function.

            Returns
            -------
            float array: 2D array of shape (num_species_pairs, nbins)
                2-body distribution function.

            """
            n0 = self.nbins[0]
            n1 = _raffle.f90wrap_raffle__dc__get_num_pairs__dc_type(this=self._handle)
            output = \
                _raffle.f90wrap_raffle__dc__get_2body__binding__dc_type(this=self._handle, n0=n0, n1=n1).reshape((n0, n1), order='F').T
            return output

        def get_3body(self):
            """
            Get the 3-body distribution function.

            Returns
            -------
            float array: 2D array of shape (num_species, nbins)
                3-body distribution function.

            """
            n0 = self.nbins[1]
            n1 = _raffle.f90wrap_raffle__dc__get_num_species__dc_type(this=self._handle)
            output = \
                _raffle.f90wrap_raffle__dc__get_3body__binding__dc_type(this=self._handle, n0=n0, n1=n1).reshape((n0, n1), order='F').T
            return output

        def get_4body(self):
            """
            Get the 4-body distribution function.

            Returns
            -------
            float array: 2D array of shape (num_species, nbins)
                4-body distribution function.
            """
            n0 = self.nbins[2]
            n1 = _raffle.f90wrap_raffle__dc__get_num_species__dc_type(this=self._handle)
            output = \
                _raffle.f90wrap_raffle__dc__get_4body__binding__dc_type(this=self._handle, n0=n0, n1=n1).reshape((n0, n1), order='F').T
            return output

        def generate_fingerprint(self,
                                 structure: Atoms | Geom_Rw.basis = None,
        ):
            """
            Generate the fingerprint for a given structure.

            Parameters
            ----------
            structure : ase.Atoms
                Atomic structure to generate the fingerprint for.

            Returns
            -------
            output : list[arrays]
                2D arrays
            """
            if isinstance(structure, Atoms):
                structure = geom_rw.basis(structure)

            num_species = structure.nspec
            num_pairs = num_species * (num_species + 1) // 2
            nbins = []
            for i in range(len(self.nbins)):
                nbins.append(self.nbins[i])
                if nbins[i] < 0:
                    nbins[i] = 1 + round( ( self.cutoff_max[i] - self.cutoff_min[i] ) / self.width[i] )

            output_2body = numpy.asfortranarray(numpy.zeros((nbins[0], num_pairs), dtype=numpy.float32))
            output_3body = numpy.asfortranarray(numpy.zeros((nbins[1], num_species), dtype=numpy.float32))
            output_4body = numpy.asfortranarray(numpy.zeros((nbins[2], num_species), dtype=numpy.float32))
            _raffle.f90wrap_raffle__dc__generate_fingerprint_python__dc_type(this=self._handle, \
                structure=structure._handle, output_2body=output_2body, \
                output_3body=output_3body, output_4body=output_4body)

            return output_2body, output_3body, output_4body

        @property
        def iteration(self):
            """
            Iteration number of the training of the distribution functions.
            """
            return _raffle.f90wrap_distribs_container_type__get__iteration(self._handle)

        @iteration.setter
        def iteration(self, iteration):
            _raffle.f90wrap_distribs_container_type__set__iteration(self._handle, \
                iteration)

        @property
        def num_evaluated(self):
            """
            Number of evaluated distribution functions.
            """
            return _raffle.f90wrap_distribs_container_type__get__num_evaluated(self._handle)

        @num_evaluated.setter
        def num_evaluated(self, num_evaluated):
            _raffle.f90wrap_distribs_container_type__set__num_evaluated(self._handle, \
                num_evaluated)

        @property
        def num_evaluated_allocated(self):
            """
            Number of evaluated distribution functions still allocated.
            """
            return \
                _raffle.f90wrap_distribs_container_type__get__num_evaluated_allocated(self._handle)

        @num_evaluated_allocated.setter
        def num_evaluated_allocated(self, num_evaluated_allocated):
            _raffle.f90wrap_distribs_container_type__set__num_evaluated_allocated(self._handle, \
                num_evaluated_allocated)

        @property
        def kBT(self):
            """
            Energy scale for the distribution functions.
            """
            return _raffle.f90wrap_distribs_container_type__get__kbt(self._handle)

        @kBT.setter
        def kBT(self, kBT):
            _raffle.f90wrap_distribs_container_type__set__kbt(self._handle, kBT)

        @property
        def history_len(self):
            """
            Length of the history for convergence checking.
            """
            return _raffle.f90wrap_distribs_container_type__get__history_len(self._handle)

        @history_len.setter
        def history_len(self, history_len):
            _raffle.f90wrap_distribs_container_type__set__history_len(self._handle, \
                history_len)

        @property
        def history_deltas(self):
            """
            History of the descriptor convergence.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_distribs_container_type__array__history_deltas(self._handle)
            if array_handle in self._arrays:
                history_deltas = self._arrays[array_handle]
            else:
                history_deltas = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_distribs_container_type__array__history_deltas)
                self._arrays[array_handle] = history_deltas
            return history_deltas

        @history_deltas.setter
        def history_deltas(self, history_deltas):
            self.history_deltas[...] = history_deltas

        @property
        def weight_by_hull(self):
            """
            Boolean whether to weight the distribution functions by the energy above hull.
            """
            return \
                _raffle.f90wrap_distribs_container_type__get__weight_by_hull(self._handle)

        @weight_by_hull.setter
        def weight_by_hull(self, weight_by_hull):
            _raffle.f90wrap_distribs_container_type__set__weight_by_hull(self._handle, \
                weight_by_hull)

        @property
        def smooth_viability(self):
            """
            DEVELOPER TOOL. Boolean whether to smooth the viability evaluation of points.
            """
            return \
                _raffle.f90wrap_distribs_container_type__get__smooth_viability(self._handle)

        @smooth_viability.setter
        def smooth_viability(self, smooth_viability):
            _raffle.f90wrap_distribs_container_type__set__smooth_viability(self._handle, \
                smooth_viability)

        @property
        def nbins(self):
            """
            Number of bins in the distribution functions.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_distribs_container_type__array__nbins(self._handle)
            if array_handle in self._arrays:
                nbins = self._arrays[array_handle]
            else:
                nbins = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_distribs_container_type__array__nbins)
                self._arrays[array_handle] = nbins
            return nbins

        @nbins.setter
        def nbins(self, nbins):
            self.nbins[...] = nbins

        @property
        def sigma(self):
            """
            Sigma values for the Gaussians used by the
            2-, 3-, and 4-body distribution functions.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_distribs_container_type__array__sigma(self._handle)
            if array_handle in self._arrays:
                sigma = self._arrays[array_handle]
            else:
                sigma = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_distribs_container_type__array__sigma)
                self._arrays[array_handle] = sigma
            return sigma

        @sigma.setter
        def sigma(self, sigma):
            self.sigma[...] = sigma

        @property
        def width(self):
            """
            Bin widths for the 2-, 3-, and 4-body distribution functions.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_distribs_container_type__array__width(self._handle)
            if array_handle in self._arrays:
                width = self._arrays[array_handle]
            else:
                width = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_distribs_container_type__array__width)
                self._arrays[array_handle] = width
            return width

        @width.setter
        def width(self, width):
            self.width[...] = width

        @property
        def cutoff_min(self):
            """
            The lower cutoff values for the 2-, 3-, and 4-body distribution functions.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_distribs_container_type__array__cutoff_min(self._handle)
            if array_handle in self._arrays:
                cutoff_min = self._arrays[array_handle]
            else:
                cutoff_min = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_distribs_container_type__array__cutoff_min)
                self._arrays[array_handle] = cutoff_min
            return cutoff_min

        @cutoff_min.setter
        def cutoff_min(self, cutoff_min):
            self.cutoff_min[...] = cutoff_min

        @property
        def cutoff_max(self):
            """
            The upper cutoff values for the 2-, 3-, and 4-body distribution functions.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_distribs_container_type__array__cutoff_max(self._handle)
            if array_handle in self._arrays:
                cutoff_max = self._arrays[array_handle]
            else:
                cutoff_max = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_distribs_container_type__array__cutoff_max)
                self._arrays[array_handle] = cutoff_max
            return cutoff_max

        @cutoff_max.setter
        def cutoff_max(self, cutoff_max):
            self.cutoff_max[...] = cutoff_max

        @property
        def radius_distance_tol(self):
            """
            The radius distance tolerance for the distribution functions.

            The radius distance tolerance represents a multiplier to the bond radii to
            determine the cutoff distance for the distribution functions.

            The first two values are the lower and upper bounds for the
            3-body distribution function radius distance tolerance.
            The third and fourth values are the lower and upper bounds for the
            4-body distribution function radius distance tolerance.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_distribs_container_type__array__radius_distance_tol(self._handle)
            if array_handle in self._arrays:
                radius_distance_tol = self._arrays[array_handle]
            else:
                radius_distance_tol = \
                    f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_distribs_container_type__array__radius_distance_tol)
                self._arrays[array_handle] = radius_distance_tol
            return radius_distance_tol

        @radius_distance_tol.setter
        def radius_distance_tol(self, radius_distance_tol):
            self.radius_distance_tol[...] = radius_distance_tol

        def __str__(self):
            ret = ['<distribs_container_type>{\n']
            ret.append('    num_evaluated : ')
            ret.append(repr(self.num_evaluated))
            ret.append(',\n    num_evaluated_allocated : ')
            ret.append(repr(self.num_evaluated_allocated))
            ret.append(',\n    kBT : ')
            ret.append(repr(self.kBT))
            ret.append(',\n    history_len : ')
            ret.append(repr(self.history_len))
            ret.append(',\n    history_deltas : ')
            ret.append(repr(self.history_deltas))
            ret.append(',\n    weight_by_hull : ')
            ret.append(repr(self.weight_by_hull))
            ret.append(',\n    nbins : ')
            ret.append(repr(self.nbins))
            ret.append(',\n    sigma : ')
            ret.append(repr(self.sigma))
            ret.append(',\n    width : ')
            ret.append(repr(self.width))
            ret.append(',\n    cutoff_min : ')
            ret.append(repr(self.cutoff_min))
            ret.append(',\n    cutoff_max : ')
            ret.append(repr(self.cutoff_max))
            ret.append(',\n    radius_distance_tol : ')
            ret.append(repr(self.radius_distance_tol))
            ret.append('}')
            return ''.join(ret)

        _dt_array_initialisers = []#_init_array_system]


    _dt_array_initialisers = []


raffle__distribs_container = Raffle__Distribs_Container()

class Generator(f90wrap.runtime.FortranModule):
    """
    Code for generating interface structures.

    The module handles converting Python objects to Fortran objects and vice versa.
    These include converting between dictionaries and Fortran derived types, and
    between ASE Atoms objects and Fortran derived types.

    Defined in ../src/lib/mod_generator.f90

    """
    @f90wrap.runtime.register_class("raffle.stoichiometry_type")
    class stoichiometry_type(f90wrap.runtime.FortranDerivedType):
        def __init__(self, dict=None, element=None, num=None, handle=None):
            """
            Object to store the stoichiometry of a structure.

            Returns
            -------
            stoichiometry_type
                Stoichiometry object
            """
            f90wrap.runtime.FortranDerivedType.__init__(self)
            result = _raffle.f90wrap_stoichiometry_type_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result

            if element:
                self.element = element
            if num:
                self.num = num


        def __del__(self):
            """
            Destructor for class Stoichiometry_Type

            Automatically generated destructor for stoichiometry_type
            """
            if self._alloc:
                _raffle.f90wrap_stoichiometry_type_finalise(this=self._handle)

        @property
        def element(self):
            """
            String representing an element symbol.
            """
            return _raffle.f90wrap_stoichiometry_type__get__element(self._handle)

        @element.setter
        def element(self, element):
            _raffle.f90wrap_stoichiometry_type__set__element(self._handle, element)

        @property
        def num(self):
            """
            Integer representing the number of atoms of the element.
            """
            return _raffle.f90wrap_stoichiometry_type__get__num(self._handle)

        @num.setter
        def num(self, num):
            _raffle.f90wrap_stoichiometry_type__set__num(self._handle, num)

        def __str__(self):
            ret = ['<stoichiometry_type>{\n']
            ret.append('    element : ')
            ret.append(repr(self.element))
            ret.append(',\n    num : ')
            ret.append(repr(self.num))
            ret.append('}')
            return ''.join(ret)

        _dt_array_initialisers = []


    @f90wrap.runtime.register_class("raffle.stoichiometry_array")
    class stoichiometry_array(f90wrap.runtime.FortranDerivedType):
        def __init__(self, dict=None, handle=None):
            """
            Array or list of stoichiometry objects.

            Returns
            -------
            Generator.stoichiometry_array
                Stoichiometry array object
            """

            f90wrap.runtime.FortranDerivedType.__init__(self)
            result = _raffle.f90wrap_generator__stoich_type_xnum_array_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result
            if dict:
                num_elements = len(dict)
                elements = list(dict.keys())
                nums = list(dict.values())
                self.allocate(num_elements)
                for i in range(num_elements):
                    self.items[i].element = elements[i]
                    self.items[i].num = nums[i]

        def __del__(self):
            """
            Destructor for class Stoichiometry_Type

            Automatically generated destructor for stoichiometry_type
            """
            if self._alloc:
                _raffle.f90wrap_generator__stoich_type_xnum_array_finalise(this=self._handle)

        def _init_array_items(self):
            self.items = f90wrap.runtime.FortranDerivedTypeArray(self,
                                            _raffle.f90wrap_stoich_type_xnum_array__array_getitem__items,
                                            _raffle.f90wrap_stoich_type_xnum_array__array_setitem__items,
                                            _raffle.f90wrap_stoich_type_xnum_array__array_len__items,
                                            """
            Element items ftype=type(stoichiometry_type) pytype=stoichiometry_type


            Defined at  line 0

            """, Generator.stoichiometry_type)
            return self.items

        def allocate(self, size):
            """
            Allocate the items array with the given size.

            Parameters
            ----------
            size : int
                Size of the items array
            """
            _raffle.f90wrap_stoich_type_xnum_array__array_alloc__items(self._handle, num=size)

        def deallocate(self):
            """
            Deallocate the items array.
            """
            _raffle.f90wrap_stoich_type_xnum_array__array_dealloc__items(self._handle)



        _dt_array_initialisers = [_init_array_items]


    @f90wrap.runtime.register_class("raffle.raffle_generator")
    class raffle_generator(f90wrap.runtime.FortranDerivedType):

        def __init__(
                self, handle=None,
                seed : int | list[int] = None,
                method_ratio : dict[str, float] = None,
                max_walk_attempts : int = None,
                walk_step_size_coarse : float = None,
                walk_step_size_fine : float = None,
                host : Atoms | Geom_Rw.basis = None,
                grid : list[int] = None,
                grid_spacing : float = None,
                grid_offset : list[float] = None,
                bounds : list[float] = None,
                **kwargs
        ):
            """
            Create a ``raffle_generator`` object.

            This object is used to generate structures using the RAFFLE method.
            The object has procedures to set the parameters for the generation
            and to generate the structures.

            Parameters
            ----------
            seed : int or list[int]
                Seed for the random number generator. If a list is provided, it will use one for each thread.
            method_ratio : dict[str, float]
                Dictionary of the ratio of the five placement methods to be used.
                The keys are the method names and the values are the ratios.
                The methods are 'void', 'rand' (random), 'walk', 'grow' (growth), and 'min' (minimum/global).
            max_walk_attempts : int
                Maximum number of attempts to place an atom using the "walk" or "grow" method before skipping.
            walk_step_size_coarse : float
                Coarse step size for the "walk" or "grow" method.
            walk_step_size_fine : float
                Fine step size for the "walk" or "grow" method.
            host : ase.Atoms or Geom_Rw.basis
                Host structure for the generation.
            grid : list[int]
                Number of grid points in each dimension for the generation.
            grid_spacing : float
                Spacing for the grid.
            grid_offset : list[float]
                Offset for the grid in each dimension.
            **kwargs
                Additional keyword arguments to be passed to the generator.
            """
            f90wrap.runtime.FortranDerivedType.__init__(self)
            result = _raffle.f90wrap_generator__raffle_generator_type_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result

            if seed is not None:
                self.init_seed(put=seed, get=None, num_threads=None)
            if method_ratio is not None:
                self.set_method_ratio_default(method_ratio)
            if max_walk_attempts is not None:
                self.set_max_attempts(max_walk_attempts)
            if walk_step_size_coarse is not None or walk_step_size_fine is not None:
                self.set_walk_step_size(coarse=walk_step_size_coarse, fine=walk_step_size_fine)

            # handle the grid parameters
            if grid is not None or grid_spacing is not None or grid_offset is not None:
                if grid is not None:
                    if not isinstance(grid, list):
                        raise TypeError("grid must be a list of integers")
                    if len(grid) != 3:
                        raise ValueError("grid must be a list of three integers")
                if grid_offset is not None:
                    if not isinstance(grid_offset, list):
                        raise TypeError("grid_offset must be a list of floats")
                    if len(grid_offset) != 3:
                        raise ValueError("grid_offset must be a list of three floats")

                self.set_grid(grid=grid, grid_spacing=grid_spacing, grid_offset=grid_offset)

            # handle additional keyword arguments, which go to the distributions container
            self.distributions = raffle__distribs_container.distribs_container_type(**kwargs)

            # host must be set after the distributions container is set, as it affects the distributions container
            if host is not None:
                self.set_host(host)

            if bounds is not None:
                self.set_bounds(bounds)

        def __del__(self):
            """
            Destructor for class raffle_generator


            Defined at ../src/lib/mod_generator.f90 lines \
                23-34

            """
            if self._alloc:
                _raffle.f90wrap_generator__raffle_generator_type_finalise(this=self._handle)

        def init_seed(self, put: int|list[int] = None, get: list[int] = None, num_threads: int = None):
            """
            Initialise the random number generator seed.

            Parameters
            ----------
            put : list[int]
                List of integers to be used as the seed for the random number generator.
            get : list[int]
                List of integers to be used as the seed for the random number generator.
            num_threads : int
                Number of threads, one for each random number generator.

            """
            # check if put is an integer
            if isinstance(put, int):
                put = [put]

            _raffle.f90wrap_generator__init_seed__binding__rgt(this=self._handle, \
                put=put, get=get, num_threads=num_threads)

        def set_method_ratio_default(self, method_ratio : dict[str, float]):
            """
            Set the method of the five placement methods to be used.

            This will be used as the default ratio if one is not provided as an input argument to the generate() method.

            Parameters
            ----------
            method_ratio : dict[str, float]
                The ratio of the walk method to the void method.
            """            # check if method_ratio is provided, if so, use it only if method_ratio is not provided

            # handle other names for the methods, such as random, growth, minimum, etc.
            if "random" in method_ratio:
                if "rand" in method_ratio:
                    raise ValueError("Both random and rand are provided, use only one (random or rand)")
                method_ratio["rand"] = method_ratio.pop("random")
            if "growth" in method_ratio:
                if "grow" in method_ratio:
                    raise ValueError("Both growth and grow are provided, use only one (growth or grow)")
                method_ratio["grow"] = method_ratio.pop("growth")
            if "minimum" in method_ratio:
                if "min" in method_ratio:
                    raise ValueError("Both minimum and min are provided, use only one (minimum or min)")
                method_ratio["min"] = method_ratio.pop("minimum")
            if "global" in method_ratio:
                if "min" in method_ratio:
                    raise ValueError("Both global and min are provided, use only one (global or min)")
                method_ratio["min"] = method_ratio.pop("global")

            # exit if any other method is provided
            for key in method_ratio.keys():
                if key not in ["void", "rand", "walk", "grow", "min"]:
                    raise ValueError(f"Unknown method {key} provided, use only void, rand (random), walk, grow (growth), or min (minimum/global)")

            method_ratio_list = []
            method_ratio_list.append(method_ratio.get("void", 0.0))
            method_ratio_list.append(method_ratio.get("rand", 0.0)) # or method_ratio.get("random", 0.0))
            method_ratio_list.append(method_ratio.get("walk", 0.0))
            method_ratio_list.append(method_ratio.get("grow", 0.0)) # or method_ratio.get("growth", 0.0))
            method_ratio_list.append(method_ratio.get("min", 0.0))  # or method_ratio.get("minimum", 0.0) or method_ratio.get("global", 0.0))

            _raffle.f90wrap_generator__set_method_ratio_default__binding__rgt(this=self._handle, \
                method_ratio=method_ratio_list)

        def set_max_attempts(self, max_attempts : int):
            """
            Set the walk-method maximum attempts parameter.
            This parameter determines the maximum number of attempts to generate a structure
            using the walk method before reverting to the void method.

            Parameters
            ----------
            max_attempts : int
                The maximum number of attempts to generate a structure using the walk method.
            """
            self.max_attempts = max_attempts

        def set_walk_step_size(self, coarse=None, fine=None):
            """
            Set the walk-method step size parameters.

            Parameters
            ----------
            coarse : float
                The coarse step size for the walk method.
            fine : float
                The fine step size for the walk method.
            """
            if coarse is not None:
                self.walk_step_size_coarse = coarse
            if fine is not None:
                self.walk_step_size_fine = fine

        def set_host(self, host : Atoms | Geom_Rw.basis):
            """
            Set the host structure for the generation.

            Parameters
            ----------
            host : ase.Atoms or Geom_Rw.basis
                The host structure for the generation.
            """
            # check if host is ase.Atoms object or a Fortran derived type basis_type
            if isinstance(host, Atoms):
                host_copy = geom_rw.basis(atoms=host.copy())
            elif isinstance(host, geom_rw.basis):
                host_copy = host.copy()
            else:
                raise TypeError("Expected host to be ASE ase.Atoms or Geom_Rw.basis")

            _raffle.f90wrap_generator__set_host__binding__rgt(this=self._handle, \
                host=host_copy._handle)

        def get_host(self):
            """
            Get the host structure for the generation.

            Returns
            -------
            ase.Atoms
                The host structure for the generation.
            """
            is_defined = _raffle.f90wrap_raffle_generator_type__get__host_defined(self._handle)
            if not is_defined:
                return None
            output = \
                _raffle.f90wrap_generator__get_host__binding__rgt(this=self._handle)
            output = f90wrap.runtime.lookup_class("raffle.basis").from_handle(output, \
                alloc=True)
            # check if host is ase.Atoms object or a Fortran derived type basis_type
            try:
                ret_host = output.toase().copy()
            except:
                ret_host = None
            return ret_host

        def prepare_host(self,
                         interface_location : list[float] = None,
                         interface_axis : int | str = 3,
                         depth : float = 3.0,
                         location_as_fractional : bool = False
        ):
            """
            Prepare the host by removing atoms depth away from the interface and returning an associated missing stoichiometry dictionary.

            Parameters
            ----------
            interface_location : list[float]
                The location of the interface in direct coordinates.
            interface_axis (int or str):
                The axis along which to remove atoms from the host.
                0 for a, 1 for b, 2 for c.
                Alternatively, 'a', 'b', or 'c' can be used.
            depth : float
                The depth to remove atoms from the host.
            location_as_fractional : bool
                Whether the interface location is given in fractional coordinates.

            Returns
            -------
            dict
                A dictionary of the missing stoichiometry.
                The keys are the element symbols and the values are the number of atoms removed.
            """
            # check if interface_axis is a string
            interface_axis_int = interface_axis
            if isinstance(interface_axis_int, str):
                interface_axis_int = interface_axis.lower()
                if interface_axis_int == 'a':
                    interface_axis_int = 0
                elif interface_axis_int == 'b':
                    interface_axis_int = 1
                elif interface_axis_int == 'c':
                    interface_axis_int = 2
                else:
                    raise ValueError("interface_axis must be 0, 1, 2, 'a', 'b', or 'c'")

            # convert interface_location to numpy array in Fortran order
            interface_location_fort = numpy.array(interface_location, dtype=numpy.float32, order='F')

            # get current stoichiometry of the host
            stoich_old = self.get_host().get_chemical_symbols()

            _raffle.f90wrap_generator__prepare_host__binding__rgt(this=self._handle, \
                interface_location=interface_location_fort, \
                interface_axis=interface_axis_int, \
                depth=depth,
                location_as_fractional=location_as_fractional)

            # get new stoichiometry of the host
            stoich_new = self.get_host().get_chemical_symbols()

            # get the missing stoichiometry
            missing_stoichiometry = {}
            for element in set(stoich_old):
                old_count = stoich_old.count(element)
                new_count = stoich_new.count(element)
                if old_count > new_count:
                    missing_stoichiometry[element] = old_count - new_count

            return missing_stoichiometry

        def set_grid(self, grid : list[int] = None, grid_spacing : float = None, grid_offset : list[float] = None):
            """
            Set the grid parameters for the generation.

            Parameters
            ----------
            grid : list[int]
                The number of grid points along each axis of the host.
            grid_spacing : float
                The spacing between grid points.
            grid_offset : list[float]
                The offset of the grid from the origin.
            """
            _raffle.f90wrap_generator__set_grid__binding__raffle_generator_type(this=self._handle, \
                grid=grid, grid_spacing=grid_spacing, grid_offset=grid_offset)

        def reset_grid(self):
            """
            Reset the grid parameters to their default values.
            """
            _raffle.f90wrap_generator__reset_grid__binding__raffle_generator_type(this=self._handle)

        def get_bounds(self):
            """
            Get the bounding box for the generation.

            Returns
            -------
            bounds : list[list[float]]
                The bounding box within which to constrain placement of atoms.
                In the form [[a_min, b_min, c_min], [a_max, b_max, c_max]].
                Values given in direct (crystal) coordinates, ranging from 0 to 1.
            """

            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_raffle_generator_type__array__bounds(this=self._handle)
            if array_handle in self._arrays:
                bounds = self._arrays[array_handle]
            else:
                bounds = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_raffle_generator_type__array__bounds)
                self._arrays[array_handle] = bounds
            return bounds

        def set_bounds(self, bounds = None):
            """
            Set the bounding box for the generation.

            Parameters
            ----------
            bounds : list[list[float]]:
                The bounding box within which to constrain placement of atoms.
                In the form [[a_min, b_min, c_min], [a_max, b_max, c_max]].
                Values given in direct (crystal) coordinates, ranging from 0 to 1.
            """
            # check if bounds is a list of length 2
            if not isinstance(bounds, list) or len(bounds) != 2:
                raise ValueError("bounds must be a list of length 2")
            # check each element of bounds is a list of length 3
            for bound in bounds:
                if not ( isinstance(bound, list) or isinstance(bound, numpy.ndarray) ) or len(bound) != 3:
                    raise ValueError("each element of bounds must be a list of length 3")

            # assert that bounds are in the range [0, 1]
            for bound in bounds:
                for value in bound:
                    if not (0.0 <= value <= 1.0):
                        raise ValueError("bounds must be in the range [0, 1]")

            # assert that a_max > a_min, b_max > b_min, c_max > c_min
            if not (bounds[0][0] < bounds[1][0] and bounds[0][1] < bounds[1][1] and bounds[0][2] < bounds[1][2]):
                raise ValueError("bounds must be in the form [[a_min, b_min, c_min], [a_max, b_max, c_max]] with a_max > a_min, b_max > b_min, c_max > c_min")

            _raffle.f90wrap_generator__set_bounds__binding__rgt(this=self._handle, \
                bounds=bounds)

        def reset_bounds(self):
            """
            Reset the bounding box to the full host structure.
            """
            _raffle.f90wrap_generator__reset_bounds__binding__rgt(this=self._handle)

        def generate(self,
                     num_structures : int,
                    stoichiometry,
                    method_ratio: dict[str, float] = {"void": 0.0, "rand": 0.0, "walk": 0.0, "grow": 0.0, "min": 0.0},
                    method_probab : dict = None,
                    seed : int = None,
                    settings_out_file : str = None,
                    verbose : int = 0,
                    return_exit_code : bool = False,
                    calc = None
        ):
            """
            Generate structures using the RAFFLE method.



            Parameters
            ----------
            num_structures : int
                The number of structures to generate.
            stoichiometry : Generator.stoichiometry_array, str, or dict
                The stoichiometry of the structures to generate.
            method_ratio : dict
                The ratio of using each method to generate a structure.
            method_probab : dict
                DEPRECATED. Use `method_ratio` instead. Will be removed in a future version.
            seed : int
                The seed for the random number generator.
            settings_out_file : str
                The file to write the settings to.
            verbose : int
                The verbosity level for the generation.
            return_exit_code : bool
                Whether to return the exit code from the generation.
            calc : ase.calculators.calculator.BaseCalculator
                The calculator to use for the generated structures.

            Returns
            -------
            structures : ase.Atoms
                The generated structures.
            exit_code : int
                The exit code from the generation.
            """

            exit_code = 0
            structures = None

            # check if method_ratio is provided, if so, use it only if method_ratio is not provided
            if method_probab is not None and not all(v == 0.0 for v in method_ratio.values()):
                method_ratio = method_probab
                warnings.warn("method_probab is deprecated, use method_ratio instead", DeprecationWarning)
            elif method_probab is not None:
                warnings.warn("method_probab is deprecated, use method_ratio instead", DeprecationWarning)
                # break if both method_ratio and method_probab are provided
                raise ValueError("Both method_ratio and method_probab are provided, use only one (method_ratio)")

            # handle other names for the methods, such as random, growth, minimum, etc.
            if "random" in method_ratio:
                if "rand" in method_ratio:
                    raise ValueError("Both random and rand are provided, use only one (random or rand)")
                method_ratio["rand"] = method_ratio.pop("random")
            if "growth" in method_ratio:
                if "grow" in method_ratio:
                    raise ValueError("Both growth and grow are provided, use only one (growth or grow)")
                method_ratio["grow"] = method_ratio.pop("growth")
            if "minimum" in method_ratio:
                if "min" in method_ratio:
                    raise ValueError("Both minimum and min are provided, use only one (minimum or min)")
                method_ratio["min"] = method_ratio.pop("minimum")
            if "global" in method_ratio:
                if "min" in method_ratio:
                    raise ValueError("Both global and min are provided, use only one (global or min)")
                method_ratio["min"] = method_ratio.pop("global")

            # exit if any other method is provided
            for key in method_ratio.keys():
                if key not in ["void", "rand", "walk", "grow", "min"]:
                    raise ValueError(f"Unknown method {key} provided, use only void, rand (random), walk, grow (growth), or min (minimum/global)")

            method_ratio_list = []
            method_ratio_list.append(method_ratio.get("void", 0.0))
            method_ratio_list.append(method_ratio.get("rand", 0.0)) # or method_ratio.get("random", 0.0))
            method_ratio_list.append(method_ratio.get("walk", 0.0))
            method_ratio_list.append(method_ratio.get("grow", 0.0)) # or method_ratio.get("growth", 0.0))
            method_ratio_list.append(method_ratio.get("min", 0.0))  # or method_ratio.get("minimum", 0.0) or method_ratio.get("global", 0.0))

            # check if all values are 0.0, if so, set them to the default of all 1.0
            if all([val < 1E-6 for val in method_ratio_list]):
                method_ratio_list = None

            # if stoichiometry is a dictionary, convert it to a stoichiometry_array
            if isinstance(stoichiometry, dict):
                stoichiometry = Generator.stoichiometry_array(dict=stoichiometry)
            elif isinstance(stoichiometry, str):
                # convert str, example "Al12O24" to dict, so {"Al": 12, "O": 24}
                split = re.findall(r'[A-Z][a-z]?\d*', stoichiometry)
                stoichiometry = {}
                for s in split:
                    element = re.findall(r'[A-Z][a-z]?', s)[0]
                    # if no number is found, set it to 1
                    if re.findall(r'\d+', s) == []:
                        num = 1
                    else:
                        num = re.findall(r'\d+', s)[0]
                    stoichiometry[element] = int(num)
                stoichiometry = Generator.stoichiometry_array(dict=stoichiometry)
            elif isinstance(stoichiometry, list) and all(isinstance(i, int) for i in stoichiometry):
                stoichiometry = [chemical_symbols[n] for n in stoichiometry]
                stoichiometry = dict(Counter(stoichiometry))
                stoichiometry = Generator.stoichiometry_array(dict=stoichiometry)

            exit_code = _raffle.f90wrap_generator__generate__binding__rgt(
                this=self._handle,
                num_structures=num_structures,
                stoichiometry=stoichiometry._handle,
                method_ratio=method_ratio_list,
                settings_out_file=settings_out_file,
                seed=seed, verbose=verbose)
            if ( exit_code != 0 and exit_code != None ) and not return_exit_code:
                raise RuntimeError(f"Interface generation failed (exit code {exit_code})")

            structures = self.get_structures(calc)[-num_structures:]
            if return_exit_code:
                return structures, exit_code
            return structures

        def get_structures(self, calculator=None):
            """
            Get the generated structures as a list of ASE Atoms objects.

            Parameters
            ----------
            calculator : ase.calculators.calculator.BaseCalculator
                The calculator to use for the generated structures.
            """
            atoms = []
            for structure in self.structures:
                atoms.append(structure.toase(calculator))
            return atoms

        def set_structures(self, structures):
            """
            Set the list of generated structures.

            Parameters
            ----------
            structures : list[geom_rw.basis] or list[ase.Atoms]
                The list of structures to set.
            """
            structures = geom_rw.basis_array(atoms=structures)
            _raffle.f90wrap_generator__set_structures__binding__rgt(this=self._handle, \
                structures=structures._handle)

        def remove_structure(self, index : int | list[int]):
            """
            Remove the structure at the given indices from the generator.

            Parameters
            ----------
            index : int or list[int]
                The indices of the structure to remove.
            """
            index_list = [index] if isinstance(index, int) else index
            index_list = [ i + 1 for i in index_list ]
            _raffle.f90wrap_generator__remove_structure__binding__rgt(this=self._handle, \
                index_bn=index_list)

        def evaluate(self, basis):
            """
            Evaluate the viability of the structures.

            Parameters
            ----------
            basis : Geom_Rw.basis or ase.Atoms
                The basis to use for the evaluation.

            Returns
            -------
            float
                The viability of the structures.
            """
            if isinstance(basis, Atoms):
                basis = geom_rw.basis(atoms=basis)

            viability = \
                _raffle.f90wrap_generator__evaluate__binding__rgt(this=self._handle, \
                basis=basis._handle)
            return viability

        def get_probability_density(self,
                                    basis,
                                    species : list[str] | str,
                                    grid : list[int] = None,
                                    grid_offset : list[float] = None,
                                    grid_spacing : float = None,
                                    bounds : list[list[float]] = None,
                                    return_grid : bool = False
        ):
            """
            Get the probability density of the generated structures.

            Parameters
            ----------
            basis : Geom_Rw.basis or ase.Atoms
                The basis to use for the evaluation.
            species : list[str] or str
                The species to use for the evaluation.
            grid : list[int]
                The number of grid points along each axis of the host.
            grid_offset : list[float]
                The offset of the grid from the origin.
            grid_spacing : float
                The spacing between grid points.
            bounds : list[list[float]]:
                The bounding box within which to constrain placement of atoms.
                In the form [[a_min, a_max], [b_min, b_max], [c_min, c_max]].
                Values given in direct (crystal) coordinates, ranging from 0 to 1.
            return_grid : bool
                Whether to return the number of grid points along each axis of the host.

            Returns
            -------
            numpy.ndarray (4 + num_species, n_points)
                The probability density of the generated structures.
            list[int]
                The grid parameters used for the generation.
            """
            probability_density = None
            ret_grid = numpy.zeros(3, dtype=numpy.int32)
            if isinstance(basis, Atoms):
                basis = geom_rw.basis(atoms=basis)

            if isinstance(species, str):
                species = re.findall(r'[A-Z][a-z]?\d*', species)
                species = [re.sub(r'\d+', '', s) for s in species]

            n_coords, n_points, ret_grid = _raffle.f90wrap_generator__get_probability_density__rgt(
                this = self._handle,
                basis = basis._handle,
                species_list = species,
                grid = grid,
                grid_offset = grid_offset,
                grid_spacing = grid_spacing,
                bounds = bounds,
            )
            ret_grid = ret_grid.tolist()


            # allocate the structures
            probability_density = numpy.asfortranarray(numpy.zeros((n_coords, n_points), dtype=numpy.float32))
            _raffle.f90wrap_retrieve_probability_density(probability_density)

            if return_grid:
                return probability_density, ret_grid
            else:
                return probability_density

        def print_settings(self, file : str):
            """
            Print the settings for the generation to a file.

            Parameters
            ----------
            file : str
                Name of the file to write the settings to.
            """
            _raffle.f90wrap_generator__print_settings__binding__rgt(this=self._handle, \
                file=file)

        def read_settings(self, file : str):
            """
            Read the settings for the generation from a file.

            Parameters
            ----------
            file : str
                Name of the file to read the settings from.
            """
            _raffle.f90wrap_generator__read_settings__binding__rgt(this=self._handle, \
                file=file)

        def get_descriptor(self):
            """
            Get the descriptor for the generated structures.

            Returns
            -------
            list[numpy arrays]
                The descriptor for the generated structures.
            """
            descriptor = [
                self.distributions.get_2body(),
                self.distributions.get_3body(),
                self.distributions.get_4body()
            ]
            return descriptor

        @property
        def num_structures(self):
            """
            The number of generated structures currently stored in the generator.
            """
            return _raffle.f90wrap_raffle_generator_type__get__num_structures(self._handle)

        @num_structures.setter
        def num_structures(self, num_structures):
            _raffle.f90wrap_raffle_generator_type__set__num_structures(self._handle, \
                num_structures)

        @property
        def host(self):
            """
            The host structure for the generation.
            """
            host_handle = _raffle.f90wrap_raffle_generator_type__get__host(self._handle)
            if tuple(host_handle) in self._objs:
                host = self._objs[tuple(host_handle)]
            else:
                host = geom_rw.basis.from_handle(host_handle)
                self._objs[tuple(host_handle)] = host
            return host

        @host.setter
        def host(self, host):
            host = host._handle
            _raffle.f90wrap_raffle_generator_type__set__host(self._handle, host)

        @property
        def grid(self):
            """
            The grid parameters for the generation.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_raffle_generator_type__array__grid(self._handle)
            if array_handle in self._arrays:
                grid = self._arrays[array_handle]
            else:
                grid = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_raffle_generator_type__array__grid)
                self._arrays[array_handle] = grid
            return grid

        @grid.setter
        def grid(self, grid):
            self.grid[...] = grid

        @property
        def grid_offset(self):
            """
            The offset of the grid from the origin.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_raffle_generator_type__array__grid_offset(self._handle)
            if array_handle in self._arrays:
                grid_offset = self._arrays[array_handle]
            else:
                grid_offset = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_raffle_generator_type__array__grid_offset)
                self._arrays[array_handle] = grid_offset
            return grid_offset

        @grid_offset.setter
        def grid_offset(self, grid_offset):
            self.grid_offset[...] = grid_offset

        @property
        def grid_spacing(self):
            """
            The spacing between grid points.
            """
            return _raffle.f90wrap_raffle_generator_type__get__grid_spacing(self._handle)

        @grid_spacing.setter
        def grid_spacing(self, grid_spacing):
            _raffle.f90wrap_raffle_generator_type__set__grid_spacing(self._handle, \
                grid_spacing)

        @property
        def bounds(self):
            """
            The bounds in direct coordinates of the host cell for the generation.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_raffle_generator_type__array__bounds(self._handle)
            if array_handle in self._arrays:
                bounds = self._arrays[array_handle]
            else:
                bounds = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_raffle_generator_type__array__bounds)
                self._arrays[array_handle] = bounds
            return bounds

        @bounds.setter
        def bounds(self, bounds):
            self.bounds[...] = bounds

        @property
        def distributions(self):
            """
            The container for the distribution functions used in the generation.
            """
            distributions_handle = \
                _raffle.f90wrap_raffle_generator_type__get__distributions(self._handle)
            if tuple(distributions_handle) in self._objs:
                distributions = self._objs[tuple(distributions_handle)]
            else:
                distributions = \
                    raffle__distribs_container.distribs_container_type.from_handle(distributions_handle)
                self._objs[tuple(distributions_handle)] = distributions
            return distributions

        @distributions.setter
        def distributions(self, distributions):
            distributions = distributions._handle
            _raffle.f90wrap_raffle_generator_type__set__distributions(self._handle, \
                distributions)

        @property
        def max_attempts(self):
            """
            The maximum number of attempts to generate a structure using the walk method.
            """
            return _raffle.f90wrap_raffle_generator_type__get__max_attempts(self._handle)

        @max_attempts.setter
        def max_attempts(self, max_attempts):
            _raffle.f90wrap_raffle_generator_type__set__max_attempts(self._handle, \
                max_attempts)

        @property
        def walk_step_size_coarse(self):
            """
            The coarse step size for the walk method.
            """
            return \
                _raffle.f90wrap_raffle_generator_type__get__walk_step_size_coarse(self._handle)

        @walk_step_size_coarse.setter
        def walk_step_size_coarse(self, walk_step_size_coarse):
            _raffle.f90wrap_raffle_generator_type__set__walk_step_size_coarse(self._handle, \
                walk_step_size_coarse)

        @property
        def walk_step_size_fine(self):
            """
            The fine step size for the walk method.
            """
            return \
                _raffle.f90wrap_raffle_generator_type__get__walk_step_size_fine(self._handle)

        @walk_step_size_fine.setter
        def walk_step_size_fine(self, walk_step_size_fine):
            _raffle.f90wrap_raffle_generator_type__set__walk_step_size_fine(self._handle, \
                walk_step_size_fine)

        @property
        def method_ratio(self):
            """
            The last used ratio of methods to employ to generate a structure.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_raffle_generator_type__array__method_ratio(self._handle)
            if array_handle in self._arrays:
                method_ratio = self._arrays[array_handle]
            else:
                method_ratio = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_raffle_generator_type__array__method_ratio)
                self._arrays[array_handle] = method_ratio
            return method_ratio

        @method_ratio.setter
        def method_ratio(self, method_ratio):
            self.method_ratio[...] = method_ratio

        @property
        def method_ratio_default(self):
            """
            The default ratio of methods to employ to generate a structure.
            """
            array_ndim, array_type, array_shape, array_handle = \
                _raffle.f90wrap_raffle_generator_type__array__method_ratio_default(self._handle)
            if array_handle in self._arrays:
                method_ratio = self._arrays[array_handle]
            else:
                method_ratio = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _raffle.f90wrap_raffle_generator_type__array__method_ratio)
                self._arrays[array_handle] = method_ratio
            return method_ratio

        @method_ratio_default.setter
        def method_ratio_default(self, method_ratio):
            self.method_ratio_default[...] = method_ratio

        def _init_array_structures(self):
            """
            Initialise the structures array.

            It is not recommended to use this function directly. Use the `structures` property instead.
            """
            self.structures = f90wrap.runtime.FortranDerivedTypeArray(self,
                                            _raffle.f90wrap_raffle_generator_type__array_getitem__structures,
                                            _raffle.f90wrap_raffle_generator_type__array_setitem__structures,
                                            _raffle.f90wrap_raffle_generator_type__array_len__structures,
                                            """
            Element items ftype=type(basis_type) pytype=basis

            """, Geom_Rw.basis)
            return self.structures

        def __str__(self):
            ret = ['<raffle_generator>{\n']
            ret.append('    num_structures : ')
            ret.append(repr(self.num_structures))
            ret.append(',\n    host : ')
            ret.append(repr(self.host))
            ret.append(',\n    grid : ')
            ret.append(repr(self.grid))
            ret.append(',\n    grid_offset : ')
            ret.append(repr(self.grid_offset))
            ret.append(',\n    grid_spacing : ')
            ret.append(repr(self.grid_spacing))
            ret.append(',\n    bounds : ')
            ret.append(repr(self.bounds))
            ret.append(',\n    distributions : ')
            ret.append(repr(self.distributions))
            ret.append(',\n    max_attempts : ')
            ret.append(repr(self.max_attempts))
            ret.append(',\n    method_ratio : ')
            ret.append(repr(self.method_ratio))
            ret.append(',\n    structures : ')
            ret.append(repr(self.structures))
            ret.append('}')
            return ''.join(ret)

        _dt_array_initialisers = [_init_array_structures]


    _dt_array_initialisers = []


generator = Generator()

class Raffle(f90wrap.runtime.FortranModule):
    """
    Module raffle
    """
    pass
    _dt_array_initialisers = []


raffle = Raffle()
