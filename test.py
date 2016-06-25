import generateQATest as genQA

# parseBySpacy test

# covers numeric with decimal point
def testParseBySpacy1():
	originalContext = u'Kathmandu(/\u02cck\u0251\u02d0tm\u0251\u02d0n\u02c8du\u02d0/; Nepali pronunciation: [k\u0251\u0288\u02b0m\u0251\u0273\u0256u]) is the capital and largest municipality of Nepal. It also hosts the headquarters of the South Asian Association for Regional Cooperation (SAARC). It is the only city of Nepal with the administrative status of Mahanagar (Metropolitan City), as compared to Upa-Mahanagar (Sub-Metropolitan City) or Nagar (City). Kathmandu is the core of Nepal\'s largest urban agglomeration located in the Kathmandu Valley consisting of Lalitpur, Kirtipur, Madhyapur Thimi, Bhaktapur and a number of smaller communities. Kathmandu is also known informally as "KTM" or the "tri-city". According to the 2011 census, Kathmandu Metropolitan City has a population of 975,453 and measures 49.45\xa0km2 (19.09\xa0sq\xa0mi).'
	parsedContext = u'kathmandu(/\u02cck\u0251\u02d0tm\u0251\u02d0n\u02c8du\u02d0/; nepali pronunciation: [k\u0251\u0288\u02b0m\u0251\u0273\u0256u]) is the capital and largest municipality of nepal. it also hosts the headquarters of the south asian association for regional cooperation (saarc). it is the only city of nepal with the administrative status of mahanagar (metropolitan city), as compared to upa-mahanagar (sub-metropolitan city) or nagar (city). kathmandu is the core of nepal\'s largest urban agglomeration located in the kathmandu valley consisting of lalitpur, kirtipur, madhyapur thimi, bhaktapur and a number of smaller communities. kathmandu is also known informally as "ktm" or the "tri-city". according to the 2011 census, kathmandu metropolitan city has a population of 975,453 and measures 49_45\xa0km2 (19_09\xa0sq\xa0mi).'
	assert genQA.parseBySpacy(originalContext).lower() == parsedContext

testParseBySpacy1()

# findSentence test

# covers answers with numeric and decimal point
def testFindSentence1():
	context = u'kathmandu(/\u02cck\u0251\u02d0tm\u0251\u02d0n\u02c8du\u02d0/; nepali pronunciation: [k\u0251\u0288\u02b0m\u0251\u0273\u0256u]) is the capital and largest municipality of nepal. it also hosts the headquarters of the south asian association for regional cooperation (saarc). it is the only city of nepal with the administrative status of mahanagar (metropolitan city), as compared to upa-mahanagar (sub-metropolitan city) or nagar (city). kathmandu is the core of nepal\'s largest urban agglomeration located in the kathmandu valley consisting of lalitpur, kirtipur, madhyapur thimi, bhaktapur and a number of smaller communities. kathmandu is also known informally as "ktm" or the "tri-city". according to the 2011 census, kathmandu metropolitan city has a population of 975,453 and measures 49_45\xa0km2 (19_09\xa0sq\xa0mi).'
	rightSentence = u'according to the 2011 census, kathmandu metropolitan city has a population of 975,453 and measures 49_45\xa0km2 (19_09\xa0sq\xa0mi)'
	assert genQA.findSentence(context, 725) == rightSentence

testFindSentence1()

print "All Passed"