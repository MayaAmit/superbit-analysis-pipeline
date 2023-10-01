#!/bin/sh
#SBATCH -t 23:59:59
#SBATCH -N 1
#SBATCH -n 18
#SBATCH --mem-per-cpu=10g
#SBATCH --partition=short
#SBATCH -J 
#SBATCH -v
#SBATCH --mail-type=ALL
#SBATCH --mail-user=j.mccleary@northeastern.edu
#SBATCH -o abell3827_b.out



source /work/mccleary_group/miniconda3/etc/profile.d/conda.sh
conda activate sbmcal_139

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

export TARGET='MACSJ1931'
export band='b'
export OUTDIR='/work/mccleary_group/superbit/real-data-2023/'$TARGET'/'$band'/out'
export CATDIR='/work/mccleary_group/superbit/real-data-2023/'$TARGET'/'$band'/cat'
export DATADIR='/work/mccleary_group/superbit/real-data-2023/'
export CODEDIR='/work/mccleary_group/superbit/superbit-metacal/superbit_lensing'

## medsmaker
python $CODEDIR/medsmaker/scripts/process_2023_withcoadd.py $TARGET $band $DATADIR -psf_mode=psfex -psf_seed=1134891269 --meds_coadd -star_config_dir $CODEDIR/medsmaker/configs 

## metacalibration
#python $CODEDIR/metacalibration/ngmix_fit_superbit3.py $OUTDIR/1E0657_Bullet_b_meds.fits $OUTDIR/1E0657_Bullet_b_mcal.fits -outdir=$OUTDIR -n 48 -seed=4225165605 --overwrite

## shear_profiles
#python $CODEDIR/shear_profiles/make_annular_catalog.py $DATADIR 1E0657_Bullet $OUTDIR/1E0657_Bullet_b_mcal.fits $OUTDIR/1E0657_Bullet_b_annular.fits -outdir=$OUTDIR --overwrite -cluster_redshift=0.2965 -redshift_cat=/work/mccleary_group/vassilakis.g/bit/real-data-2023/1E0657_Bullet/1E0657_Bullet_detection_cat_redshits.fits

