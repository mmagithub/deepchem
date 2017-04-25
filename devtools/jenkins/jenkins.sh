#!/usr/bin/env bash
envname=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1`
bash scripts/install_deepchem_conda.sh $envname
source activate $envname
python setup.py install

cd contrib/atomicconv/acnn/core
python tensor_graph_hyper_param_search.py

source deactivate
conda remove --name $envname --all
export retval=$(($retval1 + $retval2))
exit ${retval}
