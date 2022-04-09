#!/bin/bash
#SBATCH -A yph@cpu
#SBATCH --job-name=Serratus-Palmfold
#SBATCH --ntasks=1                     # total number of process
#SBATCH --ntasks-per-node=1            # Number of process per node
#SBATCH --hint=nomultithread           # No hyperthreading
#SBATCH --mem=10G
#SBATCH --cpus-per-task=1
#SBATCH --time=8:00:00
#SBATCH --output=/gpfsssd/scratch/rech/rep/ubu39dm/GMGCL_MSAs/delivery.palmfold.%a.out
#SBATCH --error=/gpfsssd/scratch/rech/rep/ubu39dm/GMGCL_MSAs/delivery.palmfold.%a.err
#SBATCH --array=2258,2259,2998,2999,311,312,313,314,315,316,317,318,319,697,698,699,700,701,702,703,704,705,706,707,708,709,710,711,712,738,739,740,741,742,743,744,745,746,747,748,749,750,751,752,753,754,755,756,757,758,759,760,761,762,763,764,765,766,767,768,769,770,771,772,773,774,775,776,777,778,779,780,781,782,783,784,785,786,787,788,789,790,791,792,793,794,795,796,797,798,799,800,801,802,803,804,805,806,807,808,809,810,811,812,813,814,815,816,817,818,819,820,821,822,823,824,825,826,827,828,829,830,831,832,833,834,835,836,837,838,839,840,841,842,843,844,845,846,847,848,849,850,851,852,853,854,855,856,857,858,859,860,861,862,863,864,865,866,867,868,869,870,871,872,873,878,879,880,881,882,883,884,885,886,887,888,889,890,891,892

module load python/3.8.8 cuda/11.2
export PATH=$PATH:/gpfs7kw/linkhome/rech/genpro01/ubu39dm/.local/bin/

cd /gpfsssd/scratch/rech/rep/ubu39dm/GMGCL_MSAs/

srun sh delivery.palmfold.sh
