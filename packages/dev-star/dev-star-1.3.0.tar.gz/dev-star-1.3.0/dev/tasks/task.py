import inspect
from abc import ABC
from argparse import ArgumentParser, Namespace, _SubParsersAction
from typing import Any, Optional

from dev.constants import ReturnCode
from dev.exceptions import TaskArgumentError
from dev.tasks.custom import CustomTask


class Task(ABC):
    def _perform(self, *_: Any, **kwargs: Any) -> int:
        raise NotImplementedError()

    @classmethod
    def _add_task_parser(cls, subparsers: _SubParsersAction) -> ArgumentParser:
        return subparsers.add_parser(cls.task_name())

    @classmethod
    def add_to_subparser(cls, subparsers: _SubParsersAction) -> None:
        cls._add_task_parser(subparsers)

    @classmethod
    def customize(cls, custom_task: CustomTask) -> None:
        cls._custom_task = custom_task

    @classmethod
    def execute(
        cls,
        args: Optional[Namespace] = None,
        allow_extraneous_args: bool = False,
        **kwargs: Any,
    ) -> int:
        task = cls()
        arguments = kwargs.copy()
        function_arguments = inspect.getfullargspec(task._perform).args

        if args is not None:
            arguments.update(vars(args))

        extra_args = set(arguments.keys()) - set(function_arguments)
        if not allow_extraneous_args and len(extra_args) > 0:
            raise TaskArgumentError(
                f"task.execute received extraneous arguments: [{', '.join(extra_args)}]"
            )

        if hasattr(cls, "_custom_task"):
            rc = cls._custom_task.perform_pre_step()
            if rc != ReturnCode.OK:
                return rc

        try:
            rc = task._perform(
                **{
                    key: value
                    for key, value in arguments.items()
                    if key in function_arguments
                }
            )
            if rc != ReturnCode.OK:
                return rc
        except TypeError as error:
            raise TaskArgumentError(str(error))
        except KeyboardInterrupt:
            return ReturnCode.INTERRUPTED

        if hasattr(cls, "_custom_task"):
            rc = cls._custom_task.perform_post_step()

        return rc

    @classmethod
    def task_name(cls) -> str:
        return cls.__name__.lower().replace("task", "")
