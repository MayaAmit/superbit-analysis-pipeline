#!/bin/sh
#SBATCH -t 23:59:59
#SBATCH -N 1
#SBATCH --partition=short
#SBATCH -J 1E0657_Bullet_union
#SBATCH -v
#SBATCH --mail-type=ALL
#SBATCH --mail-user=j.mccleary@northeastern.edu
#SBATCH -o slurm_outfiles/1E0657_Bullet_union.out


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

export OUTDIR='/scratch/j.mccleary/union/1E0657_Bullet/b/out'
export DATADIR='/scratch/j.mccleary/union'
export CODEDIR='/work/mccleary_group/superbit/superbit-metacal/superbit_lensing'

## medsmaker
python $CODEDIR/medsmaker/scripts/process_2023.py 1E0657_Bullet b,g,u $DATADIR -psf_mode=psfex -psf_seed=1134891269 -star_config_dir $CODEDIR/medsmaker/configs -outdir $OUTDIR

## metacalibration
python $CODEDIR/metacalibration/ngmix_fit_superbit3.py $OUTDIR/1E0657_Bullet_b_meds.fits $OUTDIR/1E0657_Bullet_b_mcal.fits -outdir=$OUTDIR -n 48 -seed=4225165605 --overwrite

## shear_profiles
#python $CODEDIR/shear_profiles/make_annular_catalog.py $DATADIR 1E0657_Bullet $OUTDIR/1E0657_Bullet_b_mcal.fits $OUTDIR/1E0657_Bullet_b_annular.fits -outdir=$OUTDIR --overwrite -cluster_redshift=0.2965 -redshift_cat=/work/mccleary_group/vassilakis.g/bit/real-data-2023/1E0657_Bullet/1E0657_Bullet_detection_cat_redshits.fits
