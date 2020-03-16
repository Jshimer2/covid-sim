#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 15 16:52:30 2020

@author: jordanshimer
"""

import random
import fastrand

import networkx as nx
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

from networkx.generators.degree_seq import expected_degree_graph

pio.renderers.default = 'browser'


n_iters = 40 # Number of days to run the simulation

prob = .04 # How contagious is it?

n_nodes = 200 # How many people in the network?

mean_inters = 8 # How many connection on average
std_dev = 4

n_sick = 5 # How many sick to start

interval = 5 # Create a network after this many days



def generate_network(n_nodes, mean_inters, std_dev, n_sick):
    
    # Create a graph with selected attributes
    n_ties = list(map(int, np.round(np.random.normal(mean_inters, std_dev, n_nodes))))
    G = expected_degree_graph(n_ties, selfloops=False)
    
    # Decide who is sick
    nx.set_node_attributes(G, 0, 'COVID-19')
    nx.set_node_attributes(G, 0, 'Time Sick')
    nx.set_node_attributes(G, 0, 'Symptomatic')
    nx.set_node_attributes(G, 0, 'Time Showing')
    
    sick_nodes = random.sample(list(G.nodes), n_sick)
    for node in sick_nodes:
        G.nodes[node]['COVID-19'] = 1
        
    return(G, sick_nodes)

def _create_new_sick_nodes(G, sick_nodes, showing, prob):
    for node in sick_nodes:        
        # Go through each contact
        for edge in G[node]:
            if edge not in sick_nodes and edge not in showing:    
                if fastrand.pcg32bounded(1000)/1000 < prob:
                    G.node[edge]['COVID-19'] = 1
                    sick_nodes.append(edge)
                   
    return(G, sick_nodes)  

def _update_sick_nodes(G, sick_nodes):
    for node in sick_nodes:
        G.nodes[node]['Time Sick'] += 1
    return(G, sick_nodes)

def _show_symptoms(G, sick_nodes, showing):
    '''
    Decide who should go from carrying to showing symptoms
    '''
    for node in sick_nodes:
        if random.normalvariate(8, 2) < G.nodes[node]['Time Sick']:
            G.nodes[node]['Symptomatic'] = 1
            G.nodes[node]['Time Showing'] = 1
            sick_nodes.remove(node)
            showing.append(node)
            
    return(G, sick_nodes, showing)
    

def run_iteration(G, sick_nodes, showing, prob):
    
    G, sick_nodes = _create_new_sick_nodes(G, sick_nodes, showing, prob)
    G, sick_nodes = _update_sick_nodes(G, sick_nodes)
    G, sick_nodes, showing = _show_symptoms(G, sick_nodes, showing)
    # TODO: Add casualities and recovery?
    
    return(G, sick_nodes, showing)


def visualize_network(G, day):
    
    # Most of this stolen from https://plot.ly/python/network-graphs/
    
    nx.set_node_attributes(G, nx.drawing.spring_layout(G, k = 1), 'pos')
    
    node_color = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        
        if G.nodes[node]['Symptomatic'] != 0:
            node_text.append('Showing')
            node_color.append('red')
            
        elif G.nodes[node]['COVID-19'] != 0:
            node_text.append('Sick, Not Showing')
            node_color.append('yellow')
        else:
            node_text.append('Not Sick')
            node_color.append('green')
    
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')        
    
    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = G.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))
            
    node_trace.marker.color = node_color
    node_trace.text = node_text
    
    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    title='Day Number {}'.format(day),
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    annotations=[ dict(
                        text='Day Number {}'.format(day),
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002 ) ],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    pio.show(fig)
    
    return(True)

if __name__ == '__main__':

    G, sick_nodes = generate_network(n_nodes, mean_inters, std_dev, n_sick)
    
    showing = []
    networks = []
    for iters in range(n_iters):
        print(iters)
        if iters % interval == 0:
            networks.append(G.copy())
        G, sick_nodes, showing = run_iteration(G, sick_nodes, showing, prob)
        
        print('I have {} sick nodes and {} showing'.format(len(sick_nodes), len(showing)))
     
    for n, G in enumerate(networks):
        day = n* interval
        visualize_network(G, day)