#!/bin/bash

wd=/home/badc/software/datasets/sentinel/ceda-di-sentinel/ceda-di/python/src
cd $wd

outdir=$wd/outputs
mkdir -p $outdir

dirs="/neodc/sentinel2a/data/L1C_MSI"


for dr in $dirs; do

    yrs=$(ls $dr | grep 20)
    ds=$(echo $dr | cut -d/ -f3)

    for yr in $yrs; do
        ydr=$dr/$yr

        mdirs=$(ls $ydr/)
    
        for mon in $mdirs; do
            path=$ydr/$mon
            job=${ds}-${yr}-${mon}

            cmd="bsub -q ingest -o $outdir/${job}.out -e $outdir/${job}.err ./scripts/wrap_es_index_files.sh $path"
            echo "Running: $cmd"
            $cmd

        done
    done
done

echo
echo "You can count the number of records with this line:"
echo "curl jasmin-es1.ceda.ac.uk:9200/sentinel/_count ; echo"

echo
echo "...and check the number of actual 'manifest' files with:"
echo "find $dirs -follow -type f -name "*.manifest" | wc -l"
