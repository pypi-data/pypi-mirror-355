import pytest
import numpy as np
import pandas as pd
from rdkit import Chem
from useful_rdkit_utils.descriptors import (
    Smi2Fp, mol2morgan_fp, smi2morgan_fp, mol2numpy_fp, smi2numpy_fp,
    RDKitDescriptors, RDKitProperties, Ro5Calculator
)

@pytest.fixture
def valid_smiles():
    return "CCO"  # Ethanol

@pytest.fixture
def invalid_smiles():
    return "INVALID"

@pytest.fixture
def mol(valid_smiles):
    return Chem.MolFromSmiles(valid_smiles)

def test_smi2fp(valid_smiles):
    smi2fp = Smi2Fp()
    fp = smi2fp.get_fp(valid_smiles)
    assert fp is not None
    np_fp = smi2fp.get_np(valid_smiles)
    assert isinstance(np_fp, np.ndarray)
    np_fp_counts = smi2fp.get_np_counts(valid_smiles)
    assert isinstance(np_fp_counts, np.ndarray)

def test_mol2morgan_fp(mol):
    fp = mol2morgan_fp(mol)
    assert fp is not None

def test_smi2morgan_fp(valid_smiles):
    fp = smi2morgan_fp(valid_smiles)
    assert fp is not None

def test_mol2numpy_fp(mol):
    arr = mol2numpy_fp(mol)
    assert isinstance(arr, np.ndarray)

def test_smi2numpy_fp(valid_smiles):
    arr = smi2numpy_fp(valid_smiles)
    assert isinstance(arr, np.ndarray)

def test_rdkit_descriptors(valid_smiles, invalid_smiles):
    rdkit_desc = RDKitDescriptors()
    desc = rdkit_desc.calc_smiles(valid_smiles)
    assert isinstance(desc, np.ndarray)
    assert len(desc) == len(rdkit_desc.desc_names)
    df = rdkit_desc.pandas_smiles([valid_smiles, invalid_smiles])
    assert df.shape[0] == 2
    assert df.shape[1] == len(rdkit_desc.desc_names)

def test_rdkit_properties(valid_smiles, invalid_smiles):
    rdkit_props = RDKitProperties()
    props = rdkit_props.calc_smiles(valid_smiles)
    assert isinstance(props, np.ndarray)
    assert len(props) == len(rdkit_props.property_names)
    df = rdkit_props.pandas_smiles([valid_smiles, invalid_smiles])
    assert df.shape[0] == 2
    assert df.shape[1] == len(rdkit_props.property_names)

def test_ro5_calculator(valid_smiles, invalid_smiles):
    ro5_calc = Ro5Calculator()
    props = ro5_calc.calc_smiles(valid_smiles)
    assert isinstance(props, np.ndarray)
    assert len(props) == len(ro5_calc.names)
    df = ro5_calc.pandas_smiles([valid_smiles, invalid_smiles])
    assert df.shape[0] == 2
    assert df.shape[1] == len(ro5_calc.names)
