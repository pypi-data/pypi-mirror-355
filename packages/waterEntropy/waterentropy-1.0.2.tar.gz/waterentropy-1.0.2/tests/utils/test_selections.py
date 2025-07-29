""" Tests for waterEntropy selections functions in utils."""

from tests.input_files import load_inputs
import waterEntropy.utils.selections as Select

# get mda universe for arginine in solution
system = load_inputs.get_amber_arginine_soln_universe()
resid_list = [1, 2, 3]
# select all molecules above 1 UA in size
system_solutes = Select.get_selection(system, "resid", resid_list)


def test_find_solute_molecules():
    """Test the find solute molecules function"""
    # find all molecule resids larger than 1 UA in size
    resid_list_solutes = Select.find_solute_molecules(system)

    assert resid_list_solutes == [1, 2, 3]


def test_get_selection():
    """Test the get selection function"""
    # select all molecules above 1 UA in size
    solutes = Select.get_selection(system, "resid", resid_list)

    assert list(solutes.names) == [
        "H1",
        "CH3",
        "H2",
        "H3",
        "C",
        "O",
        "N",
        "H",
        "CA",
        "HA",
        "CB",
        "HB2",
        "HB3",
        "CG",
        "HG2",
        "HG3",
        "CD",
        "HD2",
        "HD3",
        "NE",
        "HE",
        "CZ",
        "NH1",
        "HH11",
        "HH12",
        "NH2",
        "HH21",
        "HH22",
        "C",
        "O",
        "N",
        "H",
        "CH3",
        "HH31",
        "HH32",
        "HH33",
    ]


def test_find_bonded_heavy_atom():
    """Test the find bonded heavy atom function"""
    # pre-defined list of solvent atom numbers
    solvent_indices = [
        621,
        1143,
        1800,
        1737,
        1413,
        888,
        1038,
        834,
        237,
        2004,
        1878,
        2688,
        2640,
        1797,
        747,
        369,
        2646,
        2019,
        168,
        2262,
        54,
        2130,
        486,
        984,
        489,
        879,
    ]
    # find the resids from the atom numbers above
    first_shell_solvent = Select.get_selection(system, "index", solvent_indices)
    # find all heavy atoms bonded to a hydrogen
    bonded_to_H = Select.find_bonded_heavy_atom(0, system_solutes)

    assert list(first_shell_solvent.resids) == [
        10,
        48,
        71,
        115,
        154,
        155,
        199,
        241,
        270,
        285,
        288,
        320,
        338,
        373,
        463,
        571,
        591,
        592,
        618,
        660,
        665,
        702,
        746,
        872,
        874,
        888,
    ]
    assert bonded_to_H.name == "CH3"


def test_find_molecule_UAs():
    """Test find molecule UAs function"""
    # find all UAs in a selection of molecules
    UAs = Select.find_molecule_UAs(system_solutes)

    assert list(UAs.names) == [
        "CH3",
        "C",
        "O",
        "N",
        "CA",
        "CB",
        "CG",
        "CD",
        "NE",
        "CZ",
        "NH1",
        "NH2",
        "C",
        "O",
        "N",
        "CH3",
    ]
