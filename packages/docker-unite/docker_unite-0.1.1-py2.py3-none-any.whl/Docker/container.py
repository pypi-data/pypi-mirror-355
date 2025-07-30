import click
import logging



class Container:

	@staticmethod
	def Filter_Image(container, image):
		return image in container.tags()

	def __init__(self, instance):
		self.instance = instance

	def Stop(self, remove=False):
		container = self.instance
		container.stop(timeout=0)
		container.wait()

		if remove and not self.is_auto_removed():
			try:
				container.remove(force=True)
			except Exception as e:
				logging.error(f'Removal failed: {container.name}: {e}')

	def tags(self):
		image = self.instance.image
		return [_.removesuffix(":latest") for _ in image.tags]

	def name(self):
		return self.instance.name

	def is_auto_removed(self):
		return self.instance.attrs['HostConfig']['AutoRemove']



class Containers:

	def __init__(self, containers):
		self.storage = containers

	def Filter(self, fn):
		self.storage = list(filter(fn, self.storage))

	def Execute(self, fn, *args, **kwargs):
		for container in self.storage:
			fn(container, *args, **kwargs)

	def Print(self):
		count = len(self.storage)
		click.echo('Found' + click.style(f' {count} ', fg='green') + 'containers')
		for container in self.storage:
			click.echo(f'\t{container.name}')
