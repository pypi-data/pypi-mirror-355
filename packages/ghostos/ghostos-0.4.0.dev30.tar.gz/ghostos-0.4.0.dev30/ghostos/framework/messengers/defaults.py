from typing import Optional, Iterable, List, Tuple
from ghostos.abcd.concepts import Messenger
from ghostos.core.messages import (
    Message, Payload, Role, MessageType,
    Stream, FunctionCaller, Pipe, run_pipeline,
)
from ghostos.core.messages.pipeline import SequencePipe

__all__ = [
    'DefaultMessenger'
]


class DefaultMessenger(Messenger):

    def __init__(
            self,
            upstream: Optional[Stream],
            *,
            name: Optional[str] = None,
            role: Optional[str] = None,
            payloads: Optional[Iterable[Payload]] = None,
            stage: str = "",
            output_pipes: Optional[List[Pipe]] = None,
    ):
        self._upstream = upstream
        self._assistant_name = name
        self._role = role if role else Role.ASSISTANT.value
        self._payloads = payloads
        self._sent_message_ids = []
        self._sent_messages = {}
        self._sent_callers = []
        self._stage = stage
        self._destroyed = False
        self._output_pipes = output_pipes
        self._buffering: Optional[Message] = None
        self.finish_reason = None

    def flush(self) -> Tuple[List[Message], List[FunctionCaller]]:
        messages = []
        callers = []
        done = set()
        for msg_id in self._sent_message_ids:
            if msg_id in done:
                continue
            else:
                done.add(msg_id)

            message = self._sent_messages[msg_id]
            messages.append(message)
            if message.type == MessageType.FUNCTION_CALL:
                callers.append(FunctionCaller(
                    call_id=message.call_id,
                    name=message.name,
                    arguments=message.content,
                ))
            # 非 function call 类型但也可以有 caller.
            elif message.callers:
                callers.extend(message.callers)
        # if buffering is not None, means interrupted.
        if self._buffering is not None:
            self.finish_reason = "interrupt"
            messages.append(self._buffering.as_tail(copy=False))
            callers = []

        self.destroy()
        return messages, callers

    def __del__(self):
        self.destroy()

    def destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        self._upstream = None
        self._sent_messages = {}
        self._sent_message_ids = []
        self._sent_callers = []

    def send(self, messages: Iterable[Message]) -> bool:
        messages = self.buffer(messages)
        if self._upstream is not None:
            return self._upstream.send(messages)
        list(messages)
        return True

    def buffer(self, messages: Iterable[Message]) -> Iterable[Message]:
        messages = SequencePipe().across(messages)
        if self._output_pipes:
            # set output pipes.
            messages = run_pipeline(self._output_pipes, messages)

        for item in messages:
            # update buffering.

            item = self.wrap(item)
            if item.is_complete():
                # buffer outputs
                self._sent_message_ids.append(item.msg_id)
                self._sent_messages[item.msg_id] = item
                self._buffering = None
            elif self._buffering is None:
                self._buffering = item.as_head(copy=True)
            elif patched := self._buffering.patch(item):
                self._buffering = patched

            # skip chunk
            if self._upstream and self._upstream.completes_only() and not item.is_complete():
                continue
            if item.is_complete() and item.finish_reason:
                self.finish_reason = item.finish_reason
            yield item
        # if sent all, the buffering is None.
        self._buffering = None

    def wrap(self, item: Message) -> Message:
        # add message info
        if item.is_complete() or item.is_head():
            if not item.name and MessageType.is_text(item):
                item.name = self._assistant_name
            if not item.stage:
                item.stage = self._stage
            if not item.role:
                item.role = self._role
        # create buffer in case upstream is cancel
        if item.is_complete():
            # add payload to complete one
            if self._payloads:
                for payload in self._payloads:
                    payload.set_payload_if_none(item)
        return item

    def completes_only(self) -> bool:
        return self._upstream is not None and self._upstream.completes_only()

    def alive(self) -> bool:
        return self._upstream is None or self._upstream.alive()

    def close(self):
        return

    def fail(self, error: str) -> bool:
        if self._upstream is not None:
            return self._upstream.fail(error)
        return False

    def error(self) -> Optional[Message]:
        if self._upstream is not None:
            return self._upstream.error()
        return None

    def closed(self) -> bool:
        return self._upstream is None or self._upstream.closed()
