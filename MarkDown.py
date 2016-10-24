import re
p = re.compile(ur'#(\S{0,})', re.MULTILINE | re.IGNORECASE)
test_str = u"#Ciao come va test prova #Bene"
subst = u"<a href=\"/search/HashTag\g<1>\">\g<1></a>"

result = re.sub(p, subst, test_str)
print result
