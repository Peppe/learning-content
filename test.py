# Linter for folder structure and properties
# Usage: python3 test.py
#

from glob import glob
import json
import ntpath
import os.path
import re
import sys

TUTORIALS_ROOT="tutorials"
MANDATORY_ARTICLE_PROPERTIES = ["title", "author", "topics"]
MANDATORY_SECTION_PROPERTIES = ["title", "author"]

with open('tutorials/allowed_tags.lst', encoding="utf-8") as allowedTagsFile:
  ALLOWED_TAGS = [line.rstrip('\n') for line in allowedTagsFile]

# global error log to be returned as CI results
errors = []

# Traverses /tutorials to validate
# - mandatory files and properties
# - valid topics and tags
#
# TODO:
# - front matter support
# - section names should start with a order prefix XX__
def main():
	print("""
	Testing tutorials...
	""")

	# check articles
	for article in glob(TUTORIALS_ROOT + "/*/"):
		check_article_or_section(article, MANDATORY_ARTICLE_PROPERTIES)
		# check article props in detail:
		articleProps = get_properties(article)
		if len(articleProps["title"]) > 75:
			log_error("Error: Title '" + articleProps["title"] + "' too long - check " + article)

		try:
			publishDateString = articleProps["publish_date"]
			if len(publishDateString) > 0:
				try:
					datetime.datetime.fromisoformat(publishDateString)
				except :
					log_error("Error: Unable to parse date '" + publishDateString + "' - check " + article)
			else:
				log_error("Error: Parse date empty - check " + article)
		except:
			pass

		# check sections
		for section in glob(article + "/*__*/"):
			check_article_or_section(section, MANDATORY_SECTION_PROPERTIES)

	if not len(errors) == 0:
		print("Validation failed:")
		print("\n".join(errors))
		sys.exit(-1)
	else:
		print("Success")

# Checks article or section properties
def check_article_or_section(folder, mandatoryProps):
	# print("Checking " + folder + "...")
	props = get_properties(folder)
	for prop in mandatoryProps:
		if not prop in props:
			log_error("Error: Missing mandatory property '" + prop + "' in " + folder)

	with open(TUTORIALS_ROOT + "/topics.json", "r", encoding="utf-8") as read_file:
		allowedTopics = [t["id"] for t in json.load(read_file)]
		try:
			topics = [x.strip() for x in props["topics"].split(',')]
			for topic in topics:
				if topic not in allowedTopics:
					log_error("Error: Invalid topic'" + topic + "' in '" + folder + "' found - Check tutorials/topics.json and extend it if needed.")
		except:
			# ignore
			pass

	# validate allowed tags
	try:
		tags = [x.strip() for x in props["tags"].split(',')]
		for tag in tags:
			if tag not in ALLOWED_TAGS:
				log_error("Error: Invalid tag '" + tag + "' in '" + folder + "' found - Check tutorials/allowed_tags.lst and extend it if needed.")
	except:
		# ignore as tags are not mandatory
		pass

# Prints and records given error
def log_error(msg):
	errors.append(msg)
	print(msg)

# Returns all article or section properties found in the given folder
def get_properties(folder):
	# check for full article
	fullProps = {}
	if os.path.isfile(folder + "/article.properties"):
		fullProps = load_properties(folder + "/article.properties")
	# check for full section
	elif os.path.isfile(folder + "/section.properties"):
		with open(folder + "/section.properties", "r", encoding="utf-8") as fp:
			fullProps = load_properties(folder + "/section.properties")
	contentAdocProps = {}
	if os.path.isfile(folder + "/content.adoc"):
		contentAdocProps =  load_asciidoc_attributes(folder + "/content.adoc")

	props = merge_dicts(fullProps, contentAdocProps)

	if not props:
		log_error("Error: Unable to load properties of '" + folder + "'")

	return props

# Returns attributes found in given AsciiDoc file
def load_asciidoc_attributes(adocFile):
	result = {}
	possibleAttributes = [ line for line in open(adocFile, "r", encoding="utf-8") if line.startswith(":")]
	for attr in possibleAttributes:
		m = re.search("^:([^:|=]*):(.*)$", attr)
		if m:
			result[m.group(1).strip()] = m.group(2).strip();
	try:
		if result["authors"]:
			result["author"] = result["authors"]
	except KeyError:
		pass

	# special handling for title property that is also the first line in the file
	with open(adocFile, "r", encoding="utf-8") as f:
		line = f.readline().rstrip()
		if line.startswith("= "):
			result["title"] = line[2:]

	return result

# Returns properties found in Java properties file
def load_properties(propsFile):
	result = {}
	possibleAttributes = [ line for line in open(propsFile, encoding="utf-8") if ":" in line or "=" in line]
	for attr in possibleAttributes:
		m = re.search("^([^:|=]*)[:|=](.*)$", attr)
		if m:
			result[m.group(1).strip()] = m.group(2).strip();

	return result

# Basename of given path
def path_leaf(path):
	head, tail = ntpath.split(path)
	return tail or ntpath.basename(head)

def merge_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

# run
if __name__ == "__main__":main()
