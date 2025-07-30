import time
from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_utils import create_daemon
from ovos_utils.log import LOG

from ovoscope import End2EndTest, get_minicroft


class TestStopNoSkills(TestCase):

    def setUp(self):
        LOG.set_level("DEBUG")
        self.minicroft = get_minicroft([])  # reuse for speed, but beware if skills keeping internal state

    def tearDown(self):
        if self.minicroft:
            self.minicroft.stop()
        LOG.set_level("CRITICAL")

    def test_exact(self):
        session = Session("123")
        session.pipeline = ['ovos-stop-pipeline-plugin-high']
        message = Message("recognizer_loop:utterance",
                          {"utterances": ["stop"], "lang": "en-US"},
                          {"session": session.serialize()})

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            source_message=message,
            expected_messages=[
                message,
                Message("stop.openvoiceos.activate", {}),  # stop pipeline counts as active_skill

                Message("stop:global", {}),  # global stop, no active skill
                Message("mycroft.stop", {}),

                # pipelines reporting if they stopped
                # no skills loaded, else skills would also report back
                Message("persona.openvoiceos.stop.response", {"skill_id": "persona.openvoiceos", "result": False}),
                Message("common_query.openvoiceos.stop.response",
                        {"skill_id": "common_query.openvoiceos", "result": False}),
                Message("ovos.common_play.stop.response", {"skill_id": "ovos.common_play", "result": False}),
                Message("ovos.common_play.stop.response", {"skill_id": "ovos.common_play", "result": False}),
                # TODO - why duplicate?

                Message("ovos.utterance.handled", {})
            ]
        )

        test.execute()

    def test_not_exact_high(self):
        session = Session("123")
        session.pipeline = ['ovos-stop-pipeline-plugin-high']
        message = Message("recognizer_loop:utterance",
                          {"utterances": ["could you stop that"], "lang": "en-US"},
                          {"session": session.serialize()})

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            source_message=message,
            expected_messages=[
                message,
                Message("mycroft.audio.play_sound", {"uri": "snd/error.mp3"}),
                Message("complete_intent_failure", {}),
                Message("ovos.utterance.handled", {}),
            ]
        )

        test.execute()

    def test_not_exact_med(self):
        session = Session("123")
        session.pipeline = ['ovos-stop-pipeline-plugin-medium']
        message = Message("recognizer_loop:utterance",
                          {"utterances": ["could you stop that"], "lang": "en-US"},
                          {"session": session.serialize()})

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            source_message=message,
            expected_messages=[
                message,
                Message("stop.openvoiceos.activate", {}),  # stop pipeline counts as active_skill

                Message("stop:global", {}),  # global stop, no active skill
                Message("mycroft.stop", {}),

                # pipelines reporting if they stopped
                # no skills loaded, else skills would also report back
                Message("persona.openvoiceos.stop.response", {"skill_id": "persona.openvoiceos", "result": False}),
                Message("common_query.openvoiceos.stop.response",
                        {"skill_id": "common_query.openvoiceos", "result": False}),
                Message("ovos.common_play.stop.response", {"skill_id": "ovos.common_play", "result": False}),
                Message("ovos.common_play.stop.response", {"skill_id": "ovos.common_play", "result": False}),
                # TODO - why duplicate?

                Message("ovos.utterance.handled", {})
            ]
        )

        test.execute()


class TestCountSkills(TestCase):

    def setUp(self):
        LOG.set_level("DEBUG")
        self.skill_id = "ovos-skill-count.openvoiceos"
        self.minicroft = get_minicroft([self.skill_id])  # reuse for speed, but beware if skills keeping internal state
        # to make tests easier to grok
        self.ignore_messages = ["speak",
                                "ovos.common_play.stop.response",
                                "common_query.openvoiceos.stop.response",
                                "persona.openvoiceos.stop.response"
                                ]

    def tearDown(self):
        if self.minicroft:
            self.minicroft.stop()
        LOG.set_level("CRITICAL")

    def test_count(self):
        session = Session("123")
        session.pipeline = ['ovos-stop-pipeline-plugin-high', "ovos-padatious-pipeline-plugin-high"]

        message = Message("recognizer_loop:utterance",
                          {"utterances": ["count to 3"], "lang": "en-US"},
                          {"session": session.serialize()})

        # first count to 10 to validate skill is working
        activate_skill = [
            message,
            Message("ovos-skill-count.openvoiceos.activate", {}),  # skill is activated
            Message("ovos-skill-count.openvoiceos:count_to_N.intent", {}),  # intent triggers

            Message("mycroft.skill.handler.start", {
                "name": "CountSkill.handle_how_are_you_intent"
            }),
            # here would be N speak messages, but we ignore them in this test
            Message("mycroft.skill.handler.complete", {
                "name": "CountSkill.handle_how_are_you_intent"
            }),

            Message("ovos.utterance.handled", {})
        ]
        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            ignore_messages=self.ignore_messages,
            source_message=message,
            expected_messages=activate_skill
        )
        test.execute()

    def test_count_infinity_active(self):
        session = Session("123")
        session.pipeline = ['ovos-stop-pipeline-plugin-high',
                            "ovos-padatious-pipeline-plugin-high"]

        def make_it_count():
            nonlocal session
            message = Message("recognizer_loop:utterance",
                              {"utterances": ["count to infinity"], "lang": "en-US"},
                              {"session": session.serialize()})
            session.activate_skill(self.skill_id)  # ensure in active skill list
            self.minicroft.bus.emit(message)

        # count to infinity, the skill will keep running in the background
        create_daemon(make_it_count)

        time.sleep(3)

        message = Message("recognizer_loop:utterance",
                          {"utterances": ["stop"], "lang": "en-US"},
                          {"session": session.serialize()})  # skill in active list now

        stop_skill_active = [
            message,
            Message("ovos-skill-count.openvoiceos.stop.ping",
                    {"skill_id":self.skill_id}),
            Message("skill.stop.pong",
                    {"skill_id": self.skill_id, "can_handle": True},
                    {"skill_id": self.skill_id}),

            Message("stop.openvoiceos.activate",
                    context={"skill_id": "stop.openvoiceos"}),
            Message(f"{self.skill_id}.stop",
                    context={"skill_id": "stop.openvoiceos"}),
            Message(f"{self.skill_id}.stop.response",
                    {"skill_id": self.skill_id, "result": True},
                    {"skill_id": self.skill_id}),

            # skill callback to stop everything
            # TODO - clean up! most arent needed/can check session if needed (ovos-workshop)
            Message("mycroft.skills.abort_question", {"skill_id": self.skill_id},
                    {"skill_id": self.skill_id}),
            Message("ovos.skills.converse.force_timeout", {"skill_id": self.skill_id},
                    {"skill_id": self.skill_id}),
            Message("mycroft.audio.speech.stop", {"skill_id": self.skill_id},
                    {"skill_id": self.skill_id}),

            # the intent running in the daemon thread exits cleanly
            Message("mycroft.skill.handler.complete",
                    {"name": "CountSkill.handle_how_are_you_intent"},
                    {"skill_id": self.skill_id}),
            Message("ovos.utterance.handled",
                    {"name": "CountSkill.handle_how_are_you_intent"},
                    {"skill_id": self.skill_id})
        ]
        test = End2EndTest(
            minicroft=self.minicroft,
            # inject_active=[self.skill_id],  # ensure this skill is in active skills list for the test
            skill_ids=[],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            ignore_messages=self.ignore_messages,
            source_message=message,
            expected_messages=stop_skill_active
        )
        test.execute()

    def test_count_infinity_global(self):
        session = Session("123")
        session.pipeline = ['ovos-stop-pipeline-plugin-high',
                            "ovos-padatious-pipeline-plugin-high"]

        def make_it_count():
            message = Message("recognizer_loop:utterance",
                              {"utterances": ["count to infinity"], "lang": "en-US"},
                              {"session": session.serialize()})
            self.minicroft.bus.emit(message)

        # count to infinity, the skill will keep running in the background
        create_daemon(make_it_count)

        time.sleep(3)

        # NOTE: skill not in active skill list for this Session, global stop will match instead
        # this doesnt typically happen at runtime, but possible since clients send whatever Session they want
        message = Message("recognizer_loop:utterance",
                          {"utterances": ["stop"], "lang": "en-US"},
                          {"session": session.serialize()})
        stop_skill_from_global = [
            message,
            Message("stop.openvoiceos.activate", {}),  # stop pipeline counts as active_skill

            Message("stop:global", {}),  # global stop, no active skill
            Message("mycroft.stop", {}),

            Message(f"{self.skill_id}.stop.response",
                    {"skill_id": self.skill_id, "result": True}),
            Message("ovos.utterance.handled", {})
        ]
        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            ignore_messages=self.ignore_messages,
            source_message=message,
            expected_messages=stop_skill_from_global
        )
        test.execute()

