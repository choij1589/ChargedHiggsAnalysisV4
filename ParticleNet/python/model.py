"""Parametric ParticleNet of the 2024 analysis (docs/PLAN_ParticleNet.md P2, P7, P10).

Port of the previous ParticleNetMD MultiClassParticleNet (ChargedHiggsAnalysisV3/ParticleNetMD/python/lib/
MultiClassModels.py): GraphNorm on the 9 node features; 3 dynamic EdgeConv blocks (message
MLP(cat[x_i, x_j - x_i]) of 3 x (Linear, LeakyReLU, BatchNorm, Dropout), mean aggregation, residual
shortcut Linear + BatchNorm + Dropout, edge dropout); the first block on the k = 4 nearest neighbours in
Delta R (given by the caller, python/gpu_data.py), the next two on the k = 4 nearest neighbours in feature
space; concatenation of the three block outputs, global mean pooling, the graph feature (mA / mA_scale)
appended, BatchNorm, 2 dense layers (LeakyReLU, BatchNorm, Dropout), 4 logits. Xavier initialisation.

Differences to the previous code (P10): PyG DynamicEdgeConv / knn_graph need pyg-lib (unavailable for py314
+ torch 2.14) -> torch_cluster.knn_graph + PyG EdgeConv; the k-NN and the edge dropout run under
torch.compiler.disable (no fake-tensor kernel for torch_cluster.knn, data-dependent edge count), so the
rest compiles (torch.compile(dynamic=True)). Edges are (source = neighbour, target = centre): every node
aggregates its own k nearest neighbours (the previous precomputed Delta R edges were stored transposed).
The graph feature is the mA parameter (previous: 8-bit era one-hot; one era here).
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch_cluster
from torch_geometric.nn import EdgeConv, GraphNorm, global_mean_pool
from torch_geometric.utils import dropout_edge


@torch.compiler.disable
def knn_dropout_edges(x, k: int, batch, p: float, training: bool):
    ei = torch_cluster.knn_graph(x, k=k, batch=batch, loop=False)
    if training and p > 0:
        ei, _ = dropout_edge(ei, p=p, training=True)
    return ei


@torch.compiler.disable
def dropout_given_edges(ei, p: float, training: bool):
    if training and p > 0:
        ei, _ = dropout_edge(ei, p=p, training=True)
    return ei


def _block(i, o, p):
    return [nn.Linear(i, o), nn.LeakyReLU(), nn.BatchNorm1d(o), nn.Dropout(p)]


class DynEdgeBlock(nn.Module):
    def __init__(self, cin, cout, dropout_p, edge_dropout_p, k):
        super().__init__()
        self.k, self.pe = k, edge_dropout_p
        mlp = nn.Sequential(*_block(2 * cin, cout, dropout_p), *_block(cout, cout, dropout_p),
                            *_block(cout, cout, dropout_p))
        self.conv = EdgeConv(mlp, aggr="mean")
        self.shortcut = nn.Sequential(nn.Linear(cin, cout), nn.BatchNorm1d(cout), nn.Dropout(dropout_p))

    def forward(self, x, batch, edge_index=None):
        if edge_index is None:
            edge_index = knn_dropout_edges(x, self.k, batch, self.pe, self.training)
        else:
            edge_index = dropout_given_edges(edge_index, self.pe, self.training)
        return self.conv(x, edge_index) + self.shortcut(x)


class ParticleNet(nn.Module):
    def __init__(self, num_node_features=9, num_graph_features=1, num_classes=4, num_hidden=256,
                 dropout_p=0.4, edge_dropout_p=0.4, k=4, **_):
        super().__init__()
        h = num_hidden
        self.gn0 = GraphNorm(num_node_features)
        self.conv1 = DynEdgeBlock(num_node_features, h, dropout_p, edge_dropout_p, k)
        self.conv2 = DynEdgeBlock(h, h, dropout_p, edge_dropout_p, k)
        self.conv3 = DynEdgeBlock(h, h, dropout_p, edge_dropout_p, k)
        nin = 3 * h + num_graph_features
        self.bn0 = nn.BatchNorm1d(nin)
        self.dense1, self.bn1 = nn.Linear(nin, h), nn.BatchNorm1d(h)
        self.dense2, self.bn2 = nn.Linear(h, h), nn.BatchNorm1d(h)
        self.output = nn.Linear(h, num_classes)
        self.dropout_p = dropout_p
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x, batch, edge_index0, graph_x, batch_size: int):
        x = self.gn0(x, batch, batch_size=batch_size)
        h1 = self.conv1(x, batch, edge_index0)
        h2 = self.conv2(h1, batch)
        h3 = self.conv3(h2, batch)
        g = global_mean_pool(torch.cat([h1, h2, h3], 1), batch, size=batch_size)
        g = self.bn0(torch.cat([g, graph_x], 1))
        g = F.dropout(self.bn1(F.leaky_relu(self.dense1(g))), self.dropout_p, self.training)
        g = F.dropout(self.bn2(F.leaky_relu(self.dense2(g))), self.dropout_p, self.training)
        return self.output(g)
