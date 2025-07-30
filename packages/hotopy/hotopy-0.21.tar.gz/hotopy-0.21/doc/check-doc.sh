#!/bin/bash
function check_docs () {
	tmp=$(mktemp -d)
	sphinx-build -qb html $docdir/source $tmp
	code=$?
	rm -rf $tmp
	return $code
}

docdir=$(dirname $0);

check_docs && echo "docs successful" || echo "docs failed";
exit $?

