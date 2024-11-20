#!/bin/sh
#SBATCH -t 59:59
#SBATCH -n 18
#SBATCH -N 1
#SBATCH --mem-per-cpu=5g
#SBATCH --partition=short
#SBATCH -J AbellS0592_union
#SBATCH -v
#SBATCH -o slurm_outfiles/AbellS0592_union.out


source /work/mccleary_group/miniconda3/etc/profile.d/conda.sh
conda activate sbmcal_139v2

echo $PATH
echo $PYTHONPATH
dirname="slurm_outfiles"
if [ ! -d "$dirname" ]
then
     echo " Directory $dirname does not exist. Creating now"
     mkdir -p -- "$dirname"
     echo " $dirname created"
 else
     echo " Directory $dirname exists"
 fi

echo "Proceeding with code..."

export DATADIR='/work/mccleary_group/superbit/union'
export CODEDIR='/work/mccleary_group/superbit/superbit-metacal'

## medsmaker
python $CODEDIR/superbit_lensing/medsmaker/scripts/process_2023.py AbellS0592 b,g $DATADIR -psf_mode=psfex -psf_seed=1134891269 -star_config_dir $CODEDIR/superbit_lensing/medsmaker/configs

## metacalibration
python $CODEDIR/superbit_lensing/metacalibration/ngmix_fit_superbit.py AbellS0592 b,g $DATADIR -n 48 -seed=4225165605 --overwrite -start 2000 -end 3000

## shear_profiles
python $CODEDIR/superbit_lensing/shear_profiles/make_annular_catalog.py AbellS0592 b,g $DATADIR -codedir=$CODEDIR -cluster_redshift=0.2266 -config=$CODEDIR/superbit_lensing/shear_profiles/configs/default_annular_config.yaml --overwrite
