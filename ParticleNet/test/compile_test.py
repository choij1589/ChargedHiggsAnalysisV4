"""Environment check for the 2024 ParticleNet (docs/PLAN_ParticleNet.md P10, 2026-11-28): a 3-layer dynamic edge-convolution
network (k-NN in feature space with torch_cluster + PyG EdgeConv; PyG DynamicEdgeConv needs pyg-lib >= 0.6, not available
for py314 + torch 2.14), FP32 training steps on the GPU, eager vs torch.compile (k-NN excluded from tracing: no fake-tensor
kernel for torch_cluster.knn). Run: micromamba run -n NanoV15 python ParticleNet/test/compile_test.py
Result 2026-11-28 (RTX 2070 SUPER): eager 50 steps 0.41 s, compiled 0.32 s (x1.28), first compiled step 14 s, 221 MB."""
import os, time, torch, torch_cluster
from torch import nn
from torch_geometric.nn import EdgeConv, global_mean_pool, GraphNorm
from torch_geometric.data import Data, Batch
print("CC", os.environ.get("CC"), "| CPATH has cuda:", "targets/x86_64-linux/include" in os.environ.get("CPATH",""))
dev="cuda"
@torch.compiler.disable
def knn_edges(x, k, batch):
    return torch_cluster.knn_graph(x, k=k, batch=batch, loop=False)
class DynEdgeConv(nn.Module):
    def __init__(s, mlp, k): super().__init__(); s.k=k; s.conv=EdgeConv(mlp, aggr="mean")
    def forward(s, x, batch):
        return s.conv(x, knn_edges(x, s.k, batch))
def mlp(i,o): return nn.Sequential(nn.Linear(2*i,o), nn.LeakyReLU(), nn.BatchNorm1d(o), nn.Linear(o,o), nn.LeakyReLU())
class Net(nn.Module):
    def __init__(s, nf=9, nh=128, npar=1, nc=4):
        super().__init__(); s.gn=GraphNorm(nf)
        s.c1=DynEdgeConv(mlp(nf,nh),4); s.c2=DynEdgeConv(mlp(nh,nh),4); s.c3=DynEdgeConv(mlp(nh,nh),4)
        s.head=nn.Sequential(nn.Linear(3*nh+npar,nh), nn.ReLU(), nn.Linear(nh,nc))
    def forward(s,x,batch,par,bs:int):
        x=s.gn(x,batch,batch_size=bs); h1=s.c1(x,batch); h2=s.c2(h1,batch); h3=s.c3(h2,batch)
        g=global_mean_pool(torch.cat([h1,h2,h3],1),batch,size=bs); return s.head(torch.cat([g,par],1))
torch.manual_seed(1)
graphs=[Data(x=torch.randn(n,9)) for n in torch.randint(6,14,(512,)).tolist()]
b=Batch.from_data_list(graphs).to(dev); par=torch.rand(512,1,device=dev); y=torch.randint(0,4,(512,),device=dev)
net=Net().to(dev).float(); opt=torch.optim.Adam(net.parameters(),1e-3)
def step(m):
    opt.zero_grad(); loss=nn.functional.cross_entropy(m(b.x,b.batch,par,512),y); loss.backward(); opt.step(); return loss.item()
step(net); torch.cuda.synchronize()
t=time.time(); [step(net) for _ in range(50)]; torch.cuda.synchronize(); te=time.time()-t; print(f"eager FP32: 50 steps {te:.2f}s")
cm=torch.compile(net, dynamic=True)
t=time.time(); step(cm); torch.cuda.synchronize(); print(f"compile: first step {time.time()-t:.1f}s")
t=time.time(); [step(cm) for _ in range(50)]; torch.cuda.synchronize(); tc=time.time()-t; print(f"compiled FP32: 50 steps {tc:.2f}s (speed-up {te/tc:.2f}x)")
import torch._dynamo as dyn; print("graph breaks:", dict(dyn.utils.counters["graph_break"]))
print("max mem MB", round(torch.cuda.max_memory_allocated()/2**20))
