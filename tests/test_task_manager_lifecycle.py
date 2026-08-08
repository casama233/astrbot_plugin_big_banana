import asyncio
from types import SimpleNamespace

from core.drawing.tasks import DrawingTaskManager


def test_build_task_id_uses_message_id() -> None:
    manager = DrawingTaskManager()
    event = SimpleNamespace(
        unified_msg_origin="platform:message:session",
        message_obj=SimpleNamespace(message_id="message-1"),
    )

    assert manager.build_task_id(event) == "platform:message:session:message-1"


def test_build_task_id_falls_back_without_message_obj() -> None:
    manager = DrawingTaskManager()
    event = SimpleNamespace(unified_msg_origin="platform:message:session")

    assert manager.build_task_id(event) == (
        f"platform:message:session:event-{id(event)}"
    )


def test_cancel_all_cancels_tasks_replaced_under_the_same_id() -> None:
    async def scenario() -> None:
        manager = DrawingTaskManager()
        cancelled = [asyncio.Event(), asyncio.Event()]

        async def worker(index: int) -> None:
            try:
                await asyncio.Future()
            finally:
                cancelled[index].set()

        first = asyncio.create_task(worker(0))
        second = asyncio.create_task(worker(1))
        manager.start("same-id", first)
        manager.start("same-id", second)
        await asyncio.sleep(0)

        await manager.cancel_all()

        assert first.cancelled()
        assert second.cancelled()
        assert all(event.is_set() for event in cancelled)
        assert manager.running_tasks == {}

    asyncio.run(scenario())
