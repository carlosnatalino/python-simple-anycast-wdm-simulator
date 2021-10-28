import time
import typing
import datetime
import logging
if typing.TYPE_CHECKING:  # avoid circular imports
    from core import Environment
import numpy as np
import networkx as nx
import graph
# mpl.use('agg') #TODO: for use in the command-line-only (no GUI) server
from matplotlib import rcParams
# rcParams['font.family'] = 'sans-serif'
# rcParams['font.sans-serif'] = ['Times New Roman', 'Times']
# rcParams['font.size'] = 24

import matplotlib.pyplot as plt
logging.getLogger('matplotlib').setLevel(logging.WARNING)


def plot_simulation_progress(env: 'Environment'):
    """
    Plots results for a particular configuration.
    """
    plt.figure(figsize=(12, 4))

    plt.subplot(1, 3, 1)
    if any(i > 0 for i in env.tracked_results['request_blocking_ratio']):
        plt.semilogy([x * env.track_stats_every for x in range(1, len(env.tracked_results['request_blocking_ratio'])+1)],
                 env.tracked_results['request_blocking_ratio'])
    plt.xlabel('Arrival')
    plt.ylabel('Req. blocking ratio')

    plt.subplot(1, 3, 2)
    plt.plot([x * env.track_stats_every for x in range(1, len(env.tracked_results['average_link_usage'])+1)],
                 env.tracked_results['average_link_usage'])
    plt.xlabel('Arrival')
    plt.ylabel('Avg. link usage')

    plt.subplot(1, 3, 3)
    plt.plot([x * env.track_stats_every for x in range(1, len(env.tracked_results['average_node_usage']) + 1)],
             env.tracked_results['average_node_usage'])
    plt.xlabel('Arrival')
    plt.ylabel('Avg. node usage')

    plt.tight_layout()
    # plt.show()
    for format in env.plot_formats:
        plt.savefig('./results/{}/progress_{}_{}_{}.{}'.format(env.output_folder,
                                                               env.policy.name, env.load, env.id_simulation, format))
    plt.close()


def plot_final_results(env: 'Environment', results: dict, start_time: datetime.datetime, save_file=True, show=False, timedelta=None):
    """
    Consolidates the statistics and plots it periodically and at the end of all simulations.
    """
    markers = ['', 'x', 'o']

    plt.figure(figsize=(12, 4))
    plt.subplot(1, 3, 1)
    for idp, policy in enumerate(results):
        if any(results[policy][load][x]['request_blocking_ratio'] > 0 for load in results[policy] for x in range(len(results[policy][load]))):
            plt.semilogy([load for load in results[policy]],
            [np.mean([results[policy][load][x]['request_blocking_ratio'] for x in range(len(results[policy][load]))])
             for load in results[policy]], label=policy, marker=markers[idp])
    plt.xlabel('Load [Erlang]')
    plt.ylabel('Req. blocking ratio')

    plt.subplot(1, 3, 2)
    has_data = False
    for idp, policy in enumerate(results):
        if any(results[policy][load][x]['average_link_usage'] > 0 for load in results[policy] for x in range(len(results[policy][load]))):
            has_data = True
            plt.plot([load for load in results[policy]],
                [np.mean([results[policy][load][x]['average_link_usage'] for x in range(len(results[policy][load]))]) for
                load in results[policy]], label=policy, marker=markers[idp])
    plt.xlabel('Load [Erlang]')
    plt.ylabel('Avg. link usage')
    # if has_data:
    #     plt.legend(loc=2)

    plt.subplot(1, 3, 3)
    has_data = False
    for idp, policy in enumerate(results):
        if any(results[policy][load][x]['average_node_usage'] > 0 for load in results[policy] for x in
               range(len(results[policy][load]))):
            has_data = True
            plt.plot([load for load in results[policy]],
                            [np.mean([results[policy][load][x]['average_node_usage'] for x in
                                      range(len(results[policy][load]))]) for
                             load in results[policy]], label=policy, marker=markers[idp])
    plt.xlabel('Load [Erlang]')
    plt.ylabel('Avg. node usage')
    if has_data:
        plt.legend(loc=2)

    total_simulations = np.sum([1 for p in results for l in results[p]]) * env.num_seeds
    performed_simulations = np.sum([len(results[p][l]) for p in results for l in results[p]])
    percentage_completed = float(performed_simulations) / float(total_simulations) * 100.

    plt.tight_layout()

    if timedelta is None:
        timedelta = datetime.timedelta(seconds=(time.time() - start_time))

    plt.text(0.01, 0.02, 'Progress: {} out of {} ({:.3f} %) / {}'.format(performed_simulations,
                                                         total_simulations,
                                                         percentage_completed,
                                                        timedelta),
                                                        transform=plt.gcf().transFigure,
                                                        fontsize=rcParams['font.size'] - 4.)

    if save_file:
        for format in env.plot_formats:
            plt.savefig('./results/{}/final_results.{}'.format(env.output_folder, format))
    if show:
        plt.show()
    plt.close()


def plot_topology(env: 'Environment', args):

    plt.figure()
    plt.axis('off')
    pos = nx.get_node_attributes(env.topology, 'pos')

    nx.draw_networkx_edges(env.topology, pos)

    # using scatter rather than nx.draw_networkx_nodes to be able to have a legend in the topology
    nodes_x = [pos[x][0] for x in env.topology.graph['source_nodes']]
    nodes_y = [pos[x][1] for x in env.topology.graph['source_nodes']]
    plt.scatter(nodes_x, nodes_y, label='Node', color='blue', alpha=1., marker='o', linewidths=1., edgecolors='black', s=160.)

    nodes_x = [pos[x][0] for x in env.topology.graph['dcs']]
    nodes_y = [pos[x][1] for x in env.topology.graph['dcs']]
    plt.scatter(nodes_x, nodes_y, label='DC', color='red', alpha=1., marker='s', linewidths=1., edgecolors='black', s=200.)

    plt.legend(loc=1)
    for format in env.plot_formats:
        plt.savefig(f'./results/{env.output_folder}/topology_{env.topology_name}.{format}')
    plt.close() # avoids too many figures opened at once