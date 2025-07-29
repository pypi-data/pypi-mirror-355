from pigeon_transitions import RootMachine, BaseMachine
import pytest


def test_add_client(mocker):
    pigeon = mocker.MagicMock()
    mocker.patch("pigeon_transitions.root.Pigeon", pigeon)

    class TestMachine(RootMachine):
        pass

    test_machine = TestMachine()
    test_machine.add_client(
        host="1.2.3.4", port=4321, username="user", password="passcode"
    )

    pigeon.assert_called_with(
        "pigeon-transitions", host="1.2.3.4", port=4321, create_zipkin_spans=False
    )
    pigeon().connect.assert_called_with(username="user", password="passcode")
    pigeon().subscribe_all.assert_called_with(test_machine._message_callback)


def test_message_callback(mocker):
    logger = mocker.MagicMock()

    class Child(BaseMachine):
        def __init__(self):
            self._mock_callback = mocker.MagicMock()
            super().__init__(
                states=[
                    "test",
                ],
                initial="test",
            )

        def message_callback(self, msg, topic):
            self._mock_callback(msg, topic)

    child2 = Child()
    child3 = Child()

    class Root(RootMachine):
        def __init__(self):
            self._mock_callback = mocker.MagicMock()
            super().__init__(
                states=[
                    "one",
                    {
                        "name": "two",
                        "children": child2,
                    },
                    {
                        "name": "three",
                        "children": child3,
                    },
                ],
                initial="one",
                transitions=[
                    {
                        "source": "one",
                        "dest": "two",
                        "trigger": "change",
                    },
                    {
                        "source": "two",
                        "dest": "three",
                        "trigger": "change",
                    },
                ],
                logger=logger,
            )
            self._client = mocker.MagicMock()

        def message_callback(self, msg, topic):
            self._mock_callback(msg, topic)

    root = Root()

    assert root.state == "one"

    root._message_callback("some_data", "topic1")
    root.change()

    assert root.state == "two_test"

    root._message_callback("some_other_data", "topic2")
    root.change()

    assert root.state == "three_test"

    root._message_callback("some_new_data", "topic1")

    root._mock_callback.assert_has_calls(
        [
            mocker.call("some_data", "topic1"),
            mocker.call("some_other_data", "topic2"),
            mocker.call("some_new_data", "topic1"),
        ],
    )

    child2._mock_callback.assert_called_once_with("some_other_data", "topic2")

    child3._mock_callback.assert_called_once_with("some_new_data", "topic1")

    child3._mock_callback.side_effect = Exception
    root._message_callback("other_data", "topic3")
    logger.warning.assert_called_with(
        "Callback for a message on topic 'topic3' with data 'other_data' resulted in an exception:",
        exc_info=True,
    )
    root._mock_callback.assert_called_with("other_data", "topic3")

    assert root._collected == {
        "topic1": "some_new_data",
        "topic2": "some_other_data",
        "topic3": "other_data",
    }
    assert root.get_collected("topic1") == "some_new_data"
    assert root.get_collected("topic2") == "some_other_data"
    assert root.get_collected("topic3") == "other_data"
    assert root.get_collected("topic4") is None


def test_get_current_machine(mocker):
    state_list = ["machine1", "machine2", "state"]
    test_machine = RootMachine()
    test_machine.state = test_machine.separator.join(state_list)
    test_machine._children = {
        "machine1": mocker.MagicMock(_children={"machine2": "the value"})
    }
    assert test_machine._get_current_machine() == "the value"


def test_start(mocker):

    class Child(BaseMachine):
        def __init__(self, **kwargs):
            self.on_machine_enter_mock = mocker.MagicMock()
            self.on_state_enter_mock = mocker.MagicMock()
            super().__init__(**kwargs)

    child2 = Child(
        states=[
            {
                "name": "five",
                "on_enter": "on_state_enter_mock",
            },
            "six",
        ],
        initial="five",
        on_enter="on_machine_enter_mock",
    )

    child1 = Child(
        states=[
            {
                "name": "three",
                "children": child2,
                "on_enter": "on_state_enter_mock",
            },
            "four",
        ],
        initial="three",
        on_enter="on_machine_enter_mock",
    )

    root = RootMachine(
        states=[
            {
                "name": "one",
                "children": child1,
                "on_enter": "on_state_enter_mock",
            },
            "two",
        ],
        initial="one",
    )

    root.on_state_enter_mock = mocker.MagicMock()

    root._start()

    root.on_state_enter_mock.assert_called_once()
    child1.on_machine_enter_mock.assert_called_once()
    child1.on_state_enter_mock.assert_called_once()
    child2.on_machine_enter_mock.assert_called_once()
    child2.on_state_enter_mock.assert_called_once()


@pytest.mark.xfail
def test_graph():

    class Child(BaseMachine):
        def __init__(self):
            self.check = False
            super().__init__(
                on_enter="machine_enter",
                states=[
                    "three",
                    {
                        "name": "four",
                        "on_enter": self.enter_four,
                    },
                ],
                initial="three",
                transitions=[
                    {
                        "source": "three",
                        "dest": "four",
                        "trigger": "go",
                        "conditions": "check",
                        "after": self.to_four,
                    }
                ],
            )

        def machine_enter(self):
            pass

        def enter_four(self):
            pass

        def to_four(self):
            pass

    class Root(RootMachine):
        def __init__(self):
            super().__init__(
                states=[
                    "one",
                    {
                        "name": "two",
                        "children": Child(),
                    },
                ],
                initial="one",
                transitions=[
                    {
                        "source": "one",
                        "dest": "two",
                        "trigger": "start",
                        "before": "before_sub",
                        "conditions": self.enabled,
                    },
                ],
            )

        def before_sub(self):
            pass

        def enabled(self):
            return True

    machine = Root()

    graph = machine.get_graph().source.strip().replace("\t", "    ").split("\n")

    expected = r"""digraph "State Machine" {
    graph [color=black compound=true directed=true fillcolor=white label="State Machine" nodesep=1.5 rank=source rankdir=TB "strict"=false style=solid]
    node [color=black fillcolor=white peripheries=1 shape=rectangle style="rounded, filled"]
    edge [color=black]
    one [label="one\l" color=black fillcolor=white peripheries=1 shape=rectangle style="rounded, filled"]
    subgraph cluster_two {
        graph [color=black fillcolor=white label="two\l- enter:\l  + machine_enter\l" rank=source style=solid]
        subgraph cluster_two_root {
            graph [color=None label="" rank=min]
            two [fillcolor=black shape=point width=0.1]
        }
        two_three [label="three\l" color=black fillcolor=white peripheries=1 shape=rectangle style="rounded, filled"]
        two_four [label="four\l- enter:\l  + enter_four\l" color=black fillcolor=white peripheries=1 shape=rectangle style="rounded, filled"]
    }
    one -> two [lhead=cluster_two taillabel="start [enabled]\lbefore: before_sub"]
    two -> two_three [headlabel=""]
    two_three -> two_four [label="go [check]\lafter: to_four"]
}
    """.strip().split(
        "\n"
    )

    assert len(graph) == len(expected)

    for line in expected:
        assert line in graph
        graph.remove(line)


def test_state_change_logger(mocker):
    logger = mocker.MagicMock()

    machine = RootMachine(
        states=[
            "A",
            "B",
            "C",
        ],
        initial="A",
        transitions=[
            {
                "source": "A",
                "dest": "B",
                "trigger": "next",
            },
            {
                "source": "B",
                "dest": "C",
                "trigger": "next",
            },
        ],
        logger=logger,
    )

    assert machine.state == "A"
    logger.info.assert_not_called()
    machine.next()
    assert machine.state == "B"
    logger.info.assert_called_with("Transitioned to state: B")
    machine.next()
    assert machine.state == "C"
    logger.info.assert_called_with("Transitioned to state: C")
