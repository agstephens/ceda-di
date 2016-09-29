#!/bin/bash

wd=/home/badc/software/datasets/sentinel/ceda-di-sentinel/ceda-di/python/src
cd $wd

outdir=$wd/outputs
mkdir -p $outdir

dirs=$@
ds=sentinel-$(date +%Y%m%d-%H%M%S)

for dr in $dirs; do

    job=${ds}

    cmd="bsub -q ingest -o $outdir/${job}.out -e $outdir/${job}.err ./scripts/wrap_es_index_files.sh $dr"
    echo "Running: $cmd"
    $cmd 

done
