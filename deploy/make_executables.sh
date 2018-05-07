#!/bin/bash
## This script is intended for Linux and Mac OS X only
bindir="../bin"
packages=(dual_md teaching_md) # panbuild)
base_tmpdir="./tmp"
package_locdir="../dualmarkdown"
option=${1:-""}

if [ "$option" == "clean" ]; then
	echo "Cleaning up"
	rm -rf ${bindir} ${base_tmpdir}
	exit 0
fi

if [ -d ${bindir} ]; then
	echo "Removing existing version of bin directory"
	rm -rf ${bindir}
fi

mkdir ${bindir}

if [ -d ${base_tmpdir} ]; then
	echo "Removing existing version of tmp directory"
	rm -rf ${base_tmpdir}
fi

mkdir ${base_tmpdir}

failed=0

## Stage 1: build executable files 
for package in ${packages[*]}
do
	logfile="../${package}.log"

	if [ ! -f "${package_locdir}/${package}.py" ]; then
		echo "Package file ${package_locdir}/${package}.py does not exist"
		exit 1
	fi

	echo -n "Building executable file for ${package} ..."
	mkdir -p ${base_tmpdir}/$package
	olddir=$PWD
	cd ${base_tmpdir}/$package
	pyinstaller --onefile ../../${package_locdir}/"${package}.py" > ${logfile} 2>&1  
	cd $olddir

	failed=$?

	if [ $failed -ne 0 ] ; then
		echo 'Failed!'
		cat ${logfile}
		exit 2
	else
		echo 'Done!'
	fi
done


## Stage 2: copy executable files into temp folder
for package in ${packages[*]}
do
	execfile="${base_tmpdir}/${package}/dist/${package}"
	
	if [ ! -f $execfile ]; then
		echo "Executable file $execfile not found. Can't copy"
		exit 3
	fi

	cp $execfile $bindir
done




