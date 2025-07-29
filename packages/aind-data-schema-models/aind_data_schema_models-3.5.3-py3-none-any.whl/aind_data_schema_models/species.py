"""Species"""

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Annotated

from aind_data_schema_models.registries import Registry


class StrainModel(BaseModel):
    """Base model for a strain"""

    model_config = ConfigDict(frozen=True)
    name: str
    species: str
    registry: Registry.ONE_OF
    registry_identifier: str


class _C57Bl_6J(StrainModel):
    """Model C57BL/6J"""

    name: Literal["C57BL/6J"] = "C57BL/6J"
    species: Literal["Mus musculus"] = "Mus musculus"
    registry: Registry.ONE_OF = Registry.MGI
    registry_identifier: Literal["MGI:3028467"] = "MGI:3028467"


class _Balb_C(StrainModel):
    """Model BALB/c"""

    name: Literal["BALB/c"] = "BALB/c"
    species: Literal["Mus musculus"] = "Mus musculus"
    registry: Registry.ONE_OF = Registry.MGI
    registry_identifier: Literal["MGI:2159737"] = "MGI:2159737"


class _Unknown(StrainModel):
    """Model Unknown"""

    name: Literal["Unknown"] = "Unknown"
    species: Literal["Mus musculus"] = "Mus musculus"
    registry: None = None
    registry_identifier: Literal["nan"] = "nan"


class Strain:
    """Strain"""

    C57BL_6J = _C57Bl_6J()

    BALB_C = _Balb_C()

    UNKNOWN = _Unknown()

    ALL = tuple(StrainModel.__subclasses__())

    ONE_OF = Annotated[Union[tuple(StrainModel.__subclasses__())], Field(discriminator="name")]


class SpeciesModel(BaseModel):
    """Base model for species"""

    model_config = ConfigDict(frozen=True)
    name: str
    registry: Registry.ONE_OF
    registry_identifier: str


class _Callithrix_Jacchus(SpeciesModel):
    """Model Callithrix jacchus"""

    name: Literal["Callithrix jacchus"] = "Callithrix jacchus"
    registry: Registry.ONE_OF = Registry.NCBI
    registry_identifier: Literal["NCBI:txid9483"] = "NCBI:txid9483"


class _Homo_Sapiens(SpeciesModel):
    """Model Homo sapiens"""

    name: Literal["Homo sapiens"] = "Homo sapiens"
    registry: Registry.ONE_OF = Registry.NCBI
    registry_identifier: Literal["NCBI:txid9606"] = "NCBI:txid9606"


class _Macaca_Mulatta(SpeciesModel):
    """Model Macaca mulatta"""

    name: Literal["Macaca mulatta"] = "Macaca mulatta"
    registry: Registry.ONE_OF = Registry.NCBI
    registry_identifier: Literal["NCBI:txid9544"] = "NCBI:txid9544"


class _Mus_Musculus(SpeciesModel):
    """Model Mus musculus"""

    name: Literal["Mus musculus"] = "Mus musculus"
    registry: Registry.ONE_OF = Registry.NCBI
    registry_identifier: Literal["NCBI:txid10090"] = "NCBI:txid10090"


class _Rattus_Norvegicus(SpeciesModel):
    """Model Rattus norvegicus"""

    name: Literal["Rattus norvegicus"] = "Rattus norvegicus"
    registry: Registry.ONE_OF = Registry.NCBI
    registry_identifier: Literal["NCBI:txid10116"] = "NCBI:txid10116"


class _Gallus_Gallus(SpeciesModel):
    """Model Gallus gallus"""

    name: Literal["Gallus gallus"] = "Gallus gallus"
    registry: Registry.ONE_OF = Registry.NCBI
    registry_identifier: Literal["NCBI:txid9031"] = "NCBI:txid9031"


class _Oryctolagus_Cuniculus(SpeciesModel):
    """Model Oryctolagus cuniculus"""

    name: Literal["Oryctolagus cuniculus"] = "Oryctolagus cuniculus"
    registry: Registry.ONE_OF = Registry.NCBI
    registry_identifier: Literal["NCBI:txid9986"] = "NCBI:txid9986"


class _Cavia_Porcellus(SpeciesModel):
    """Model Cavia porcellus"""

    name: Literal["Cavia porcellus"] = "Cavia porcellus"
    registry: Registry.ONE_OF = Registry.NCBI
    registry_identifier: Literal["NCBI:txid10141"] = "NCBI:txid10141"


class _Carpa_Hircus(SpeciesModel):
    """Model Carpa hircus"""

    name: Literal["Carpa hircus"] = "Carpa hircus"
    registry: Registry.ONE_OF = Registry.NCBI
    registry_identifier: Literal["NCBI:txid9925"] = "NCBI:txid9925"


class _Equus_Asinus(SpeciesModel):
    """Model Equus asinus"""

    name: Literal["Equus asinus"] = "Equus asinus"
    registry: Registry.ONE_OF = Registry.NCBI
    registry_identifier: Literal["NCBI:txid9793"] = "NCBI:txid9793"


class _Lama_Glama(SpeciesModel):
    """Model Lama glama"""

    name: Literal["Lama glama"] = "Lama glama"
    registry: Registry.ONE_OF = Registry.NCBI
    registry_identifier: Literal["NCBI:txid9844"] = "NCBI:txid9844"


class _Vicuna_Pacos(SpeciesModel):
    """Model Vicuna pacos"""

    name: Literal["Vicuna pacos"] = "Vicuna pacos"
    registry: Registry.ONE_OF = Registry.NCBI
    registry_identifier: Literal["NCBI:txid30538"] = "NCBI:txid30538"


class Species:
    """Species"""

    CALLITHRIX_JACCHUS = _Callithrix_Jacchus()
    HOMO_SAPIENS = _Homo_Sapiens()
    MACACA_MULATTA = _Macaca_Mulatta()
    MUS_MUSCULUS = _Mus_Musculus()
    RATTUS_NORVEGICUS = _Rattus_Norvegicus()
    GALLUS_GALLUS = _Gallus_Gallus()
    ORYCTOLAGUS_CUNICULUS = _Oryctolagus_Cuniculus()
    CAVIA_PORCELLUS = _Cavia_Porcellus()
    CARPA_HIRCUS = _Carpa_Hircus()
    EQUUS_ASINUS = _Equus_Asinus()
    LAMA_GLAMA = _Lama_Glama()
    VICUNA_PACOS = _Vicuna_Pacos()

    ALL = tuple(SpeciesModel.__subclasses__())

    ONE_OF = Annotated[Union[tuple(SpeciesModel.__subclasses__())], Field(discriminator="name")]
