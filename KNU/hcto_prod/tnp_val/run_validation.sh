#!/bin/bash
# tnp_tamsa NanoV15/RDF validation (2026-11-25). Every heavy step runs on condor
# (condor_run); this script only orchestrates. Log: run_validation.log
V=/d0/scratch/choij/TnP/2024/validation
S=/d0/scratch/choij/hcto_prod/tnp_val
T=/d0/scratch/choij/tnp_tamsa
L=/d0/scratch/choij/SKNanoRunlog
mkdir -p $V/rntuple/muon/{data,sim} $V/rntuple/electron/{data,sim} $V/tree/muon/{data,sim} $V/tree/electron/{data,sim}
ln -sf $L/2026_11_25_003952_MuonTnPProducer/2024/Muon0_H/output/hists_0.root $V/rntuple/muon/data/Muon0_H.root
ln -sf $L/2026_11_25_003952_MuonTnPProducer/2024/DYto2Mu_4J_MLL50toInf/output/hists_0.root $V/rntuple/muon/sim/DYto2Mu_4J.root
ln -sf $L/2026_11_25_004034_ElectronTnPProducer/2024/EGamma0_H/output/hists_0.root $V/rntuple/electron/data/EGamma0_H.root
ln -sf $L/2026_11_25_004034_ElectronTnPProducer/2024/DYto2E_2J_MLL50toInf/output/hists_0.root $V/rntuple/electron/sim/DYto2E_2J.root
NV='export MAMBA_ROOT_PREFIX=/d0/scratch/choij/micromamba_envs; eval "$(/d0/scratch/choij/micromamba_bin/micromamba shell hook -s bash)"; micromamba activate /d0/scratch/choij/micromamba_envs/envs/NanoV15'
cat > $S/prep.sh <<EOS
#!/bin/bash
$NV
C=/d0/scratch/choij/TnP/scripts/rntuple_to_ttree.py
for l in muon electron; do for k in data sim; do
  for f in $V/rntuple/\$l/\$k/*.root; do python \$C --lepton \$l --force --out $V/tree/\$l/\$k/\$(basename \$f) \$f || exit 1; done
done; done
EOS
for x in A B C; do
  case $x in
    A) ENV=cmssw; BE=loop; KIND=tree ;;
    B) ENV=nanov15; BE=rdf; KIND=tree ;;
    C) ENV=nanov15; BE=rdf; KIND=rntuple ;;
  esac
  cat > $S/run_$x.sh <<EOS
#!/bin/bash
cd $T && export TNP_ENV=$ENV && source setup.sh && export TNP_HIST_BACKEND=$BE
rm -rf $V/out/$x
( time python3 $S/validate_hist.py --kind $KIND --out $V/out/$x ) 2>&1
EOS
done
cat > $S/compare.sh <<EOS
#!/bin/bash
$NV
echo "== A (CMSSW loop, TTree) vs B (NanoV15 RDF, TTree)"; python $S/compare_hists.py $V/out/A $V/out/B
echo "== B (RDF, TTree) vs C (RDF, RNTuple)"; python $S/compare_hists.py $V/out/B $V/out/C
EOS
chmod +x $S/*.sh
cd $S
echo "prep $(date)"; env -i HOME=$HOME PATH=/usr/bin:/bin condor_run -a jobbatchname=tnpval_prep ./prep.sh > prep.log 2>&1; echo "prep rc=$?"
for x in A B C; do env -i HOME=$HOME PATH=/usr/bin:/bin condor_run -a jobbatchname=tnpval_$x -a request_memory=3000 ./run_$x.sh > run_$x.log 2>&1 & done
wait; for x in A B C; do echo "$x: $(grep -c VALIDATE_DONE run_$x.log) $(grep real run_$x.log)"; done
env -i HOME=$HOME PATH=/usr/bin:/bin condor_run -a jobbatchname=tnpval_cmp ./compare.sh > compare.log 2>&1; echo "compare rc=$?"
cat compare.log
echo "VALIDATION END $(date)"
