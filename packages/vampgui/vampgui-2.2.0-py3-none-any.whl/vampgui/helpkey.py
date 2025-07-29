# -*- coding: utf-8 -*-
#
# copyright (c) 06-2024 G. Benabdellah
# Departement of physic
# University of Tiaret , Algeria
# E-mail ghlam.benabdellah@gmail.com
#
# this program is part of VAMgui 
# first creation 28-05-2024
#  
#
# License: GNU General Public License v3.0
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#  log change:
#
#  text of VAMPIRE 6 manual


import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import font as tkfont
 
        
def show_help(keywords):
    if keywords == "applied-field-strengths ":
        keywords="applied-field-strength "
    if keywords == "applied-field-unit-vectors=":
        keywords="applied-field-unit-vector="
    if keywords == "macro-cell-sizes=":
        keywords="macro-cell-size="
    if keywords == "magnetisation-lengths ":
        keywords="magnetisation-length "
    if keywords == "material-magnetisations ":
        keywords="material-magnetisation " 
    if keywords == "mean-magnetisation-lengths ":
        keywords="mean-magnetisation-length " 
    if keywords == "temperatures ":
        keywords="temperature "
    if  keywords == "temperature. ":
        keywords="temperature "
    if keywords == "time-steps. ":
        keywords="time-steps " 
        
    help_content = ""
    keyword=keywords.strip()
    keyword=keyword.strip("=")
    
    help_content ="                     VAMPIRE 6 manual:   https://vampire.york.ac.uk/resources/release-6/vampire-manual.pdf\n\n"         
    help_content += f"   {keyword} : "
    help_content += "\n"

# material: help keywords -------------------------------------------------------    
    if keyword == "num-materials":
        help_content += "=integer [1-100; default 1]\n Defines the number of materials to be used in the simulation, and must be the first uncommented line in the file. If more than n materials are defined, then only the first n materials are actually used. The maximum number of different materials is currently limited to 100. If using a custom unit cell then the number of materials in the unit cell cell must match the number of materials here, otherwise the code will produce an error."
    elif keyword == "material-name": 
        help_content += " = string [default material#n]\n  Defines an identifying name for the material with a maximum length of xx characters. The identifying name is only used in the output files and does not affect the running of the code."
    elif keyword == "damping-constant": 
        help_content += " = float [0.0-10.0; default 1.0]\n Defines the phenomenological relaxation rate (damping) in dynamic simulations using the LLG equation. For equilibrium properties the damping should be set to 1 (critical damping), while for realistic dynamics the damping should be representative of the material. Typical values range from 0.005 to 0.1 for most materials."
    elif keyword == "exchange-matrix[1]": 
        help_content += " = float [default 0.0 J/link]\n Defines the pairwise exchange energy between atoms of type index and neighbour-index. The pairwise exchange energy is independent of the coordination number, and so the total exchange integral will depend on the number of nearest neighbours for the crystal lattice. The exchange energy must be defined between all material pairs in the simulation, with positive values representing ferromagnetic coupling, and negative values representing anti ferromagnetic coupling. ….VAMPIRE  User Manual p64."
    elif keyword == "exchange-matrix-1st-nn[1]": 
        help_content += " = float [default 0.0 J/link]\n Defines the pairwise exchange energy between atoms of type index and neighbour-index for the first nearest neighbour shell when using the built in exchange functions. This is exactly the same as the usual parameter exchange-matrix[index] but with a more specific syntax including the shell number of 1."
    elif keyword == "exchange-matrix-2nd-nn[1]": 
        help_content += " = float [default 0.0 J/link]\n Defines the pairwise exchange energy between atoms of type index and neighbour-index for the second nearest neighbour shell when using the built in exchange functions. If you are using the generic crystal structures available in VAMPIRE, then it is possible to define a longer ranged Hamiltonian with next-nearest up to 10th nearest neighbour interactions. The interaction shells refer to sets ofneighbours with the same interaction range from a target atom. To define a longer range Hamiltonian you need to define the input file parameters exchange:interaction-range = R  and exchange:function = shell, where R is the interaction range as a multiple of the nearest neighbour distance.….VAMPIRE  User Manual p64."
    elif keyword == "exchange-matrix-3rd-nn[1]": 
        help_content += " = float [default 0.0 J/link] \n Defines the pairwise exchange energy between atoms of type index and neighbour-index for the third nearest neighbour shell when using the built in exchange functions. See 2nd neighbour description for more details on using this feature." 
    elif keyword == "exchange-matrix-4th-nn[1]": 
        help_content += " = float [default 0.0 J/link] \n Defines the pairwise exchange energy between atoms of type index and neigh bour-index for the fourth nearest neighbour shell when using the built in exchange functions. See 2nd neighbour description for more details on using this feature."
    elif keyword == "biquadratic-exchange-matrix[1]": 
        help_content += " = float [default 0.0 J/link]\n Defines the pairwise biquadratic exchange energy between atoms of type index and neighbour-index. The pair wise exchange energy is independent of the coordination number, and so the total exchange integral will depend on the number of neighbours for the crystal lattice. The exchange energy must be defined between all material pairs in the simulation, with positive values representing ferromagnetic coupling, and negative values representing anti ferromagnetic coupling.….VAMPIRE  User Manual p65."
    elif keyword == "atomic-spin-moment": 
        help_content += " = float [0.01+ uB , default 1.72 uB ] it must be in the range 0.1 - 1e8 mu_B. \n Defines the local effective spin moment for each atomic site. Atomic moments can be found from ab-initio calculations or derived from low temperature measurements of the saturation magnetisation.….VAMPIRE  User Manual p65."
    elif keyword == "uniaxial-anisotropy-constant": 
        help_content += " = float [default 0.0 J/atom]\n Defines the local second order single-ion magnetocrystalline anisotropy constant at each atomic site. .….VAMPIRE  User Manual p66."
    elif keyword == "second-order-uniaxial-anisotropy-constant": 
        help_content += " = float [default 0.0J/atom]\n Has the same meaning and is the preferred form for material:fourth-order-uniaxial-anisotropy-constant = float [default 0.0J/atom] Implements fourth order uniaxial anisotropy as implemented with spherical harmonics."
    elif keyword == "cubic-anisotropy-constant": 
        help_content += " = float [default 0.0 J/atom]\n Defines the local cubic magnetocrystalline anisotropy constant at each atomic site. The anisotropy energy is given by the expression Ei = +1/4*kc(Sx^4+Sy^4+Sz^4),where Sx,y,z are the components of the local spin direction and kc is the cubic anisotropy constant. Positive values of kc give a preferred easy axis orientation along the [001] directions, medium-hard along the [110] directions and hard along the [111] directions. Negative values give a preferred easy direction along the [111] directions, medium ahead along the [110] directions and hard along the[100] directions." 
    elif keyword == "fourth-order-cubic-anisotropy-constant": 
        help_content += " = float [default 0.0 J/atom]\n Has the same meaning and preferred form for materialcubic-anisotropy-constant."
    elif keyword == "uniaxial-anisotropy-direction": 
        help_content += " = float  vector|random|random-grain [default (0,0,1)]\n A unitvector ei describing the magnetic easy axis direction for uniaxial anisotropy. The vector is entered in comma delimited form - For example: material[1]:uniaxial-anisotropy-direction = 0,0,1 The unit vector is self normalising and so the direction can be expressed in standard form (with length r = 1) or in terms of crystallographic directions,. .….VAMPIRE  User Manual p67."
    elif keyword == "surface-anisotropy-constant": 
        help_content += " = float [default 0.0 (J/atom)] \n Describes the surface anisotropy constant in the Néel pair anisotropy model. The anisotropy is given by a summation over nearest neighbour atoms  .….VAMPIRE  User Manual p67."
    elif keyword == "neel-anisotropy-constant[1]": 
        help_content += " = float [default 0.0 J] \n Has the same meaning and is the preferred form for material:surface-anisotropy-constant."
    elif keyword == "lattice-anisotropy-constant": 
        help_content += " = float [default 0.0 J/atom]\n Defines anisotropy arising from temperature dependent lattice expansion such as in RETM alloys. The temperature dependence of the lattice anisotropy is defined with a user defined function specified in the parameterlattice-anisotropy-file."
    elif keyword == "lattice-anisotropy-file": 
        help_content += " = string \n Defines a file containing the temperature dependence of anisotropy arising from lattice expansion. The first line of the file specifies the number of points, followed by a list of pairs indicating the temperature (in K) and normalised lattice anisotropy, typically of order 1 at T = 0K. The specified points are linearly interpolated by the code and so excessively high resolution is not required for high accuracy, and 1 K resolution is typically sufficient for most problems."
    elif keyword == "voltage-controlled-magnetic-anisotropy-coefficient": 
        help_content += " = float [default 0.0 J/V]\n Defines the material-dependent magnetic anisotropy induced by an applied voltage. Here the easy axis is always assumed along z, and so a positive coefficient will add uniaxial anisotropy along the z-direction. The coefficient is multiplied by spin-transport:applied-voltage and so has units of J/V (or Coulombs), with typical values in the range 0.1 − 10 × 10−21 J / volt."
    elif keyword == "relative-gamma": 
        help_content += " = float [default 1] \nDefines the gyromagnetic ratio of the material relative to that of the electron  gamma_e=1.76 T^-1 s^−1 . Valid values are in the range 0.01 - 100.0. For most materials gamma_r = 1."
    elif keyword == "initial-spin-direction": 
        help_content += "= float vector /bool [default (001) / false] \n Determines the initial direction of the spins in the material. Value can wither be a unit  vector defining a direction in space, or a boolean which initialises each spin to a different random direction (equivalent to infinite temperature). As with other unit vectors, a normalised value or crystallographic notation (e.g. [110]) may be used."
    elif keyword == "material-element": 
        help_content += "= string [default Fe]\n Defines a purely descriptive chemical element for the material, which gives visual contrast in a range of interactive atomic structure viewers such as jmol, rasmol etc. This parameter has no relevance to the simulation at all, and only appears when outputting atomic coordinates, which can be post-processed to be viewable in rasmol." 
    elif keyword == "geometry-file": 
        help_content += "= string [default ""] \nSpecifies a filename containing a series of connected points in space which is used to cut a specified shape from the material, in a process similar to lithography. The first line defines the total number of points, which must be in the range 3-100 (A minimum of three points is required to define a  polygon). The points are normalised to the sample size, and so all points are defined as x, y pairs in the range 0-1, with one point per line. The last point is automatically connected first, so need not be defined twice."
    elif keyword == "host-alloy": 
        help_content += "=flag [default off ] \nScans over all other materials to replace the desired fraction of host atoms with alloy atoms. This is primarily used to create random alloys of materials with different properties (such as FeCo, NiFe) or disordered ferrimagnets (such as GdFeCo)."
    elif keyword == "alloy-fraction[1]": 
        help_content += " = float [ 0-1 : default 0.0 ] \nDefines the fractional number of atoms of the host material to be replaced by atoms of material index."
    elif keyword == "minimum-height": 
        help_content += " = float [ 0-1 : default 0.0 ] \nDefines the minimum height of the material as a fraction of the total height z of the system. By defining different minimum and maximum heights it is easy to define a multilayer system consisting of different materials, such as FM/AFM, or ECC recording media..….VAMPIRE  User Manual p69."
    elif keyword == "maximum-height": 
        help_content += " = float [ 0-1 : default 1.0 ] \n Defines the maximum height of the material as a fraction of the total height z of the system. See  ,minimum-height, for more details."
    elif keyword == "core-shell-size": 
        help_content += " = float [ 0-1 : default 1.0 ] \nDefines the radial extent of a material as a fraction of the particle radius. This parameter is used to generate core-shell nanoparticles consisting of two or more distinct layers. The core-shell-size is compatible with spherical, ellipsoidal, cylindrical, truncated octahedral and cuboid shaped particles. In addition when particle arrays are generated all particles are also core-shell type. This option is also comparable with the minimum/maximum-height options, allowing for partially filled or coated nanoparticles."
    elif keyword == "interface-roughness": 
        help_content += " = float [ 0-1 : default 1.0 ]\n Defines interfacial roughness in multilayer systems."
    elif keyword == "intermixing[1]": 
        help_content += " = float [ 0-1 : default 1.0 ]\n Defines intermixing between adjacent materials in multilayer systems. The intermixing is defined as a fraction of the total system height, and so small values are usually used. The intermixing defines the mixing of material index into the host material, and can be asymmetric (a -> b != b -> a)."
    elif keyword == "density": 
        help_content += " = float [ 0-1 : default 1.0 ] \n Defines the fraction of atoms to remove randomly from the material (density)."
    elif keyword == "continuous": 
        help_content += " = flag [ default off ] \n Defines materials which ignore granular CSG operations, such as particles, voronoi media and particle arrays."
    elif keyword == "fill-space": 
        help_content += " = flag [ default off ] \n Defines materials which obey granular CSG operations, such as particles, voronoi media and particle arrays, but in-fill the void created. This is useful for embedded nanoparticles and recording media with dilute interlayer coupling."
    elif keyword == "couple-to-phononic-temperature": 
        help_content += " = flag [ default off ]\n Couples the spin system of the material to the phonon temperature instead of the electron temperature in pulsed heating simulations utilising the two temperature model. Typically used for rare-earth elements."
    elif keyword == "temperature-rescaling-exponent": 
        help_content += " = float [ 0-10 : default 1.0 ] \n Defines the exponent when rescaled temperature calculations are used. The higher the exponent the flatter the magnetisation is at low temperature. This parameter must be used with temperature-rescaling-curie-temperature to have any effect."
    elif keyword == "temperature-rescaling-curie-temperature": 
        help_content += " = float [ 0-10,000 : default 0.0 ]\n Defines the Curie temperature of the material to which temperature rescaling is applied."
    elif keyword == "non-magnetic": 
        help_content += "=flag [default remove]\n Defines atoms of that material as being non-magnetic. Non-magnetic atoms by default are removed from the simulation and play no role in the simulation. If configuration output is specified then the positions of the non-magnetic atoms are saved and processed by thevdc utility. This preserves the existence of non-magnetic atoms when generating visualisations but without needing to simulate them artificially. The \"keep\" option preserves the non-magnetic atoms in the simulation for parallelization efficiency but instructs the dipole field solver to ignore them for improved accuracy."

    elif keyword == "unit-cell-category": 
        help_content += " = integer [ default 0 ] \n Allocates different materials to different atoms in the unit cell. In complex crystals such as spinel and rocksalt, the material allocations of different atoms in the unit cell are defined by the structure. For example, in the rocksalt structure there are two distinct types of atoms. Material 1 could be allocated to this site using material[1]:unit-cell-category =1, and a second material could be allocated to the second site using material[2]:unit-cell-category = 2. The default value of this variable is 0, and so for complex crystals only a single site is defined and the other sites will not be generated unless a material is attached to it in this way. \n This keyword also works with the create:crystal-sublattice-materials flag to allocate different materials to different sites in the simple crystals bcc, fcc, hcp and kagome. This feature is especially useful for simulating simple antiferromagnets and materials with different kinds of defects or site specific alloying."
# ---------Create help keyword-----------------------------------------Add help content for each keyword
    elif keyword == "full":
        help_content += "Uses the entire generated system without any truncation or consideration of the create:particle-size parameter. create:full should be used when importing a complete system, such as a complete nanoparticle and where a further definition of the system shape is not required. This is the default if no system truncation is defined."
    elif keyword == "cube":
        help_content += " Cuts a cuboid particle of size lx = ly = lz = create:particle-size from the defined crystal lattice."
    elif keyword == "cylinder":
        help_content += " Cuts a cylindrical particle of diameter create:particle-size from the defined crystal lattice. The height of the cylinder extends to the whole extent of the system size create:system-size-z in the z-direction."
    elif keyword == "ellipsoid":
        help_content += " Cuts an ellipsoid particle of diameter create:particle-size with fractional diameters of dimensions:particle-shape-factor-x, dimensions:particle-shape-factor-y, dimensions:particle-shape-factor-z from the defined crystal lattice."
    elif keyword == "sphere":
        help_content += " Cuts a spherical particle of diameter create:particle-size from the defined crystal lattice."
    elif keyword == "truncated-octahedron":
        help_content += " Cuts a truncated octahedron particle of diameter create:particle-size from the defined crystal lattice."
    elif keyword == "particle":
        help_content += "Defines the creation of a single particle at the centre of the defined system. If create:particle-size is greater than the system dimensions then the outer boundary of the particle is truncated by the system dimensions."
    elif keyword == "particle-array":
        help_content += " Defines the creation of a two-dimensional array of particles on a square lattice. The particles are separated by a distance create:particle-spacing. If the system size is insufficient to contain at least a single entire particle of size create:particle-size then no atoms will be generated and the program will terminate with an error."
    elif keyword == "voronoi-film":
        help_content += " Generates a two-dimensional voronoi structure of particles, with a mean grain size of create:particle-size and variance create:voronoi-size-variance as a fraction of the grain size. If create:voronoi-size-variance=0 then hexagonal shaped grains are generated. The spacing between the grains (defined by the initial voronoi seed points) is controlled by create:particle-spacing. The pseudo-random pattern uses a predefined random seed, and so the generated structure will be the same every time. A different structure can be generated by setting a new random seed using the create:voronoi-random-seed parameter.\n Depending on the desired edge structure, the first row can be shifted using the create:voronoi-row-offset flag which changes the start point of the voronoi pattern. The create:voronoi-rounded-grains parameter generates a voronoi structure, but then applies a grain rounding algorithm to remove the sharp edges."
    elif keyword == "voronoi-size-variance":
        help_content += " =[float]\n Controls the randomness of the voronoi grain structure. The voronoi structure is generated using a hexagonal array of seed points appropriately spaced according to the particle size and particle spacing. The seed points are then displaced in x and y according to a gaussian distribution of width create:voronoi-size-variance times the particle size. The variance must be in the range 0.0-1.0.\n Typical values for a realistic looking grain structure are less than 0.2, and larger values will generally lead to oblique grain shapes and a large size distribution."
    elif keyword == "voronoi-row-offset":
        help_content += " [default false]\n Offsets the first row of hexagonal points to generate a different pattern, e.g. 2,3,2 grains instead of 3,2,3 grains."
    elif keyword == "voronoi-random-seed":
        help_content += "= integer \n Sets a different integer random seed for the voronoi seed point generation, and thus produces a different random grain structure."
    elif keyword == "voronoi-rounded-grains":
        help_content += " [default false]\n Controls the rounding of voronoi grains to generate more realistic grain shapes. The algorithm works by expanding a polygon from the centre of the grain, until the total volume bounded by the edges of the grain is some fraction of the total grain area, defined by create:voronoi-rounded-grains-area. This generally leads to the removal of sharp edges."
    elif keyword == "voronoi-rounded-grains-area": 
        help_content += "  = float [0.0-1.0, default 0.9] \n Defines the fractional grain area where the expanding polygon is constrained, in the range 0.0-1.0. Values less than 1.0 will lead to truncation of the voronoi grain shapes, and very small values will generally lead to circular grains. A typical value is 0.9 for reasonable voronoi variance."
    elif keyword == "particle-centre-offset":
        help_content += "Shifts the origin of a particle to the centre of the nearest unit cell."
    elif keyword == "crystal-structure":
        help_content += " = string [sc, fcc, bcc, hcp, heusler, kagome, rocksalt,spinel; default sc] \n Defines the default crystal lattice to be generated. The code supports the basic metallic crystal types simple cubic (sc), body-centred-cubic (bcc), face-centred-cubic (fcc) and hexagonal close-packed (hcp). The code also supports important magnetic structures such as Heusler alloys (heusler), rocksalt such as NiO (rocksalt) spinels such as magnetite (spinel) and kagome lattices."
    elif keyword == "crystal-sublattice-materials":
        help_content += " = flag [true, false]; default false] \n When set or defined as true, simple crystals with more than one atom per unit cell (bcc, bcc110, fcc, hpc, and kagome) will allocate each atom in the unit cell to a different material. The material allocation to atomic sites can then be done using the usual material:unit-cell-category flags in the material file, in much the same way as for complex crystals."
    elif keyword == "single-spin":
        help_content += " =flag Overrides all create options and generates a single isolated spin."
    elif keyword == "periodic-boundaries-x":
        help_content += " flag\n Creates periodic boundaries along the x-direction."
    elif keyword == "periodic-boundaries-y":
        help_content += "Flag\n Creates periodic boundaries along the y-direction."
    elif keyword == "periodic-boundaries-z":
        help_content += " Flag\nCreates periodic boundaries along the z-direction."
    elif keyword == "periodic-boundaries":
        help_content += " =flag [yz |zx|xy| ]\nCreates periodic boundaries along user-defined directions. If left empty this sets periodic boundaries along the xyz-directions. If set to any combination of x, y, z it sets the commensurate directions. For example create:periodic-boundaries = yz will set the periodic boundary conditions along the y and z directions."
    elif keyword == "select-material-by-height":
        help_content += " Specifies that materials are preferentially assigned by their height specification."
    elif keyword == "select-material-by-geometry":
        help_content += " Specifies that materials are preferentially assigned by their geometric specification (eg in core-shell systems)."
    elif keyword == "fill-core-shell-particles":
        help_content += " ... "
    elif keyword == "interfacial-roughness":
        help_content += "Specifies that a global roughness is applied to the material height specification (eg from a non-flat substrate)."
    elif keyword == "material-interfacial-roughness":
        help_content += "Specifies that a material-specific roughness is applied to the material height specification (eg from differences in local deposition rate)."
    elif keyword == "interfacial-roughness-random-seed":
        help_content += "Specifies the random seed for generating the roughness pattern, where different numbers generate different random patterns. Number should ideally be large and around 2,000,000,000."
    elif keyword == "interfacial-roughness-number-of-seed-points":
        help_content += "Determines the undulation for the roughness, where more points gives a larger undulation."
    elif keyword == "interfacial-roughness-type":
        help_content += "Determines whether the roughness is applied as peaks or troughs in the material-specific material heights. Valid options are \"peaks\" or \"troughs\"."
    elif keyword == "interfacial-roughness-seed-radius":
        help_content += " .."
    elif keyword == "interfacial-roughness-seed-radius-variance":
        help_content += ".."
    elif keyword == "interfacial-roughness-mean-height":
        help_content += "..."
    elif keyword == "interfacial-roughness-maximum-height":
        help_content += "..."
    elif keyword == "interfacial-roughness-height-field-resolution":
        help_content += "..."
    elif keyword == "alloy-random-seed":
        help_content += "= integer [default 683614233]\n Sets the random seed for the psuedo random number generator for generating random alloys. Simulations use a predictable sequence of psuedo random numbers to give repeatable results for the same simulation. The seed determines the actual sequence of numbers and is used to generate a different alloy distribution. Note that different numbers of cores will change the structure that is generated."
    elif keyword == "grain-random-seed":
        help_content += "= integer [default 1527349271]\n Sets the random seed for the psuedo random number generator for generating random grain structures."
    elif keyword == "dilution-random-seed":
        help_content += "integer=[default 465865253] Sets the random seed for the psuedo random number generator for diluting the atoms, leading to a different realization of a dilute material. Note that different numbers of cores will change the structure that is generated."
    elif keyword == "intermixing-random-seed":
        help_content += "= integer [default 100181363]\nSets the random seed for the psuedo random number generator for calculating intermixing of materials. A different seed will lead to a different realization of a dilute material. Note that different numbers of cores will change the structure that is generated."
    elif keyword == "spin-initialisation-random-seed":
        help_content += "= integer [default 123456]\n Sets the random seed for the psuedo random number generator for initialising spin directions. Note that different numbers of cores will change the spin positions that are generated."
    
#---------dimensions-----------------    
    elif keyword == "unit-cell-size": 
        help_content += "float [0.1 A- 10 μ m, default 3.54 A] Defines the size of the unit cell."
    elif keyword == "unit-cell-size-x":
        help_content += "Defines the size of the unit cell if asymmetric."
    elif keyword == "unit-cell-size-y":
        help_content += "Defines the size of the unit cell if asymmetric."
    elif keyword == "unit-cell-size-z":
        help_content += "Defines the size of the unit cell if asymmetric."
    elif keyword == "system-size":
        help_content += "Defines the size of the symmetric bulk crystal."
    elif keyword == "system-size-x":
        help_content += "Defines the total size if the system along the x-axis.\n dimensions:system-size-x  must be in the range 0.1 Angstroms - 1 millimetre "
    elif keyword == "system-size-y":
        help_content += " Defines the total size if the system along the y-axis.\n dimensions:system-size-z  must be in the range 0.1 Angstroms - 1 millimetre "
    elif keyword == "system-size-z":
        help_content += "Defines the total size if the system along the z-axis.\n dimensions:system-size-z  must be in the range 0.1 Angstroms - 1 millimetre "
    elif keyword == "particle-size":
        help_content += "[float]\n Defines the size of particles cut from the bulk crystal."
    elif keyword == "particle-spacing":
        help_content += "Defines the spacing between particles in particle arrays or voronoi media."
    elif keyword == "particle-shape-factor-x":
        help_content += "float [0.001-1, default 1.0]\nModifies the default particle shape to create elongated particles. The selected particle shape is modified by changing the effective particle size in the x direction. This property scales the as a fraction of the particle-size along the x-direction."
    elif keyword == "particle-shape-factor-y":
        help_content += "float [0.001-1, default 1.0]\Modifies the default particle shape to create elongated particles. The selected particle shape is modified by changing the effective particle size in the y direction. This property scales the as a fraction of the particle-size along the y-direction."
    elif keyword == "particle-shape-factor-z":
        help_content += "float [0.001-1, default 1.0]\nModifies the default particle shape to create elongated particles. The selected particle shape is modified by changing the effective particle size in the z direction. This property scales the as a fraction of the particle-size along the z-direction."
    elif keyword == "particle-array-offset-x":
        help_content += "[0-104 A] \nTranslates the 2-D particle array the chosen distance along the x-direction."
    elif keyword == "particle-array-offset-y":
        help_content += "Translates the 2-D particle array the chosen distance along the y-direction."
    elif keyword == "macro-cell-size":
        help_content += "0.0 Angstroms - 1 millimetre \nDetermines the macro cell size for calculation of the demagnetizing field and output of the magnetic configuration. Finer discretisation leads to more accurate results at the cost of significantly longer run times. The cell size should always be less than the system size, as highly asymmetric cells will lead to significant errors in the demagnetisation field calculation.s"

# -----------Exchange-----
    
    elif keyword == "interaction-range":
        help_content += "Determines the cutoff range exchange interactionsfor built-in crystal structures in terms of the nearest neighbour range. Larger ranges will enable more interactions via an exchange function which can include 2nd-10th nearest neighbour interaction shells or exponential functions. Note that longer ranged interactions are slower to calculate. In shell mode the computed interaction shells are printed in the log file."
    elif keyword == "function": 
        help_content += "Determines the type of interaction to be used in the spin Hamiltonian. The default nearest neighbour option forces nearest neighbour interactions only. The shell option groups neighbours at the same interaction distance into shells which can then be assigned different exchange constants. The exponential option implements an exponential decay that is useful for simulating spin glasses and systems such as NdFeB where there are no well-defined neighbour shells. The material-exponential function is similar to exponential, however it allows different exponential exchange functions to be defined for different inter-material type (for materials as defined in the unit-cell module) interactions e.g. in NdFeB Nd-Fe interactions can have a different function defined vs Fe-Fe interactions."
    elif keyword == "decay-multiplier":
        help_content += "Determines the value of A to be used in A exp −r/B+C for exchange:function = exponential."
    elif keyword == "decay-length": 
        help_content += "Determines the value of B to be used in A exp−r/B +C for exchange:function = exponential."
    elif keyword == "decay-shift":
        help_content += "Determines the value of C to be used in A exp −r/B + C for exchange:function = exponential."

    elif keyword == "ucc-exchange-parameters[i][j]": 
        help_content += "This is used in conjunction with exchange:function = material-exchange. i and j represent the unit cell category(material as per unit cell module) of the interacting atoms that the user wishes to set the exponential exchange function for. This variable is set to the three comma separated values: A, exchange:decay-multiplier; B, exchange:decay-length; C, exchange:decay-shift in this order."
    elif keyword == "dmi-cutoff-range":
        help_content += "Determines the cutoff range for i-j-k interactions for the built-in DMI in VAMPIRE."
    elif keyword == "ab-initio": 
        help_content += "Interprets exchange constants in the ab-initio sense and applies a factor 2 increase in the strength of the exchange constants."
            
# --------------Anisotropy calculation---------------
    elif keyword == "surface-anisotropy-threshold":
        help_content += "= integer [default native] \n Determines minimal number of neighbours to classify as surface atom. The defaultb value is the number of neighbours specified by the crystal or unit cell file. You can set this as a lower threshold."
    elif keyword == "surface-anisotropy-nearest-neighbour-range":
        help_content += "= float [default infinity]\n Sets the interaction range for the nearest neighbour list used for the surface anisotropy calculation."
    elif keyword == "enable-bulk-neel-anisotropy":
        help_content += "= bool [default false] \nEnables calculation of the Néel pair anisotropy in the bulk, irrespective of the number of neighbours, enabling the effect of localised spin-orbit interactions. Internally this sets a large threshold, and so specifying anisotropy:surface-anisotropy-threshold will override this flag."

    elif keyword == "neel-anisotropy-exponential-range":
        help_content += "= float [default 2.5] \nEnables an exponentially range dependent Néel pair anisotropy so that lattice distortions and strains change the magnetoelastic compling strength. In the usual form the method only takes into account the symmetry (Lij (r) = const). The value should be set to the typical lattice parameter otherwise the total anisotropy will be significantly higher or lower than expected. The functional form of the range dependence is …. VAMPIRE 6 Manual … p45"

    elif keyword == "neel-anisotropy-exponential-factor":
        help_content += "= float [default 5.52] \n Enables an exponentially range dependent Néel pair anisotropy so that lattice distortions and strains change the magnetoelastic compling strength. In the usual form the method only takes into account the symmetry (Lij (r) = const). The prefactorcontrols the falloff with increasing range." 
# --------------------Dipole-------------------------------------------
    elif keyword == "solver":
        help_content += "=  exclusive string [default tensor]\n The following commands control the calculation of the dipole-dipole field. By default the dipole fields are disabled for performance reasons, but for large systems (> 10 nm) the interactions can become important. The VAMPIRE code implements several different solvers balancing accuracy and performance. The default in V5+ is the tensor method, which approximates the dipole dipole interactions at the macrocell level but calculating a dipole-dipole tensor which is exact if the magnetic moments in each cell are aligned.\n\n dipole:solver Declares the solver to be used for the dipole calculation. Available options are:\n\n  macrocell\n  tensor\n   atomistic"
 # ---------------------HAMR calculation---------------------------------    
    elif keyword == "laser-FWHM-x":  
        help_content += " = float [default 20.0 nm]\n    Defines the full width at half maximum of the Gaussian temperature profile in x-direction in the program hamr-simulation with default units of Angstrom and a default value of 20 nm."
    elif keyword == "laser-FWHM-y":  
        help_content += " = float [default 20.0 nm]\n  Defines the full width at half maximum of the Gaussian temperature profile in y-direction in the program hamr-simulation with default units of Angstrom and a default value of 20 nm."
    elif keyword == "head-speed":  
        help_content += " = float [default 30.0 m/s]\n Defines the speed of the head sweeping over the medium in the program hamr-simulation with default units of Angstrom/second and a default value of 30 m/s. "

    elif keyword == "head-field-x":  
        help_content += " = float [default 20.0 nm]\n Defines the full width of the box in x-direction where the magnetic field is applied in the program hamr-simulation with default units of Angstrom and a default value of 20 nm."

    elif keyword == "head-field-y":  
        help_content += " = float [default 20.0 nm]\n Defines the full width of the box in y-direction where the magnetic field is applied in the program hamr-simulation with default units of Angstrom and a default value of 20 nm." 

    elif keyword == "field-rise-time":  
        help_content += " = float [default 1 ps]\n Defines the field linear rise time in the program hamr-simulation with default units of seconds and a default value of 1 ps." 

    elif keyword == "field-fall-time":  
        help_content += " = float [default 1 ps]\n Defines the field linear fall time in the program hamr-simulation with default units of seconds and a default value of 1 ps."

    elif keyword == "NPS":  
        help_content += " = float [default 0.0 nm]\n Defines the shift between the centre of the temperature pulse and the centre of the box defined by hamr:head-field-x and hamr:head-field-y in the program hamr-simulation with default units of Angstrom and a default value of 0 nm. The parameter can be also parsed via the key hamr:NFT-to-pole-spacing."

    elif keyword == "bit-size":  
        help_content += " = float [default 0.0 nm]\n Defines the size of the bit along x (down-track) in the program hamr-simulation with default units of Angstrom and a default value of 0 nm. The parameter can be also parsed via the key hamr:bit-length."

    elif keyword == "track-size":  
        help_content += " = float [default 0.0 nm]\n Defines the size of the bit along y (cross-track), i.e. the track size of the bit pattern, in the program hamr-simulation with default units of Angstrom and a default value of 0 nm. The parameter can be also parsed via the key hamr:track-width."

    elif keyword == "track-padding":  
        help_content += " = float [default 0.0 nm]\n  Defines the spacing between the edges of the system along y (cross-track) and the written bit pattern in the program hamr-simulation with default units of Angstrom and a default value of 0 nm."

    elif keyword == "number-of-bits":  
        help_content += " = int [default 0]\n  Defines the number of bits to be written in total in the program hamr-simulation with default value of 0. If the system it too small for the number of bits requested, the sequence is truncated to adapt it to the system. "

    elif keyword == "bit-sequence-type":  
        help_content += " = exclusive string [default text]\n Specifies the format type of bit sequence to be simulated in the program hamr-simulation. Available options are: \n\n single-tone-predefined \n user-defined \n\n If (single-tone-predefined) is given, a single tone adapted to the system size will be generated and hamr:bit-sequence is ignored."

    elif keyword == "bit-sequence":  
        help_content += " = integer vector Specifies the bit sequence to be simulated in the program hamr-simulation. Acceptable values are -1 (opposite to field direction), 0 (zero field) and 1 (along field direction) and by default the vector is empty."

# -------------------simulation ---------------
    elif keyword == "integrator":
        help_content += " =exclusive string [default llg-heun]\n Declares the integrator to be used for the simulation. Available options are: \n\n llg-heun \n monte-carlollg-midpoint \n constrained-monte-carlo  \n hybrid-constrained-monte-carlo"
    elif keyword == "program":
        help_content += " =exclusive string \n Defines the simulation program to be used.\n\n sim:program=benchmark :\n Program which integrates the system for 10,000 time steps and exits. Used primarily for quick performance comparisons for different system architectures, processors and during code performance optimisation.\n\n sim:program=time-series:\n Program to perform a single time series typically used for switching calculations, ferromagnetic resonance or to find equilibrium magnetic configurations. The system is usually simulated with constant temperature and applied field. The system is first equilibrated for sim:equilibration-time-steps time steps and is then integrated for sim:time-steps time steps.\n\n sim:program=hysteresis-loop :\nProgram to simulate a dynamic hysteresis loop in user defined field range and precision. The system temperature is fixed and defined by sim:temperature. The system is first equilibrated for sim:equilibration time-steps time steps at sim:maximum-applied-field-strength applied field. For normal loops sim:maximum-applied-field-strength should be a saturating field. After equilibration the system is integrated for sim:loop-time-steps at each field point. The field increments from +sim:maximum-applied-field-strength to=sim:maximum-appli-field-strength in steps of sim:applied-field-increment, and data is output after each field step.\n\n sim:program=static-hysteresis-loop :\nProgram to perform a hysteresis loop in the same way as a normal hysteresis loop, but instead of a dynamic loop the equilibrium condition is found by minimisation of the torque on the system. For static loops the temperature must be zero otherwise the torque is always finite. At each field increment the system is integrated until either the maximum torque for any one spin is less than the tolerance value (10−6 T), or if sim:loop-time-steps is reached. Generally static loops are computationally efficient, and so sim:loop-time-steps can be large, as many integration steps are only required during switching, i.e. near the coercivity.\n\n sim:program=curie-temperature \n Simulates a temperature loop to determine the Curie temperature of the system. The temperature of the system is increased stepwise, starting at sim:minimum temperature and ending at  sim:maximum-temperature in steps of sim:temperature-increment. At each temperature the system is first equilibrated for sim:equilibration-steps time steps and then a statistical average is taken over sim:loop-time-steps. In general the Monte Carlo integrator is the optimal method for determining the Curie temperature, and typically a few thousand steps is sufficient to equilibrate the system. To determine the Curie temperature it is best to plot the mean magnetization length at each temperature, which can be specified using the output:mean-magnetisation-length keyword. Typically the temperature dependent magnetization can be fitted using the function….VAMPIR 6 manual p49. \n\n sim:program=field-cooling :\n\n sim:program=temperature-pulse :\n\n sim:program=electrical-pulse: \n Simulates the effect of an electrical pulse through either spin-transfer (STT) or spin-orbit (SOT) torques, or through the spin-transport circuit theory model. The system is first equilibrated at constant temperature with zero voltage. A trapezium shaped electrical pulse is applied, linearly increasing from zero voltage to that defined in the code, held constant, then linearly decreased back to zero. In the case of direct STT and SOT simulations, the effective fields are scaled in direct proportion with the applied voltage. The pulse duration is controlled by the parameter sim:electrical-pulse-time with a rise time of sim:electrical-pulse-rise-time and fall time of sim:electrical-pulse-fall-time. The default pulse time is 1 ns, and default fall and rise times are 0, reproducing a square pulse. The time dependence of the fractional voltage can be printed in the output file with the parameter output:fractional-electric-field-strength.\n\n sim:program=cmc-anisotropy :\n Iterates through a series of angles at which the global magnetisation is contrained, allowing individual spins to vary, but preventing the system from reaching a true equilibrium. This allows for the examination of magnetocrystalline anisotropy energy and restoring torques. \n\n sim:program=hamr-simulation :\n Simulates a heat assisted magnetic recording (HAMR) writing process with a head sweeping across the medium at a speed defined by the input parameter hamr:head-speed, generating an external magnetic field of maximum magnitude sim:maximum-applied-field-strength with rise time hamr:field-rise-time and fall time hamr:field-fall-time within the  region underneath the head defined by the parameters hamr:head-field-x and hamr:head-field-y. The head also generates a heat pulse with Gaussian profile in the xy--plane and uniform along z defined by FWHM in x and y direction hamr:laser-FWHM-x and hamr:laser-FWHM-y respectively, minimum and maximum values of the Gaussian sim:minimum-temperature and sim:maximum-temperature, respectively. The desired number of bits to be written and bit sequence are defined via hamr:number-of-bits, hamr:bit-sequence-type and hamr:bit-sequence parameters, whereas hamr:bit-size/hamr:bit-length and hamr:track-size/hamr:track-width set the bit dimension in down-track and cross-track respectively. The margin between the edge of the system and the written tracks in cross-track is specified via hamr:track-padding, while hamr:NPS/hamr:NFT-to-pole-spacing set the shift between the centre of application of the external field and temperature pulse."
    elif keyword == "enable-dipole-fields":
        help_content += "flag \n Enables calculation of the demagnetising field."
    elif keyword == "enable-fmr-field":
        help_content +=  "No additional help available for this keyword."
    elif keyword == "enable-fast-dipole-fields":
        help_content += "=Bool [default false]\n Enables fast calculation of the demag field by pre calculation of the interaction matrix."
    elif keyword == "field-update-rate":
        help_content += "=integer [default 1000]\n Number of timesteps between recalculation of the demag field. Default value is suitable for slow calculations, fast dynamics will generally require much faster update rates."
    elif keyword == "time-step":
        help_content += "The timestep for the evolution of the system, determines how long a simulation will take. \n It must be in the range 0.01 attosecond - 1 picosecond."
    elif keyword == "total-time-steps":
        help_content += "The total number of time steps the program will run for."
    elif keyword == "loop-time-steps":
        help_content += "The number of time steps that statistics are taken over, including the mean-magnetisation and material-standard-deviation. This takes place after sim:equilibration time steps have passed in simulations such as program:curie-temperature."
    elif keyword == "time-steps-increment":
        help_content +=  "No additional help available for this keyword."
    elif keyword == "equilibration-time-steps":
        help_content += "The number of simulation time steps that the system is allowed to equilibrate for at each temperature. Statistics are not taken over this range."
    elif keyword == "simulation-cycles":
        help_content +=  "No additional help available for this keyword."
    elif keyword == "maximum-temperature":
        help_content += "The maximum temperature in a simulation over a temperature series, such as sim:program=curie-temperature."
    elif keyword == "minimum-temperature":
        help_content += "The minimum temperature in a simulation over a temperature series, such as sim:program=curie-temperature."
    elif keyword == "equilibration-temperature":
        help_content += "The temperature at which a simulation equilibrates, for example, prior to the temperature pulse in sim:program=temperature-pulse"
    elif keyword == "temperature":
        help_content += "The temperature of the simulation."
    elif keyword == "temperature-increment":
        help_content += "The temperature step size in a simulation over a temperature series, such as sim:program=curie-temperature.\n It must be in the range 1.0e-10 - 1000000 K. "
    elif keyword == "cooling-time":
        help_content +=  "No additional help available for this keyword."
    elif keyword == "laser-pulse-temporal-profile":
        help_content += "The shape of the laser temperature pulse in time, used in sim:program=temperature-pulse. \n\n Square two-temperature \n double-pulse-two-temperature \n double-pulse-square"
    elif keyword == "laser-pulse-time":
        help_content += "The length of the laser temperature pulse in time, used in sim:program=temperature-pulse."
    elif keyword == "laser-pulse-power":
        help_content += "The fluence of the laser temperature pulse, used in sim:program=temperature-pulse."
    elif keyword == "second-laser-pulse-time":
        help_content +=  "No additional help available for this keyword."
    elif keyword == "second-laser-pulse-power":
        help_content +=  "No additional help available for this keyword."
    elif keyword == "second-laser-pulse-maximum-temperature":
        help_content += "No additional help available for this keyword."
    elif keyword == "second-laser-pulse-delay-time":
        help_content += "No additional help available for this keyword."
    elif keyword == "two-temperature-heat-sink-coupling":
        help_content += "No additional help available for this keyword."
    elif keyword == "two-temperature-electron-heat-capacity": 
        help_content += "The heat capacity of the electrons in the system, used in sim:program=emperature-pulse."
    elif keyword == "two-temperature-phonon-heat-capacity":
        help_content += "The heat capacity of the phonons in the system, used in sim:program=temperature-pulse."
    elif keyword == "two-temperature-electron-phonon-coupling":
        help_content += "Dictates the heat exchange coupling between the electrons and the phonons in the system, used in sim:program=temperature-pulse."
    elif keyword == "cooling-function":
        help_content += "Dictates the shape of the cooling curve in sim:program=field-cool simulations. Choose from:\n\n exponential \n\n gaussian \n double-gaussian \n linear"

    elif keyword == "applied-field-strength":
        help_content += "The strength of the applied external field acting on the system."
    elif keyword == "maximum-applied-field-strength":
        help_content += "The maximum strength of the applied external field acting on the system, in a magnetisation field series simulation such as sim:program=hysteresis-loop. In this simulation, this maximum is the maximum magnitude, and dictates both the maximum and minimum (±) magnetisation in the target direction."
    elif keyword == "equilibration-applied-field-strength":
        help_content += "The strength of the applied external field the system equilibrates in, in a magnetisation field series simulation such as sim:program=hysteresis-loop."
    elif keyword == "applied-field-strength-increment":
        help_content += "The increment in the strength of the applied external field acting on the system, in a magnetisation field series simulation such as sim:program=hysteresis-loop."
    elif keyword == "applied-field-angle-theta":
        help_content +=  "No additional help available for this keyword."
    elif keyword == "applied-field-angle-phi":
        help_content +=  "No additional help available for this keyword."
    elif keyword == "applied-field-unit-vector":
        help_content += "No additional help available for this keyword."
    elif keyword == "demagnetisation-factor":
        help_content += "=float vector [default (000)]\n Vector describing the components of the demagnetising factor from a macroscopic sample. By default this is disabled, and specifying a demagnetisation factor adds an effective field, such that the total field is given by:\n Htot=Hext + Hint − M · Nd \n where M is the magnetisation of the sample and Nd is the demagnetisation factor of the macroscopic sample. The components of the demagnetisation factor must sum to 1. In general the demagnetisation factor should be used without the dipolar field, as this results in counting the demagnetising effects twice. However, the possibility of using both is not prevented by the code."
    elif keyword == "integrator-random-seed":
        help_content += "=integer [default 12345]\n Sets a seed for the psuedo random number generator. Simulations use a predictable sequence of psuedo random numbers to give repeatable results for the same simulation. The seed determines the actual sequence of numbers and is used to give a different realisation of the same simulation which is useful for determining statistical properties of the system."
    elif keyword == "constraint-rotation-update":
        help_content +=  "No additional help available for this keyword."
    elif keyword == "constraint-angle-theta":
        help_content += "=float (default 0)  When a constrained integrator is used in a normal program, this variable controls the angle of the magnetisation of the whole system from the x-axis [degrees]. In constrained simulations (such as cmc anisotropy) this has no effect."

    elif keyword == "constraint-angle-theta-minimum":
        help_content += "float (default 0)\n The minimum angle of theta that the global magnetisation is constrained to in a constrained angle series, used in sim:program=cmc-anisotropy."
    elif keyword == "constraint-angle-theta-maximum":
        help_content += "The maximum angle of theta that the global magnetisation is constrained to in a constrained angle series, used in  sim:program=cmc-anisotropy."
    elif keyword == "constraint-angle-theta-increment":
        help_content += "=float [0.001-360, default 5] \nIncremen tal Change of the angle of global magnetisation from z-direction in constrained simulations. Controls the resolution of the angular sweep. sim:constraint-angle-phi When a constrained integrator is used in a normal program, this variable controls the angle of the magnetisation of the whole system from the x-axis [degrees]. In constrained simulations (such as cmc anisotropy) this has no effect."
    elif keyword == "constraint-angle-phi-minimum":
        help_content += "The minimum angle of phi that the global magnetisation is constrained to in a constrained angle series, used in sim:program=cmc-anisotropy."
    elif keyword == "constraint-angle-phi-maximum":
        help_content += "The maximum angle of phi that the global magnetisation is constrained to in a constrained angle series, used in sim:program=cmc-anisotropy."
    elif keyword == "constraint-angle-phi-increment":
        help_content += "Incremental Change of the angle of global magnetisation from z-direction in constrained simulations. Controls the resolution of the angular sweep."
    elif keyword == "checkpoint":
        help_content += "flag [default false]\n Enables checkpointing of spin configuration at end of the simulation. The options are:\n\nsim:save-checkpoint=end \n sim:save-checkpoint=continuous \nsim:save-checkpoint-rate=1 \nsim:load-checkpoint=restart \n sim:load-checkpoint=continue\n "
    elif keyword == "preconditioning-steps":
        help_content += "=integer [default 0] \nDefines a number of preconditioning steps to thermalise the spins at sim:equilibration-temperature prior to the main simulation starting. The preconditioner uses a Monte Carlo algorithm to develop a Boltzmann spin distribution prior to the main program starting. The method works in serial and parallel mode and is especially efficient for materials with low Gilbert damping. The preconditioning steps are applied after loading a checkpoint, allowing you to take a low temperature starting state and thermally equilibrate it."
    elif keyword == "electrical-pulse-time":
        help_content += "=float [default 1.0 ns] \n Defines the pulse time in the program electrical-pulse with default units of seconds and a default pulse time of 1 ns."
    elif keyword == "electrical-pulse-rise-time":
        help_content += "=float [default 0.0 ns] \n Defines the pulse linear rise time in the program electrical-pulse with default units of seconds and a default pulse time of 0, i.e. an instantaneous turning on of the current."
    elif keyword == "electrical-pulse-fall-time":
        help_content += "=float [default 0.0 ns] \n Defines the pulse linear fall time in the program electrical-pulse with default units of seconds and a default pulse time of 0, i.e. an instantaneous turning off of the current. "
# -----------montecarlo:  ------------------------
    elif keyword == "algorithm":
        help_content += "Selects the trial move algorithm for use with the Monte Carlo solver. The following options are available: \n\n adaptive (default) \n spin-flip \n uniform \n angle \nhinzke-nowak \n\n The adaptive move performs a gaussian move with a tuned trial width to attempt to maintain a 50% acceptance probability, and is the most efficient method in most cases. A spin flip flips the direction of the spin 180◦ and can be used to perform Ising-type simulations for a uniform starting configuration. Uniform moves a spin to a random location on the unit sphere. Angle performs a gaussian move with a parametric estimate of the optimal width. Hinzke-Nowak performs a random combination of spin-flip, uniform and angle type-moves."
    elif keyword == "constrain-by-grain":
        help_content += "Applies a local constraint in granular systems so that the magnetisation within individual grains is conserved along the global constraint directions sim:constrain-phi and sim:constraint-theta. Without this additional constraint, the system will tend to demagnetise and form a demagnetised state (with zero torque). With this parameter defined it is possible to determine grain-level properties and distributions of the Curie temperature and anisotropy."
# -----------output config:  ------------------------
    elif keyword == "time-steps": 
        help_content += "Outputs the number of time steps (or Monte Carlo steps) completed during the simulation so far. "
    elif keyword == "real-time":
        help_content += "Outputs the simulation time in seconds. The real time is given by the number of time steps multiplied by sim:time-step (default value is 1.0 ×10−15 s). The real time has no meaning for Monte Carlo simulations."
    elif keyword == "temperature.":
        help_content += "Outputs the instantaneous system temperature in Kelvin. "
    elif keyword == "applied-field-strengths":
        help_content += "Outputs the strength of the applied field in Tesla. For hysteresis simulations the sign of the applied field strength changes along a fixed axis and is represented in the output by a similar change in sign."
    elif keyword == "applied-field-unit-vectors":
        help_content += "Outputs a unit vector in three columns ^hx , ^hy ,^hz indicating the direction of the external applied field."
    elif keyword == "applied-field-alignment":
        help_content += "Outputs the dot product of the net magnetization direction of the system with the external applied field direction ^m· ^H."
    elif keyword == "material-applied-field-alignment":
        help_content += "Outputs the dot product of the net magnetization direction of each material  defined in the material file with the external applied field direction [m1 · H], [m2 · H] …"
    elif keyword == "magnetisation":
        help_content += "Outputs the instantaneous magnetization of the system.  The data is output in four columns mx , my , mz , |m| giving the unit vector direction of the magnetization and normalized length of the magnetization respectively. sum The normalized of all moments length in the of the system magnetization assuming …. VAMPIRE 6 manual p56"
    elif keyword == "mean-magnetisation-length":
        help_content += "Outputs the time-averaged normalized magnetization length <|m|>."
    elif keyword == "mean-magnetisation":
        help_content += "Outputs the time-averaged normalized magnetization vector <|m|>."
    elif keyword == "material-magnetisation":
        help_content += "Outputs the instantaneous normalized magnetization for each material in the simulation. The data is output in blocks of four columns, with one block per material defined in the material file, ….. Note that obtaining the actual macroscopic magnetization length from this data is not trivial, since it is necessary to know how many atoms of each material are in the system. This information is contained within the log file (giving the fraction of atoms which make up each material). However it is usual to also output the total normalized magnetization of the system to give the relative ordering of the entire system."
    elif keyword == "material-mean-magnetisation-length":
        help_content += "Outputs the time-averaged normalized magnetization length for each material, e.g. <|m1|>, <|m2|>…"
    elif keyword == "material-mean-magnetisation":
        help_content += "Outputs the time-averaged normalized magnetization length for each material, e.g. <|m1|>, <|m2|>...<|mn |>."
    elif keyword == "total-torque":
        help_content += "Outputs the instantaneous components of the torque on  system tau  in three columns tau_x , tau_y , tau_z  (units for of Joules).  In  equilibrium  the  total  torque will  be close  to zero,  but  is  useful  for  testing convergence to an equilibrium state for zero temperature simulations."
    elif keyword == "mean-total-torque":
        help_content += "Outputs the time average of components of the torque equilibrium on the system the total <tau> torque, three   columns  <tau_x >, <tau_y>, <tau_z>. In  equilibrium  the total will  be  close  to  zero,  but  the average is useful for extracting effective anisotropies or exchange using constrained Monte Carlo simulations."
    elif keyword == "constraint-phi":
        help_content += "Outputs the current angle of constraint from the z-axis for constrained simulations using either the Lagrangian Multiplier Method (LMM) or Constrained Monte Carlo (CMC) integration methods."
    elif keyword == "constraint-theta":
        help_content += "Outputs the current angle of constraint from the x-axis for constrained simulations using either the Lagrangian Multiplier Method (LMM) or Constrained Monte Carlo (CMC) integration methods."
    elif keyword == "material-mean-torque":
        help_content += "Outputs the time average of components of the torque on the each material system <tau> in blocks of three columns, with one block for each material defined in the material file .…"
    elif keyword == "mean-susceptibility":
        help_content += "Outputs the components of the magnetic susceptibility"
    elif keyword == "material-mean-susceptibility":
        help_content += "Outputs the components of the magnetic susceptibility X for each defined material in the system. The data is output in sets of four columns Xx, Xy ,Xz , and Xm for each material. In multisublattice systems the susceptibility of each sublattice can be different."
    elif keyword == "material-standard-deviation":
        help_content += "Outputs the standard deviation in the components of the instantaneous normalized magnetization for each material in the simulation. The data is output in blocks of four columns, with one block per material defined in the material file, e.g… The statistic is taken over the range of values gathered during the loop-time-steps after equilibration."
    elif keyword == "electron-temperature":
        help_content += "Outputs the instantaneous electron temperature as calculated from the two temperature model."
    elif keyword == "phonon-temperature":
        help_content += "Outputs the instantaneous phonon (lattice) temperature as calculated from the two temperature model."
    elif keyword == "total-energy":
        help_content +=  "No additional help available for this keyword."
    elif keyword == "mean-total-energy":
        help_content += "No additional help available for this keyword."
    elif keyword == "anisotropy-energy":
        help_content += "No additional help available for this keyword."
    elif keyword == "mean-anisotropy-energy":
        help_content += "No additional help available for this keyword."
    elif keyword == "exchange-energy":
        help_content += "No additional help available for this keyword."
    elif keyword == "mean-exchange-energy":
        help_content += "No additional help available for this keyword."
    elif keyword == "applied-field-energy":
        help_content += "No additional help available for this keyword."
    elif keyword == "mean-applied-field-energy":
        help_content += "No additional help available for this keyword."
    elif keyword == "magnetostatic-energy":
        help_content += "No additional help available for this keyword."
    elif keyword == "mean-magnetostatic-energy":
        help_content += "No additional help available for this keyword."
    elif keyword == "material-total-energy":
        help_content += "Outputs the total energy of each material in the system."
    elif keyword == "material-mean-total-energy":
        help_content += "Outputs the mean total energy of each material in the system."
    elif keyword == "mean-specific-heat":
        help_content += "Outputs the mean total specific heat Cv …"
    elif keyword == "material-mean-specific-heat":
        help_content += "Outputs the mean specific heat for each defined material in the system in units of k_B per spin. The data is formatted as one column per material."
    elif keyword == "fractional-electric-field-strength":
        help_content += "Outputs the fractional electric field strngth (or voltage) during an electrical-pulse simulation."
    elif keyword == "mpi-timings":
        help_content +=  "No additional help available for this keyword."
    elif keyword == "gnuplot-array-format":
        help_content += "No additional help available for this keyword."
    elif keyword == "output-rate":
        help_content += "= integer [default 1]\n Controls the number of data points written to the output file or printed to screen. By default VAMPIRE calculates statistics once every sim:time-steps-increment number of time steps. Usually you want to output the updated statistic (e.g. magnetization) every time, which is the default behaviour. However, sometimes you may want to plot the time evolution of an average, where you want to collect statistics much more frequently than you output to the output file, which is controlled by this keyword. For example, if output:output-rate = 10 and sim:time-steps-increment = 10 then statistics (and average values) will be updated once every 10 time steps, and the new statistics will be written to the output file every 100 time steps."
    elif keyword == "precision":
        help_content += "= integer [default 6]\nControls the number of digits to be used for data written to the output file or printed to screen. The default value is 6 digits of precision."
    elif keyword == "fixed-width":
        help_content += "= flag [default false]\nControls the formatting to be used for data written to the output file or printed to screen. The default is false which ignores trailing zeros in the output."

    elif keyword == "atoms":
        help_content += "flag [atoms continuous end (default false)]\n Enables the output of atomic spin configurations either at the end of the simulations or during the simulation. The options are: \n config:atoms to output continuously during the simulation \n config:atoms=continuous   to output continuously during the simulation (same as previous option) \n config:atoms=end   to output at the end of the simulation."
    elif keyword == "atoms-output-rate":
        help_content += "= integer [0+, default 1000]\nDetermines the rate configuration files are outputted as a multiple of sim:time-steps-increment. It is considered only if config:atoms=continuous or is empty. The following options allow a cubic slice of the total configuration data to be output to the configuration file. This is useful for reducing disk usage and processing times, especially for large sale simulations."
    elif keyword == "atoms-minimum-x":
        help_content += "= float [0.0 – 1.0]\nDetermines the minimum x value (as a fraction of the total system dimensions) of the data slice to be outputted to the configuration file."
    elif keyword == "atoms-minimum-y":
        help_content += "Determines the minimum y value (as a fraction of the total system dimensions) of the data slice to be outputted to the configuration file."
    elif keyword == "atoms-minimum-z":
        help_content += "Determines the minimum z value (as a fraction of the total system dimensions) of the data slice to be outputted to the configuration file."
    elif keyword == "atoms-maximum-x":
        help_content += "Determines the maximum x value (as a fraction of the total system dimensions) of the data slice to be outputted to the configuration file."
    elif keyword == "atoms-maximum-y":
        help_content += "Determines the maximum y value (as a fraction of the total system dimensions) of the data slice to be outputted to the configuration file."
    elif keyword == "atoms-maximum-z":
        help_content += "Determines the maximum z value (as a fraction of the total system dimensions) of the data slice to be outputted to the configuration file."
    elif keyword == "macro-cells":
        help_content += "flag [  =continuous  =end default false]\nEnables the output of macro cell spin configurations either at the end of the simulations or during the simulation. The options are: \nconfig:macro-cells  to output continuously during the simulation \nconfig:macro-cells=continuous   to output continuously during the simulation (same as previous option) \n config:macro-cells=end to output at the end of the simulation"
    elif keyword == "macro-cells-output-rate":
        help_content += "Determines the rate configuration files are outputted as a multiple of sim:time-steps-increment. It is considered only if config:macro-cells = continuous or is empty"
    elif keyword == "output-format":
        help_content += "= exclusive string [text binary default text]\n Specifies the format of the configuration data. Available options are:\n text \n binary\n The text option outputs data files as plain text, allowing them to be read by a wide range of applications and hence the highest portability. There is a performance cost to using text mode and so this is recommended only if you need portable data and will not be using the vampire data converter (vdc) utility.\n The binary option outputs the data in binary format and is typically 100 times faster than text mode. This is important for large-scale simulations on large numbers of processors where the data output can take a significant amount of time. Binary files are generally not compatible between operating systems and so the vdc tools generally needs to be run on the same system which generated the files."
    elif keyword == "output-mode":
        help_content += "= exclusive string [file-per-node file-per-process mpi-io (default file-per-node)]\n Specifies how configuration data is outputted to disk. Available options are:\n file-per-node \n file-per-process \n mpi-io \n Using this option is important for obtaining good performance on Tier-0 (Euro-pean) and Tier-1 (National) supercomputers for simulations typically using more than 1000 cores. Large scale supercomputers have high performance parallel file ….VAMPIRE 6 manual p62"
    elif keyword == "output-nodes":
        help_content += "= int [default 1] \nSpecifies the number of files to be generated per snapshot. For typical small scale simulations (on a single physical node) the default value of 1 is fine. For larger scale simulations more output nodes are beneficial to achieve maximum performance, with one output node per physical node being a sensible choice, but this can be specified up to the maximum number of processes in the simulation."
    elif keyword == "column-headers":
        help_content += "output column headers [default false]"  

# visualization ---------------
    elif keyword == "--xyz": 
        help_content += " vdc --xyz \n to generate  .xyz format for viewing in vesta, rasmol/jmol"
    elif keyword == "--povray":
        help_content += " vdc --povray \n To generate povray files, Data output in PoVRAY format for rendering"
    elif keyword == "--vtk": 
        help_content += "vdc --vtk \n To generate vtk files, Data output in VTK format for viewing in Paraview"
    elif keyword == "--text":
        help_content += "--text \n To  generate plain text file, Data output in plain text format for plotting in gnuplot/excel etc"
    elif keyword == "--custom-colourmap" :
        help_content += """---custom-colourmap  filename \n A user defined colourmap can also be used. To apply a different map, a file containing 256 colours in the RBG format must be provided in the same directory that VDC is run. RGB values must be space separated, with no other information such as line numbers. The beginning of an  example colourmap is shown below. Pregenerated perceptually uniform colourmaps of various forms, including those included in vampire by default. 
                        custom_colourmap_file
                        0.000000 0.000000 0.000000
                        0.005561 0.005563 0.005563
                        0.011212 0.011219 0.011217
                        0.016877 0.016885 0.016883
                        0.022438 0.022448 0.022445
                        0.027998 0.028011 0.028008
                        0.033540 0.033554 0.033551
                        0.039316 0.039333 0.039329
                        0.044700 0.044719 0.044714
                        0.049695 0.049713 0.049709
                        0.054322 0.054343 0.054338 """
    elif keyword == "--spin-spin-correlation":
        help_content += "--spin-spin-correlation \n Spin-spin correlation data in text format "
    elif keyword == "--3D":
        help_content += "--3D   \n POV-Ray images produced by VDC can have a 3D brightening effect applied. Spins which do not line only in the yz-plane have their brightness adjusted according to their x-axis spin component."
    elif keyword == "--verbose":
        help_content += "--verbose \n set verbose output to screen"
    elif keyword == "--vector-z":
        help_content += "vector-z = float vector(3) [default {0,0,1}] \n The principle axis, along which colour is applied, is the z-axis. This determines where colours will occur depending on the colourmap being used. By default the CBWR map is used; spins along the positive z-direction are red, those along the negative z-direction are blue, and spins aligned along the xy-plane are white.\n In many cases, the overall magnetic moment does not necessarily lie along the z-axis. To remedy this, a new vector-z may be defined. To redefine the z-axis, use the parameter vector-z followed by a direction vector. This does not need to be normalised. \nFor example, if the user defines vector-z = {1,1,1}, spins along the {1,1,1} direction will be red, {-1,-1,-1} will be blue and those perpendicular to the given axis will be white. Brackets can be omitted."
    elif keyword == "--vector-x":
        help_content += "--vector-x  float vector(3) [default {0,0,1}]\n In some cases, the colourmap may not be symmetric along the default xy-plane, such as the C2 colourmap. Here, spins along positive-y are magenta, while those antiparallel are green. This can be adjusted using a similar command line argument vector-x, however this argument cannot be used without first defining vector-z."
    elif keyword == "--slice":
        help_content += "--slice float vector(6) [0-1 : default {0,1,0,1,0,1}] \nThe first slice type defines minimum and maximum values for each axis. Only atoms and spins inside these boundaries are included in the visualisation. The parameters passed to this argument are interpreted as fractional coordinates."
    elif keyword == "--slice-void":
        help_content += "--slice-void  float vector(6) [0-1 : default not set] \nThis parameter will remove all atoms and spins inside the given borders. This can be used to create cubic hollow systems where only surface atoms are shown, removing a very high percentage of atoms in the system, which can greatly reduce rendering time for both POV-Ray and Rasmol."
    elif keyword == "--slice-sphere":
        help_content += "--slice-sphere float vector(3) [0-1 : xfrac,yfrac,zfrac]\n The sphere slice is also used to remove the atoms and spins at the centre of a system. This particular parameter lends itself well to spherical systems as it removes a spherical section of atoms. Three parameters are required, instead of six. Each one defines a region, centred on the centre of the original system, along the respective axis, equal to a fraction of the system size along that axis. As these parameters are not necessarily equal to each other, this can be used to create an ellipse of missing atoms at the centre of the system."
    elif keyword == "--slice-cylinder":
        help_content += "--slice-cylinder  float vector(4) [0-1 : xfrac,yfrac,zmin,zmax] \n This slice parameter can be used to remove all atoms outside a cylindracal section by defining the x,y-fractional sizes as well as a fractional minimum and maximum along the z-axis "
    elif keyword == "--frame-start":
        help_content += "--frame-start  integer [default 0] \nDepending on output options used in VAMPIRE, multiple frames may be rendered by VDC. frame-start can be used to skip an initial number of frames."
    elif keyword == "--frame-final":
        help_content += "--frame-final integer [default 0] \n Depending on output options used in VAMPIRE, multiple frames may be rendered by VDC. frame-final can be used to skip later frames."
    elif keyword == "--remove-material":
        help_content += "--remove-material  integer [one or more values] \n In some cases whole materials are not relevant for visualisation purposes and can be altogether removed. To use this command line parameter a list of material indices need to be provided. Material indices start from 1."
    elif keyword == "--afm":
        help_content += "--fm  intger [one or more values] \nPOV-Ray visualization of antiferromagnets can be difficult due to the contrast of colours of antiparallel spins. To remedy this, it is possible to define materials as antiferromagnetic. These materials will have their colours flipped so that they match neighbouring spins while their spin direction remains antiferromagnetic."
    elif keyword == "--colourmap":
        help_content += "--colourmap string [default CBWR] By default, a 1D colourmap is used. Aligned  along the z-axis, spins in the {0,0,1} direction are red, while spins antiparallel to this {0,0,-1} are blue. Between these values, the colour transitions to white around the xy-plane. This corresponds to the CBWR colourmap, a cyclic blue-white-red map, which lends itself well to 1D or 2D spin sytems where there are two principle spin directions, such as antiferromagnets and ferrimagnets. Some care must  be taken to align the principle spin directions with the z-axis, as this is the axis along which colour is applied. This can also be changed using the vector-z input parameter. There are several choices of possible colourmap configurations, the ones provided by default are made to be perceptually uniform and in some cases  take account of colourblindness. Information on the colourmaps, the importance  of perceptually uniform maps and how to adapt and use different maps can be  found from 'Peter Kovesi. Good Colour Maps: How to Design Them. 2015' The C2 coloumap is also cyclic and useful for 3D magnetic systems such as vortex states. It has four principle directions of magenta, yellow, green and blue. As it is cyclic, there will be a smooth transition between colour at all angles, irrespective "
        
    elif keyword == "ufc_file":
        help_content +="""
                        1| # Unit cell size:
                        2| ucx ucy ucz
                        3| # Unit cell vectors:
                        4| ucvxx  ucvxy  ucvxz
                        5| ucvyx  ucvyy  ucvyz
                        6| ucvzx  ucvzy  ucvzz
                        7| # Atoms
                        8| num_atoms_in_unit_cell number_of_materials
                        9| atom_id cx cy cz [mat_id cat_id hcat_id]
                        10| …
                        11| # Interactions
                        12| num_interactions [exchange_type]
                        13| IID  i  j  dxuc  dyuc  dzuc | Jij
                        14|                             | Jx Jy Jz
                        15|                             | Jxx Jxy Jxz Jyx Jyy Jyz Jzx Jzy Jzz
                        16| …
                        In general this format now allows the specification of any system we want, but clearly complex multilayered systems require large file sizes. Working through line by line:
                        1--   “#” defines a comment line which is ignored by the parser – so these lines are optional.
                        2-- ucx, ucy and ucz are the unit cell size in angstroms.
                        4-6- These lines define the shape of the unit cell to be replicated, for cubic cells this is the unit matrix
                        8--   Define the number of atoms, number of materials, and anisotropy type in the unit cell.Materials allow grouping of atoms by material, and should have the same parameters 
                        (ie moment, damping, etc). Material specification affects the way statistics are collected anddisplayed, and also allows the simple creation of order alloys.The list of atoms must immediately follow this line.
                        9-10- These lines define the atoms in each unit cell and their parameters: 
                            atom_id Number:  identifier of atom in unit cell, starts at 0.
                            cx,cy,cz      :  unit cell coordinates as a fraction of unit cell size 
                            mat_id material id of the atom: integer starting at 0
                            cat_id category id of the atom: used for calculating properties not categorised by material, eg height or sublattice. Integer starting at 0.
                            hcat_id height category id: used for calculating properties as a function of height 
                        12--Defines the total number of interactions for the unit cell and the expected type of exchange:(0=isotropic, 1=vector, 2=tensor). 
                            If omitted then interactions are taken from the material input file specification. No lines are allowed between this line and the list of interactions.
                        13-- These lines list all the interactions. IID Interaction ID – only used for accounting purposes, starts at 0.
                              i Atom number of atom in local unit cell
                              j Atom number of atom in local/remote unit cell
                              dxuc,dyuc,dzuc: relative integer coordinates of unit cell for atom j
                              Jij, Jxx… Exchange values (zepto Joules [10-21 Joules]), Positive energy convention.
                        Positive energy convention means that aligning energies are negative, and repulsive energies are positive. In the case of exchange negative is FM, positive is AFM."""
                        
                        
    
   
   
   
   
   
   
   
   
    else:
        help_content += "No additional help available for this keyword."

    keys =["material:[","material:", "sim:","create:","exchange:","anisotropy:", "dipole:","hamr:", "montecarlo", "config:","output:",f"{keyword}" ]
    
    def apply_tags(keys):
        # Get the content of the text widget
        content = text_widget.get("1.0", "end")
        # Clear previous tags
        text_widget.tag_remove("bold_italic", "1.0", "end")
        # Find and tag occurrences of the keywords
        for key in keys:
            start_index = "1.0"
            while True:
                start_index = text_widget.search(key, start_index, stopindex="end", nocase=True)
                if not start_index:
                    break
                end_index = f"{start_index}+{len(key)}c"
                end_index = text_widget.search(r"\s", f"{start_index}+{len(keyword)+1}c", stopindex="end", regexp=True)
                if not end_index:
                    end_index = "end"
                text_widget.tag_add("bold_italic", start_index, end_index)
                start_index = f"{end_index}+1c"
                #text_widget.tag_add("bold_italic", start_index, end_index)
                #start_index = end_index
        # Apply bold and italic styles to the tagged text
        text_widget.tag_configure("bold_italic", font=("Helvetica", 12, "bold italic"))

    # Create the main window
    root = tk.Tk()
    root.title("Help keyword")
    root.geometry("700x500")

    # Display the file content in a text widget
    text_widget = tk.Text(root, wrap="word", bg="white", font=12, padx=10 )
    text_widget.pack(fill="both", expand=True)
    text_widget.insert("1.0", help_content)
     
    apply_tags(keys)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    #messagebox.showinfo("Help keyword", str(help_content))


        
    
    
    
    
    
    
    
    
    
