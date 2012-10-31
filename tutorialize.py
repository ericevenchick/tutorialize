import sys
import markdown
import argparse
from jinja2 import Environment, FileSystemLoader

# front matter block starts and ends with ---
FRONT_MATTER_DELIMITER = "---"
# step blocks start and end with ///
STEP_DELIMITER = "///"

# parses a YAML style block into a dictionary
def parse_block(data):
	block_data = {}
	# remove blank lines, strip whitespace
	data = [line.strip() for line in data.split("\n") if line.strip()]

	# parse the yaml style data into the dictionary
	for line in data:
		# get the key and value
		[key, value] = line.split(":", 2)
		# store key and value, make key lowercase
		block_data[key.strip().lower()] = value.strip()
	
	return block_data	

class Tutorial:
	def __init__(self):
		self.front_matter = {}
		self.steps = []

	def parse(self, data):
		# limit to 3 splits to ensure only first block is front matter 
		section_split = data.split(FRONT_MATTER_DELIMITER, 2)
		front_matter_str = section_split[1]		
		steps_str = section_split[2]	

		self._parse_front_matter(front_matter_str)
		self._parse_steps(steps_str)

	def _parse_front_matter(self, data):
		self.front_matter = parse_block(data)

	def _parse_steps(self, data):
		# make a list of lines, restore newlines for markdown parsing
		data = [line + "\n" for line in data.split("\n")]
		in_step_def = False
		body_str = ""
		new_step = None
		step_count = 1

		for line in data:
			# start of a step definition block 
			if line.rstrip() == STEP_DELIMITER and not in_step_def:
				# if this is the end of a step, put the body text into that step
				if new_step:
					new_step.parse_body(body_str)

				# create a new step
				new_step = Step(step_count)
				self.steps.append(new_step)

				param_str = ""
				body_str = ""
				in_step_def = True
				step_count = step_count + 1
			
			# end of a step definition block
			elif line.rstrip() == STEP_DELIMITER and in_step_def:
				# parse the parameters, move on to body
				new_step.parse_params(param_str)
				in_step_def = False

			# line in a step definition block
			elif line.rstrip() != STEP_DELIMITER and in_step_def:
				param_str = param_str + line
			
			# line in a step, outside of definition block
			else:
				body_str = body_str + line
		# take care of the last step
		if new_step:
			new_step.parse_body(body_str)

	def generate(self, path, filename):
		jinja_env = Environment(loader=FileSystemLoader(path))
		template = jinja_env.get_template(filename)
		return template.render(front_matter=self.front_matter, steps=self.steps)

class Step:
	def __init__(self, number):
		self.params = {}
		self.number = number

	def parse_params(self, data):
		self.params = parse_block(data)

	def parse_body(self, data):
		self.body = data
		self.markup = markdown.markdown(self.body)

	def __str__(self):
		return str(self.params) + "\n" + str(self.markup) + "\n"

# test case
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generate a tutorial using a Markdown formatted input file and Jinja2 templates.")
	parser.add_argument("input_file", metavar="<input_file>")
	parser.add_argument("-t", metavar="<template_file>", dest="template_file")
	args = parser.parse_args()
	t = Tutorial()
	f = open(args.input_file, "r")
	t.parse(f.read())
	print t.generate('.', args.template_file)
