import abc
import typing
import numpy as np
from typing import Tuple
if typing.TYPE_CHECKING:
    from core import Service
    from graph import Path
    from networkx import Graph


class RoutingPolicy(abc.ABC):

    def __init__(self):
        self.env = None
        self.name = None

    @abc.abstractmethod
    def route(self, service: 'Service') -> Tuple[bool, str, 'Path']:
        pass


class ClosestAvailableDC(RoutingPolicy):

    def __init__(self):
        super().__init__()
        self.name = 'CADC'

    def route(self, service: 'Service') -> Tuple[bool, str, 'Path']:
        """
        Finds the closest DC with enough available CPUs and with a path with enough available network resources
        """
        found = False
        closest_path_hops = np.finfo(0.0).max  # initializes load to the maximum value of a float
        closest_dc = None
        closest_path = None
        for iddc, dc in enumerate(self.env.topology.graph['dcs']):
            if self.env.topology.nodes[dc]['available_units'] >= service.computing_units:
                paths = self.env.topology.graph['ksp'][service.source, dc]
                for idp, path in enumerate(paths):
                    if is_path_free(self.env.topology, path, service.network_units) and closest_path_hops > path.hops:
                        closest_path_hops = path.hops
                        closest_dc = dc
                        closest_path = path
                        found = True
        return found, closest_dc, closest_path  # returns false and an index out of bounds if no path is available


class FarthestAvailableDC(RoutingPolicy):

    def __init__(self):
        super().__init__()
        self.name = 'FADC'

    def route(self, service: 'Service') -> Tuple[bool, str, 'Path']:
        """
        Finds the farthest DC with enough available CPUs and with a path with enough available network resources
        """
        found = False
        farthest_path_hops = 0.0  # initializes load to the maximum value of a float
        farthest_dc = None
        farthest_path = None
        for iddc, dc in enumerate(self.env.topology.graph['dcs']):
            if self.env.topology.nodes[dc]['available_units'] >= service.computing_units:
                paths = self.env.topology.graph['ksp'][service.source, dc]
                for idp, path in enumerate(paths):
                    if is_path_free(self.env.topology, path, service.network_units) and farthest_path_hops < path.hops:
                        farthest_path_hops = path.hops
                        farthest_dc = dc
                        farthest_path = path
                        found = True
        return found, farthest_dc, farthest_path  # returns false and an index out of bounds if no path is available


class FullLoadBalancing(RoutingPolicy):

    def __init__(self):
        super().__init__()
        self.name = 'FLB'

    def route(self, service: 'Service') -> Tuple[bool, str, 'Path']:
        """
        Finds the path+DC pair with lowest combined load
        """
        found = False
        lowest_load = np.finfo(0.0).max  # initializes load to the maximum value of a float
        closest_dc = None
        closest_path = None
        for iddc, dc in enumerate(self.env.topology.graph['dcs']):
            if self.env.topology.nodes[dc]['available_units'] >= service.computing_units:
                paths = self.env.topology.graph['ksp'][service.source, dc]
                for idp, path in enumerate(paths):
                    load = (get_max_usage(self.env.topology, path) / self.env.resource_units_per_link) * \
                           ((self.env.topology.nodes[dc]['total_units'] - self.env.topology.nodes[dc]['available_units']) /
                            self.env.topology.nodes[dc]['total_units'])
                    if is_path_free(self.env.topology, path, service.network_units) and load < lowest_load:
                        lowest_load = load
                        closest_dc = dc
                        closest_path = path
                        found = True
        return found, closest_dc, closest_path  # returns false and an index out of bounds if no path is available


def is_path_free(topology: 'Graph', path: 'Path', number_units: int) -> bool:
    for i in range(len(path.node_list) - 1):
        if topology[path.node_list[i]][path.node_list[i + 1]]['available_units'] < number_units:
            return False
    return True


def get_max_usage(topology: 'Graph', path: 'Path') -> int:
    """
    Obtains the maximum usage of resources among all the links forming the path
    """
    max_usage = np.finfo(0.0).min
    for i in range(len(path.node_list) - 1):
        max_usage = max(max_usage, topology[path.node_list[i]][path.node_list[i + 1]]['total_units'] - topology[path.node_list[i]][path.node_list[i + 1]]['available_units'])
    return max_usage
