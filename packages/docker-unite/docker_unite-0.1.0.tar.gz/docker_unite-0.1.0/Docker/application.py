from . docker import Docker



class Application:

	@classmethod
	def Run(self, args):
		Docker.Initialize()
		application = self(args.command, args)
		application.run()

	def __init__(self, command, args):
		self.command = command
		self.args = args

	def run(self):
		function = {
			'stop': Docker.Stop,
		}

		fn = function[self.command]
		fn(self.args)
