import sys
import docker
import logging

from . container import Container, Containers



class Docker:

	@classmethod
	def Initialize(self):
		try:
			self.client = docker.from_env()

		except docker.errors.DockerException:
			logging.error("Docker is not running.")
			sys.exit(1)

	@classmethod
	def Containers(self):
		containers = []
		for instance in self.client.containers.list(all=True):
			containers.append(Container(instance))
		return Containers(containers)

	@classmethod
	def Stop(self, args):
		containers = self.Containers()

		if args.image is not None:
			containers.Filter(lambda c: Container.Filter_Image(c, args.image))

		containers.Print()
		containers.Execute(Container.Stop, remove=args.remove)
