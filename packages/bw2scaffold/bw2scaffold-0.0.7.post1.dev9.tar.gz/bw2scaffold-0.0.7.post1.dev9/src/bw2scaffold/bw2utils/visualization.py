# UNder dev
# flake8: noqa
import re
from itertools import count
from pathlib import Path
from pprint import pprint

import bw2calc as bc
import bw2data as bd
import bw2io.importers
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import yaml
from pyvis.network import Network

stop_flying = ["#00B5C0", "#0E304B", "#FDD003", "#FF3967"]
more_and_more = ["#76C498", "#E1CE53", "#F06B39", "#AD1234", "#372B3B"]


def create_ei_network(key_list=None, n_layers=None, complete=False):
    """:return networkx.DiGraph(): networkx directed graph object

    Args:
      key:  (Default value = None)
      n_layers:  (Default value = None)
      complete:  (Default value = False)

    Returns:

    """

    graph = nx.DiGraph()

    if not complete:
        processed = []
        # selecting all processes
        for n in range(n_layers + 1):
            if n == 0:
                n_layer = key_list  # begins with layer 0 (ego)
            else:
                upper_layer = []
                for key in n_layer:
                    if key not in processed:
                        # upper_layer = []

                        # adds consumer process (to)
                        graph.add_node(
                            str(key),
                            activity_type=bd.get_activity(key)["activity type"],
                            location=bd.get_activity(key)["location"],
                            name=bd.get_activity(key)["name"],
                            database=key[0]
                            # rp=bd.get_activity(key)["reference product"],
                        )
                        for exchange in bd.get_activity(key).technosphere():
                            # adds supplier node (from)
                            graph.add_node(
                                str(exchange.input.key),
                                activity_type=exchange.input.get("activity type"),
                                location=exchange.input.get("location"),
                                name=exchange.input.get("name"),
                                database=exchange.input.key[0]
                                # rp=exchange.input.get("reference product"),
                            )

                            graph.add_edges_from(
                                [
                                    (
                                        str(exchange.input.key),
                                        str(exchange.output.key),
                                        {
                                            "amount": exchange["amount"],
                                            "product": exchange["name"],
                                        },
                                    )
                                ]
                            )

                            upper_layer += [exchange.input.key]
                        processed += [key]
                n_layer = list(
                    set(upper_layer)
                )  # the n+1 layer (suppliers) become consumers for next iteration

    else:
        for key in key_list:
            for activity in bd.Database(key[0]):
                # adds nodes with attributes
                graph.add_node(
                    activity["code"],
                    activity_type=activity["activity type"],
                    location=activity["location"],
                    database=activity["key"][0]
                    # rp=activity["reference product"],
                )
                # adds edges with attributes
                for exchange in activity.technosphere():
                    graph.add_edges_from(
                        [
                            (
                                str(exchange.input.key),
                                str(exchange.output.key),
                                {
                                    "amount": exchange["amount"],
                                    "product": exchange["name"],
                                },
                            )
                        ]
                    )

    return graph


def plot_ei_dyn_network(network, property, html_name="example"):
    """

    Args:
      network:
      property:

    Returns:

    """
    groups = set(nx.get_node_attributes(network, property).values())
    # maps each unique string to a number and color:
    mapping_numbers = dict(zip(sorted(groups), count()))
    mapping_colors = dict(zip(sorted(groups), stop_flying))
    # Assigns a color to an specific value
    nodes = network.nodes()
    outdegrees = network.out_degree
    net = Network(directed=True)
    net.width = "2100px"
    net.height = "1000px"

    for node, node_attrs in network.nodes(data=True):
        net.add_node(
            node,
            label=node_attrs["name"] + f" [{node_attrs['location']}]",
            size=max(outdegrees[node] * 10, 1),
            color=mapping_colors[node_attrs[property]],
        )

    for source, target, edge_attrs in network.edges(data=True):
        net.add_edge(
            source, target, title=edge_attrs["product"], arrowStrikethrough=False
        )
    net.show_buttons(
        filter_=[
            "physics",
            # "nodes",
            # "edges",
            "layout",
            # "interaction",
            # "manipulation",
            # "physics",
            # "selection",
            # "renderer",
        ]
    )
    net.show(f"{html_name}.html", notebook=False)


# %%

############################
# bd.projects.set_current("default")
# ei = bd.Database("ecoinvent36")
# bio = bd.Database("biosphere3")
# act1 = ei.get("fd1f8146d43d39613d13f409771d3b19")
# gold = ei.get("eef967d84f1d5dbef61e0eb6e8167488")
# gold1 = ei.get("2c04e4079f0ffaa934f0f949c154f97b")
# g1 = create_ei_network_2([act1.key], 1)
# plot_ei_dyn_network(g1, "activity_type")

# del bd.databases["foreground"]

# path_foreground = "experiment_base/templates/foreground_database.yaml"
# with open(path_foreground, "r") as f:
#    # dicto = yaml.safe_load(f.read())
#    string = f.read()
#    string_corrected = re.sub(
#        r"\((.*)\)", lambda x: f" !!python/tuple [{x.groups()[0]}]", string
#    )
#    dicto = yaml.load(string_corrected, Loader=yaml.Loader)

# bd.Database("foreground").write(dicto)
# method = ("IPCC 2013", "climate change", "GWP 100a")
# fg = bd.Database("foreground")
# act_test = fg.get("fishmeal_prod")
# heat = bd.get_activity(("ecoinvent36", "29e29e3f34580860d08c102328eee797"))

# g1 = create_ei_network_2([act.key for act in fg], 1)
# plot_ei_dyn_network(g1, "activity_type")
# plot_ei_dyn_network(g2, "activity_type")

# lca = bc.LCA({act1: 1}, method=method)
# lca.lci(factorize=True)
# lca.lcia()
# print(lca.score)

# lca.redo_lci({heat: 1})
# lca.lcia_calculation()
# lca.score


# charac_bio = lca.characterization_matrix.dot(lca.biosphere_matrix)
# lcam = bc.MonteCarloLCA({act_test: 1}, method=method, seed=42)
# lcam.load_data()
# lcam.lci(factorize=True)
# lcam.lcia_calculation()
# lcam.score

# lcam = bc.MonteCarloLCA({act_test: 1}, seed=42)
# _ = next(lcam)
# lcam.decompose_technosphere()
# lcam.switch_method(method)
# lcam.lcia_calculation()
# print(lcam.score)

# lcam.redo_lci({heat: 1})
# lcam.lcia_calculation()
# lcam.score


# lca = bc.LCA({act_test: 1})
# lca.load_lci_data()
# lca.build_demand_array()

# lca.technosphere_matrix = lcam.technosphere_matrix
# lca.biosphere_matrix = lcam.biosphere_matrix
# lca.decompose_technosphere()


# lca.build_demand_array({act_test: 1})
# lca.demand = {act_test: 1}
# lca.lci_calculation()
# lca.switch_method(method)
# lca.lcia_calculation()
# lca.score

# lca.build_demand_array({heat: 1})
# lca.demand = {heat: 1}
# lca.lci_calculation()
# lca.switch_method(method)
# lca.lcia_calculation()
# lca.score


# lca.switch_method(method)
# lca.lcia_calculation()
# print(lca.score)

# lca.redo_lci({heat: 1})
# lca.lcia_calculation()
# print(lca.score)


# lcam = bc.MonteCarloLCA({heat: 1}, method=method, seed=42)
# lcam = bc.MonteCarloLCA({heat: 1}, seed=42)
# lcam.redo_lci({act_test: 1})
# lcam.lcia_calculation()
# lcam.score
# for i in range(1000):
#    next(lcam)
#    datum.append(lcam.score)

##########################################################################
#####
# string = ""  # this is code to convert tuples from yaml to dicts
# re.sub(r"\(.*\)", lambda x: f"!!python/tuple {x.group()}", string)
# re.sub(r"(.*)\(.*\)", "!!python/tuple ", string)
########


# fm = bd.get_activity(("foreground", "fishmeal_prod"))
# heat = bd.get_activity(("ecoinvent36", "29e29e3f34580860d08c102328eee797"))
# vsteel = bd.get_activity(("foreground", "landed_anchovy_steel"))
# vwood = bd.get_activity(("foreground", "landed_anchovy_wooden"))
# diesel = bd.get_activity(("foreground", "diesel_peru"))


# list_keys = [
#    ("foreground", "fishmeal_prod"),
#    ("foreground", "heat_peru"),
# ]
# op = Reader.op_from_ei(
#    "ABM_SN",
#    list_keys,
#    outputs={"fishmeal, 65-67% protein"},
#    quantitiy_warehouses=1,
#    list_methods=[("IPCC 2013", "climate change", "GWP 100a")],
# )
# Writer.excel_from_op("text.xlsx", op, head_idx=True)

# op_new = Reader.op_from_excel("text.xlsx", head_idx=True)
