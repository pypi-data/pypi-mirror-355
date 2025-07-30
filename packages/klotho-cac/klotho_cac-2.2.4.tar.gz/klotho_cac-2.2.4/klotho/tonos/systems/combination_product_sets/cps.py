from abc import ABC
from typing import Union, Dict, Tuple
from math import prod
from fractions import Fraction
import sympy as sp
import math
import networkx as nx
from tabulate import tabulate

from klotho.topos.collections import CombinationSet as CS
from klotho.tonos.utils.interval_normalization import equave_reduce

__all__ = [
    'CombinationProductSet',
    'Hexany',
    'Dekany',
    'Pentadekany',
    'Eikosany',
    'Hebdomekontany',
    'Diamond',
]

ALPHA_SYMBOLS = {chr(65 + i): sp.Symbol(chr(65 + i)) for i in range(26)}

MASTER_SETS = {
  'tetrad': {
    # Generating
    ALPHA_SYMBOLS['D'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 7/6, 'distance': math.sqrt(3.0), 'elevation': None},
    ALPHA_SYMBOLS['D'] / ALPHA_SYMBOLS['B']: {'angle': math.pi * 0/1, 'distance': math.sqrt(3.0), 'elevation': None},
    ALPHA_SYMBOLS['D'] / ALPHA_SYMBOLS['C']: {'angle': math.pi * 1/2, 'distance': math.sqrt(3.0), 'elevation': None},
    ALPHA_SYMBOLS['C'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 4/3, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['C'] / ALPHA_SYMBOLS['B']: {'angle': math.pi * 5/3, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['B'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 1/1, 'distance': 3.0, 'elevation': None},

    # Reciprocal
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['D']: {'angle': math.pi * 1/6, 'distance': math.sqrt(3.0), 'elevation': None},
    ALPHA_SYMBOLS['B'] / ALPHA_SYMBOLS['D']: {'angle': math.pi * 1/1, 'distance': math.sqrt(3.0), 'elevation': None},
    ALPHA_SYMBOLS['C'] / ALPHA_SYMBOLS['D']: {'angle': math.pi * 3/2, 'distance': math.sqrt(3.0), 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['C']: {'angle': math.pi * 1/3, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['B'] / ALPHA_SYMBOLS['C']: {'angle': math.pi * 2/3, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['B']: {'angle': math.pi * 0/1, 'distance': 3.0, 'elevation': None},
  },
  'asterisk': {
    # Generating Hexad (X/A relationships)
    ALPHA_SYMBOLS['B'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 3/2,   'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['C'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 11/10, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['D'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 7/10,  'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['E'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 3/10,  'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['F'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 19/10, 'distance': 3.0, 'elevation': None},
    
    # Reciprocal Hexad (A/X relationships)
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['B']: {'angle': math.pi * 1/2,   'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['C']: {'angle': math.pi * 1/10,  'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['D']: {'angle': math.pi * 17/10, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['E']: {'angle': math.pi * 13/10, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['F']: {'angle': math.pi * 9/10,  'distance': 3.0, 'elevation': None},
  },
  'centered_pentagon': {
    # Generating
    ALPHA_SYMBOLS['B'] / ALPHA_SYMBOLS['F']: {'angle': math.pi * 6/5, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['B'] / ALPHA_SYMBOLS['C']: {'angle': math.pi * 9/5, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['F'] / ALPHA_SYMBOLS['E']: {'angle': math.pi * 8/5, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['C'] / ALPHA_SYMBOLS['D']: {'angle': math.pi * 7/5, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['E'] / ALPHA_SYMBOLS['D']: {'angle': math.pi * 0/1, 'distance': 3.0, 'elevation': None},

    # Reciprocal
    ALPHA_SYMBOLS['F'] / ALPHA_SYMBOLS['B']: {'angle': math.pi * 1/5, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['C'] / ALPHA_SYMBOLS['B']: {'angle': math.pi * 4/5, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['E'] / ALPHA_SYMBOLS['F']: {'angle': math.pi * 3/5, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['D'] / ALPHA_SYMBOLS['C']: {'angle': math.pi * 2/5, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['D'] / ALPHA_SYMBOLS['E']: {'angle': math.pi * 1/1, 'distance': 3.0, 'elevation': None}
  },
  'hexagon': {
    # Generating
    ALPHA_SYMBOLS['C'] / ALPHA_SYMBOLS['F']: {'angle': math.pi * 5/4,   'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['C'] / ALPHA_SYMBOLS['D']: {'angle': math.pi * 7/4,   'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['F'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 17/12, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['D'] / ALPHA_SYMBOLS['B']: {'angle': math.pi * 19/12, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['E']: {'angle': math.pi * 23/12, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['B'] / ALPHA_SYMBOLS['E']: {'angle': math.pi * 13/12, 'distance': 3.0, 'elevation': None},
    
    # Reciprocal
    ALPHA_SYMBOLS['F'] / ALPHA_SYMBOLS['C']: {'angle': math.pi * 1/4,   'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['D'] / ALPHA_SYMBOLS['C']: {'angle': math.pi * 3/4,   'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['F']: {'angle': math.pi * 5/12,  'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['B'] / ALPHA_SYMBOLS['D']: {'angle': math.pi * 7/12,  'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['E'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 11/12, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['E'] / ALPHA_SYMBOLS['B']: {'angle': math.pi * 1/12,  'distance': 3.0, 'elevation': None},
  },
  'irregular_hexagon': {
    # Generating
    ALPHA_SYMBOLS['C'] / ALPHA_SYMBOLS['F']: {'angle': math.pi * 5/4,   'distance': 3.0 + 0.25, 'elevation': None},
    ALPHA_SYMBOLS['C'] / ALPHA_SYMBOLS['D']: {'angle': math.pi * 7/4,   'distance': 3.0 + 0.25, 'elevation': None},
    ALPHA_SYMBOLS['F'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 17/12, 'distance': 3.0 - 0.25, 'elevation': None},
    ALPHA_SYMBOLS['D'] / ALPHA_SYMBOLS['B']: {'angle': math.pi * 19/12, 'distance': 3.0 - 0.25, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['E']: {'angle': math.pi * 23/12, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['B'] / ALPHA_SYMBOLS['E']: {'angle': math.pi * 13/12, 'distance': 3.0, 'elevation': None},

    # Reciprocal
    ALPHA_SYMBOLS['F'] / ALPHA_SYMBOLS['C']: {'angle': math.pi * 1/4,   'distance': 3.0 + 0.25, 'elevation': None},
    ALPHA_SYMBOLS['D'] / ALPHA_SYMBOLS['C']: {'angle': math.pi * 3/4,   'distance': 3.0 + 0.25, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['F']: {'angle': math.pi * 5/12,  'distance': 3.0 - 0.25, 'elevation': None},
    ALPHA_SYMBOLS['B'] / ALPHA_SYMBOLS['D']: {'angle': math.pi * 7/12,  'distance': 3.0 - 0.25, 'elevation': None},
    ALPHA_SYMBOLS['E'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 11/12, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['E'] / ALPHA_SYMBOLS['B']: {'angle': math.pi * 1/12,  'distance': 3.0, 'elevation': None},
  },
  'ogdoad': {
    # Generating
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['B']: {'angle': math.pi * 1/2,   'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['C']: {'angle': math.pi * 3/14,  'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['D']: {'angle': math.pi * 27/14, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['E']: {'angle': math.pi * 23/14, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['F']: {'angle': math.pi * 19/14, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['G']: {'angle': math.pi * 15/14, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['A'] / ALPHA_SYMBOLS['H']: {'angle': math.pi * 11/14, 'distance': 3.0, 'elevation': None},

    # Reciprocal
    ALPHA_SYMBOLS['B'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 3/2,   'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['C'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 17/14, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['D'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 13/14, 'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['E'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 9/14,  'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['F'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 5/14,  'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['G'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 1/14,  'distance': 3.0, 'elevation': None},
    ALPHA_SYMBOLS['H'] / ALPHA_SYMBOLS['A']: {'angle': math.pi * 25/14, 'distance': 3.0, 'elevation': None},
  }
}

class CombinationProductSet(CS, ABC):
  '''
  General class for an arbitrary Combination Product Set (CPS).
  
  Abstract Base Class for Hexany, Dekany, Pentadekany, and Eikosany class implementations.
  
  A combination product set (CPS) is a scale generated by the following means:
  
      1. A set S of n positive real numbers is the starting point.
      
      2. All the combinations of k elements of the set are obtained, and their 
          products taken.
          
      3. These are combined into a set, and then all of the elements of that set 
          are divided by one of them (which one is arbitrary; if a canonical choice 
          is required, the smallest element could be used).
          
      4. The resulting elements are octave-reduced and sorted in ascending order, 
          resulting in an octave period of a periodic scale (the usual sort of 
          scale, in other words) which we may call CPS(S, k).
  
  see: https://en.xen.wiki/w/Combination_product_set
  '''
  def __init__(self, factors: Tuple[int], r: int, normalized: bool = False, master_set: str = None):
    super().__init__(factors, r)
    self._normalized = normalized
    self._master_set = master_set.lower() if master_set else None
    self._populate_graph()
    if self._master_set and self._master_set in MASTER_SETS:
      self._build_master_set_structure(MASTER_SETS[self._master_set])
    
  def _populate_graph(self):
    """Populate graph nodes with combo, product, ratio, and alias information."""
    for node, attrs in self._graph.nodes(data=True):
      if 'combo' in attrs:
        combo = attrs['combo']
        product = prod(combo)
        ratio = equave_reduce(product)
        
        if self._normalized:
          ratio = equave_reduce(ratio / max(self._factors))
        
        symbolic_expr = sp.Integer(1)
        for factor in combo:
          symbolic_expr *= self.factor_to_alias[factor]
        
        self._graph.nodes[node]['product'] = product
        self._graph.nodes[node]['ratio']   = ratio
        self._graph.nodes[node]['alias']   = symbolic_expr
  
  def _build_master_set_structure(self, relationship_dict):
    """
    Enhance the graph with edges based on relationships defined in the provided dictionary.
    
    Args:
        relationship_dict: Dictionary mapping symbolic relationships to values
    """
    if not relationship_dict:
      return
      
    combo_to_node = {}
    for node, attrs in self._graph.nodes(data=True):
      if 'combo' in attrs:
        combo_to_node[attrs['combo']] = node
    
    for c1 in self._combos:
      node1 = combo_to_node[c1]
      for c2 in self._combos:
        if c1 != c2:
          node2 = combo_to_node[c2]
          
          alias1 = self.get_attrs_by('combo', c1)['alias']
          alias2 = self.get_attrs_by('combo', c2)['alias']
          sym_ratio = sp.simplify(alias1 / alias2)
          
          if sym_ratio in relationship_dict:
            self._graph.add_edge(node1, node2, relation=sym_ratio)

  @property
  def master_set(self):
    return self._master_set
  
  @property
  def aliases(self):
    return self.factor_to_alias
    
  @property
  def products(self):
    return tuple(sorted(attrs['product'] for _, attrs in self._graph.nodes(data=True)))
  
  @property
  def ratios(self):
    return tuple(sorted(attrs['ratio'] for _, attrs in self._graph.nodes(data=True)))
  
  def get_node_by(self, attr_name, value):
    for node, attrs in self._graph.nodes(data=True):
      if attrs.get(attr_name) == value:
        return node
    return None
  
  def get_attrs_by(self, attr_name, value):
    for node, attrs in self._graph.nodes(data=True):
      if attrs.get(attr_name) == value:
        return attrs
    return None  
  
  def __str__(self):
    table_data = []
    node_data = [(attrs['combo'], attrs['product'], attrs['ratio']) for _, attrs in self._graph.nodes(data=True)]
    sorted_data = sorted(node_data, key=lambda x: x[2])
    for combo, product, ratio in sorted_data:
      table_data.append([combo, product, str(ratio)])
    return tabulate(table_data, headers=['Combo', 'Product', 'Ratio'], tablefmt='simple', colalign=('center', 'center', 'center'))
  
  def __repr__(self):
    return self.__str__()

class Hexany(CombinationProductSet):
  '''
  Calculate a Hexany scale from a list of factors and a rank value.
  
  The Hexany is a six-note scale in just intonation derived from combinations
  of prime factors, as conceptualized by Erv Wilson.
  
  see:  https://en.wikipedia.org/wiki/Hexany
        https://en.xen.wiki/w/Hexany
  
  '''  
  def __init__(self, factors:tuple[int] = (1, 3, 5, 7), normalized:bool = False):
    if len(factors) != 4:
      raise ValueError('Hexany must have exactly 4 factors.')
    super().__init__(factors, r=2, normalized=normalized, master_set="tetrad")

class Dekany(CombinationProductSet):
  '''
  A dekany is a 10-note scale built using all the possible combinations 
  of either 2 or 3 intervals (but not a mix of both) from a given set of 
  5 intervals. It is a particular case of a combination product set (CPS).
  
  see: https://en.xen.wiki/w/Dekany
  
  '''
  def __init__(self, factors:tuple[int] = (1, 3, 5, 7, 11), r:int = 2, normalized:bool = False, master_set:str = None):
    if len(factors) != 5:
      raise ValueError('Dekany must have exactly 5 factors.')
    if not r in (2, 3):
      raise ValueError('Dekany rank must be 2 or 3.')
    super().__init__(factors, r, normalized=normalized, master_set=master_set)
    
class Pentadekany(CombinationProductSet):
  '''
  A pentadekany is a 15-note scale built using all the possible combinations
  of either 2 or 4 intervals (but not a mix of both) from a given set of 6 
  intervals. Pentadekanies may be chiral, and the choice of whether to take 
  combinations of 2 or 4 elements is equivalent to choosing the chirality. 
  It is a particular case of a combination product set (CPS).
  
  see: https://en.xen.wiki/w/Pentadekany
  
  '''
  def __init__(self, factors:tuple[int] = (1, 3, 5, 7, 11, 13), r:int = 2, normalized:bool = False, master_set:str = None):
    if len(factors) != 6:
      raise ValueError('Pentadekany must have exactly 6 factors.')
    if not r in (2, 4):
      raise ValueError('Pentadekany rank must be 2 or 4.')
    super().__init__(factors, r, normalized=normalized, master_set=master_set)

class Eikosany(CombinationProductSet):
  '''
  An eikosany is a 20-note scale built using all the possible combinations 
  of 3 intervals from a given set of 6 intervals. It is a particular case 
  of a combination product set (CPS).
  
  see:  https://en.xen.wiki/w/Eikosany
  
  '''
  def __init__(self, factors:tuple[int] = (1, 3, 5, 7, 9, 11), normalized:bool = False, master_set:str = "asterisk"):
    if len(factors) != 6:
      raise ValueError('Eikosany must have exactly 6 factors.')
    valid_master_sets = ("asterisk", "irregular_hexagon", "centered_pentagon")
    if master_set and master_set.lower() not in valid_master_sets:
      raise ValueError(f'Master set must be one of: {", ".join(valid_master_sets)}.')
    super().__init__(factors, r=3, normalized=normalized, master_set=master_set)

class Hebdomekontany(CombinationProductSet):
  '''
  A hebdomekontany is a 12-note scale built using all the possible combinations
  of 4 intervals from a given set of 8 intervals. It is a particular case 
  of a combination product set (CPS).
  
  see: https://en.xen.wiki/w/Hebdomekontany
  '''
  def __init__(self, factors:tuple[int] = (1, 3, 5, 7, 9, 11, 13, 17), normalized:bool = False):
    if len(factors) != 8:
      raise ValueError('Hebdomekontany must have exactly 8 factors.')
    super().__init__(factors, r=4, normalized=normalized, master_set='ogdoad')

class Diamond:
  '''
  Calculate the ratios of each odd number up to and including the upper limit to every other odd number 
  in the set, grouped by common denominators.

  Args:
    upper_limit: An integer representing the upper limit to generate the odd numbers.

  Returns:
    A tuple of tuples, each inner tuple containing ratios of each odd number to every other odd number, 
    grouped by common denominators.
  '''
  def __init__(self, n:Union[tuple, int]):
    self.__factors = tuple(range(1, n + 1, 2)) if isinstance(n, int) else tuple(sorted(n))
    self.__ratio_sets = self._calculate()

  def _calculate(self):
    return tuple(
      tuple(Fraction(numerator, denominator) for numerator in self.__factors)
      for denominator in self.__factors
    )
  
  @property
  def limit(self):
    return self.__factors[-1]

  @property
  def factors(self):
    return self.__factors
  
  @property
  def ratio_sets(self):
    return self.__ratio_sets
  
  @property
  def otonal(self):
    pass

  @property
  def utonal(self):
    pass

  def __repr__(self):
    return (
      f'Limit:   {self.__factors[-1]}\n'
      f'Factors: {self.__factors}\n'
    )
