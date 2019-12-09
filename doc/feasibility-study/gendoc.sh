mddia $1 | pandoc -s --pdf-engine=pdflatex -o ${1%%.*}.pdf
okular ${1%%.*}.pdf