"""
Definições de tipos (também conhecidos como "schemas") do modelo de dados e funções utilitárias.

Por convenção:

*  `xxxxSpec` é um tipo que corresponde a (valida/é validada por) uma sub-árvore em uma entrada JSON.
*  `xxxxSet` é um tipo enum que especifica alternativas válidas.

Todas as especificações podem ser introspectadas com os métodos `.schema` e `.schema_json`:

     python -c "from data_model import *; print(ImovelSpec.schema())" 
     python -c "from data_model import *; print(ImovelSpec.schema_json())"

"""
from pydantic import BaseModel, PositiveFloat
from typing import List, Any, Tuple
from enum import Enum
import numpy as np
import pyproj
from umba import JIT

BRL = float
unit_id = str
Interval = Tuple[float, float]


@jit
def _to_planar_transform(lat : float, lon : float) -> float:
    """ Recebe números lat, lon e returna números utm_norte, utm_leste
    Usado internamente
    """
    wgs84=pyproj.Proj("+init=EPSG:4326") # LatLon with WGS84 datum used by GPS units and Google Earth
    utm23=pyproj.Proj("+init=EPSG:32723") # WGS 84 / UTM zone 23S
    return pyproj.transform(wgs84,utm23,self.lat,self.lon)

class LocationSpec(BaseModel):
    """Objeto especifica um ponto no espaço e é inicializado com uma tupla (lat,lon).
    (Na validação de JSON essa tupla é uma arary JS com dois números.)

    Uma vez inicializado contém as coordenadas em formato UTM e o cálculo de distâncias
    para 
    """
    def __init__(self, location : Tuple[float,float]):
        self.location = location
        self.lat = self.location.coordinates[0]
        self.lon = self.location.coordinates[1]
        self.utm_north, self.utm_east = _to_planar_transform(self.lat, self.lon)
    def __init_from_abbrev__(self,abbrev_object):
        self.__init__(self, location = abbrev_object.location)
    def utm_distance(self,utm_north : float, utm_east: float, p: int = 2) -> float:
        """Distância (Lp) para um ponto definido por coordenadas UTM"""
        dy = np.power(np.abs(utm_north - self.utm_north),p)
        dx = np.power(np.abs(utm_east - self.utm_east),p)
        return dx + dy
    def lat_lon_distance(self, lat: float, lon: float, p : int = 2) -> float:
        """Distância (Lp) para um ponto definido por coordenadas lat/lon"""
        new_north, new_east = _to_planar_transform(lat, lon)
        return self.utm_distance(utm_north = new_north, utm_east = new_east, p = p)
    def loc_distance(self, other : LocationSpec, p : int = 2) -> float:
        """Distância (Lp) para outro LocationSpec. """
        return self.utm_distance(self, other.utm_north, utm_east, p)


class TransactionSet(str, Enum):
    """Tipo de transação: `aluguel` ou `venda` """
    rental = "aluguel"
    sale = "venda"

class CitySet(str, Enum):
    """Cidade: atualmente só estão implementados `sp` e `rj` """
    sp_capital = "sp"
    rj_capital = "rj"

class ModelSpec(BaseModel):
    """Os modelos de regressão estão indexados a um par (transação, cidade)"""
    city : CitySet
    transaction : TransactionSet
    def spec(self):
        return self.city.value, self.transaction.value
    def __str__(self):
        return f"{self.city.value}_{self.transaction.value}"


class AVM_AbbrevSpecm(BaseModel):
    """API definida pelo Renan"""
    city   : CitySet
    transacao   : TransactionSet
    condominio  : BRL
    quartos     : int
    banheiros   : int
    vagas       : int
    area        : float
    suites      : int
    lat         : float
    lon         : float
    @property
    def location(self):
        return (self.lat, self.on)

class AddressSpec(BaseModel):
    """Esquema de endereço herdado da base de dados"""
    street : str
    streetNumber: str
    unitNumber: str
    floor: int
    complement: str
    neighborhood: str
    city: str
    state: str
    country: str
    cityCode: str
    zipCode: str
    zone: str
    location: LocationSpec
    def __str__(self):
        return f"{self.street}, {self.streetNuber}/{self.unitNumber} (andar {self.floor})\n"+ \
               f"{self.neighborhood}\n" +\
               f"{self.city, self.state}" +\
               f"{self.zipCode} -- {self.country}"



class UnitSpec(BaseModel):
    """ Especificação de um imóvel. 
    """
    model_context : ModelSpec
    other_costs  : BRL # condomínio
    parkingSets : Interval
    suites : Interval
    bathrooms : Interval
    bedrooms : Interval
    location: LocationSpec #OU
    # address : AddressSpec
    # @property
    # def location(self):
    #   return self.address.location
