#!/bin/sh
#SBATCH -t 23:59:59
#SBATCH -N 1
#SBATCH -n 18
#SBATCH --mem-per-cpu=10g
#SBATCH --partition=short
#SBATCH -J Abell3411_union
#SBATCH -v
#SBATCH --mail-type=ALL
#SBATCH --mail-user=j.mccleary@northeastern.edu
#SBATCH -o slurm_outfiles/Abell3411_union_round2.out



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

export OUTDIR='/scratch/j.mccleary/Abell3411/'
export DATADIR='/work/mccleary_group/superbit/union'
export CODEDIR='/work/mccleary_group/superbit/superbit-metacal/superbit_lensing'

## medsmaker
#python $CODEDIR/medsmaker/scripts/process_2023.py -outdir $OUTDIR Abell3411 b $DATADIR -psf_mode=psfex -psf_seed=1134891269 -star_config_dir $CODEDIR/medsmaker/configs --meds_coadd

## metacalibration
python $CODEDIR/metacalibration/ngmix_fit_superbit3.py $OUTDIR/Abell3411_b_meds.fits $OUTDIR/Abell3411_b_mcal.fits -outdir=$OUTDIR -n 48 -seed=4125165605 --overwrite 

## shear_profiles
python $CODEDIR/shear_profiles/make_annular_catalog.py $DATADIR Abell3411 $OUTDIR/Abell3411_b_mcal.fits $OUTDIR/Abell3411_b_annular.fits -outdir=$OUTDIR --overwrite -cluster_redshift=0.17 -redshift_cat=$DATADIR/catalogs/redshifts/Abell3411_NED_redshifts.csv
