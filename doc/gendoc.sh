mddia $1 | pandoc -s -o ${1%%.*}.docx
mddia $1 | pandoc -s --pdf-engine=pdflatex -o ${1%%.*}.pdf
okular ${1%%.*}.pdf