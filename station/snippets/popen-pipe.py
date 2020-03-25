from subprocess import Popen, PIPE

text = "Lorem ipsum\ndolor sit ament"

cat_process = Popen(["echo", text], stdout=PIPE)
grep_process = Popen(["grep", "ipsum"], stdin=cat_process.stdout, stdout=PIPE)
cut_process = Popen(["cut", "-d", " ", "-f", "1"], stdin=grep_process.stdout, stdout=PIPE)
out, err = cut_process.communicate()

print(out)