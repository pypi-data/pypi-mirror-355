import json


class QueueMessages:
    def __init__(self, *, channel):
        self.channel = channel

    @property
    def messages(self):
        publish = self.channel.default_exchange.publish

        result = []

        for i in publish.call_args_list:
            args = i.args
            assert len(args) == 2
            assert i.kwargs == {}

            task_call = {
                "queue": args[1],
                "message": json.loads(json.loads(args[0].body)["message"]),
            }

            if (expiration := args[0].expiration) is not None:
                task_call["expiration"] = expiration

            result.append(task_call)

        return result
