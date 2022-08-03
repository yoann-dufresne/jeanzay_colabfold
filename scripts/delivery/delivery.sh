#script that unpacks all results_x.tar.gz in a folder and then also flattens everything in a single folder (yoann would hate this)

# this is the first of the delivery scripts. then, run the following ones:
# delivery.check.py
#    to see which were badly executed (got a3m but missing pdb)
# delivery.redo_some.sh
#    to redo those pdb's
# delivery.final_checks.py
#    to see which are missing tm's (got a3m but not tm)
# delivery.palmfold.sh
#    to re-run some of the palmfold.py's to have .tm file
# delivery.package.sh
#    to neatly package results

cd delivery

#for f in `find $PWD/../in/ -name "result_*.tar.gz" -type f`
if false
then
	for f in `cat ../delivery.toprocess.txt`
	do
	echo $(basename $f)
	tar xf $f
	done
fi


for d in `find -type d`
do
	mv $d/* .
done
