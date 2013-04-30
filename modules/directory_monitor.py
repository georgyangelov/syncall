import logging

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from pymodules.Module import *
from decorator_utils import delay_keys


class DirectoryMonitor(Module):
    def __init__(self):
        super().__init__(self)

        self.logger = logging.getLogger(__name__)
        self.observer = Observer()

    def module_init(self):
        self.observer.start()
        self.event_manager.notify('update_monitored_dirs')

    def module_exit(self):
        self.observer.unschedule_all()
        self.observer.stop()

    @event_handler('update_monitored_dirs')
    def update_monitors(self, _):
        """
        [
            {
                'path': '/dev/python-dev/syncall',
                'recursive': True,
                'ignores': ['*/.*']
            }
        ]
        """
        monitor_dirs = self.data_manager.request('monitor_dirs', [])
        self.observer.unschedule_all()

        for dir in monitor_dirs:
            event_handler = MonitorEventHandler(
                ignores=dir.get('ignores', None),
                event_manager=self.event_manager
            )
            self.observer.schedule(
                event_handler,
                path=dir['path'],
                recursive=dir.get('recursive', False)
            )

        self.logger.debug("Monitoring dirs '{}'".format(
            ', '.join(dir['path'] for dir in monitor_dirs)
        ))


class MonitorEventHandler(PatternMatchingEventHandler):
    def __init__(self, event_manager, ignores=None):
        super().__init__(ignore_patterns=ignores)
        self.logger = logging.getLogger(__name__)
        self.event_manager = event_manager

    @delay_keys(1, lambda self, event: event.src_path)
    def on_any_event(self, event):
        data = {}
        data['src_path'] = event.src_path
        data['type'] = event.event_type

        if hasattr(event, 'dst_path'):
            data['dst_path'] = event.dst_path

        self.event_manager.notify('dir_change', data)
