"""Charlie AI - unit, integration, white-box and black-box test suite.

Every test method is named after its test-case ID (UT-nn, IT-nn, WB-nn, BB-nn)
used in the practical file.  Uses only the standard library (unittest) and also
runs under pytest.   Run:  python tests/run_suite.py
"""
import contextlib
import datetime
import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

METRICS = {}   # filled by performance tests, read by run_suite.py


class StubModel:
    """Stands in for ModelManager."""
    def __init__(self, reply="  stub reply  "):
        self.reply = reply; self.calls = []
    def chat(self, messages, **kw):
        self.calls.append(messages); return self.reply
    def shutdown(self): pass


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(); self.tmp = Path(self._tmp.name)
        self._cwd = os.getcwd(); self._assistants = []
    def tearDown(self):
        for a in self._assistants:
            try: a.shutdown()
            except Exception: pass
        os.chdir(self._cwd); self._tmp.cleanup()

    def make_assistant(self, features=None, model="stub", real_manager=False):
        from core.assistant import OfflineAssistant
        feats = {"file_search": True, "system_info": True, "note_taking": True, "todo_list": True,
                 "reminders": True, "time_telling": True, "open_apps": True, "play_music": True, "memory": True}
        feats.update(features or {})
        cfg = {"data_dir": str(self.tmp / "data"), "model_directories": [str(self.tmp / "models")],
               "discover_existing_model_blobs": False, "features": feats}
        (self.tmp / "config.json").write_text(json.dumps(cfg))
        os.chdir(self.tmp)
        try:
            a = OfflineAssistant(config_path=str(self.tmp / "config.json"))
        except TypeError:                      # earlier version without arguments
            a = OfflineAssistant()
        self._assistants.append(a)
        if not real_manager:
            a.model_manager = StubModel() if model == "stub" else model
        return a

    def data(self): return self.tmp / "data"


# ===================================================================== UNIT
class UnitConfig(Base):
    def test_UT_01(self):
        from config.config import Config
        p = self.tmp / "c.json"; c = Config(p)
        self.assertEqual(c.config["tts_rate"], 150)
        self.assertTrue(all(c.config["features"].values())); self.assertTrue(p.exists())
    def test_UT_02(self):
        from config.config import Config
        p = self.tmp / "c.json"; p.write_text(json.dumps({"features": {"file_search": False}}))
        c = Config(p)
        self.assertFalse(c.get("features.file_search")); self.assertTrue(c.get("features.note_taking"))
        c.set("features.todo_list", False); self.assertFalse(Config(p).get("features.todo_list"))
    def test_UT_03(self):
        from config.config import Config
        p = self.tmp / "c.json"; p.write_text("{bad")
        with contextlib.redirect_stdout(__import__("io").StringIO()) as out:
            c = Config(p)
        self.assertIn("Error loading config", out.getvalue()); self.assertEqual(c.config["tts_rate"], 150)


class UnitIntent(Base):
    def d(self, t):
        from core.intent import IntentDetector
        return IntentDetector().detect(t)
    def test_UT_04(self):
        for t in ("hello", "hi", "hey"):
            r = self.d(t); self.assertEqual((r.intent, r.confidence, r.requires_llm), ("greeting", 1.0, False))
    def test_UT_05(self):
        for t, task in (("add a task to call mom", "call mom"), ("add todo for me to study", "study"), ("add task buy milk", "buy milk")):
            r = self.d(t); self.assertEqual((r.intent, r.slots["task"], r.confidence), ("add_todo", task, 0.95))
    def test_UT_06(self):
        r = self.d("add task"); self.assertEqual(r.intent, "chat"); self.assertTrue(r.requires_llm)
    def test_UT_07(self):
        exp = {"list todos": "list_todos", "show tasks": "list_todos", "list my notes": "list_notes", "system info": "system_info", "battery": "battery"}
        for t, i in exp.items():
            r = self.d(t); self.assertEqual((r.intent, r.confidence), (i, 0.98))
    def test_UT_08(self):
        for t in ("what is python", "tell me a joke"):
            r = self.d(t); self.assertEqual((r.intent, r.confidence, r.requires_llm), ("chat", 0.5, True))
    def test_UT_09(self):
        for t, a in (("open chrome", "chrome"), ("launch vs code", "vs code"), ("start calc", "calc")):
            r = self.d(t); self.assertEqual((r.intent, r.slots["app"]), ("open_application", a))
    def test_UT_10(self):
        for t in ("open notepad", "open chrome && calc"): self.assertEqual(self.d(t).intent, "chat")
    def test_UT_11(self):
        self.assertEqual(self.d("lock pc").intent, "lock_pc"); self.assertEqual(self.d("mute").intent, "mute")
        self.assertEqual(self.d("take screenshot").intent, "take_screenshot")
        r = self.d("shutdown pc"); self.assertEqual((r.intent, r.slots["action"]), ("system_power", "shutdown"))
        r = self.d("restart"); self.assertEqual((r.intent, r.slots["action"]), ("system_power", "restart"))


class UnitTodo(Base):
    def todo(self):
        from core.assistant import TodoList
        return TodoList(str(self.tmp))
    def test_UT_12(self):
        t = self.todo(); t.add_todo("Test task", "high"); i = t.todos[0]
        self.assertEqual((i["task"], i["priority"], i["completed"], i["completed_at"]), ("Test task", "high", False, None))
        self.assertIn("id", i); self.assertIn("created", i)
    def test_UT_13(self):
        t = self.todo(); t.add_todo("keep me"); t2 = self.todo()
        self.assertEqual(t2.todos[0]["task"], "keep me"); json.loads((self.tmp / "todo.json").read_text())
    def test_UT_14(self):
        t = self.todo(); t.add_todo("x"); i = t.todos[0]["id"]
        self.assertTrue(t.complete_todo(i)); self.assertTrue(t.todos[0]["completed"]); self.assertIsNotNone(t.todos[0]["completed_at"])
    def test_UT_15(self):
        t = self.todo(); t.add_todo("x"); before = json.dumps(t.todos)
        self.assertFalse(t.complete_todo(-1)); self.assertEqual(json.dumps(t.todos), before)
    def test_UT_16(self):
        t = self.todo(); t.add_todo("a"); t.add_todo("b"); t.complete_todo(t.todos[0]["id"])
        self.assertEqual((len(t.list_todos(False)), len(t.list_todos(True))), (1, 2))
    def test_UT_17(self):
        t = self.todo(); t.add_todo("a"); i = t.todos[0]["id"]
        self.assertTrue(t.remove_todo(i)); self.assertFalse(t.remove_todo(i)); self.assertEqual(t.todos, [])
    def test_UT_18(self):
        t = self.todo(); t.add_todo("Buy Milk")
        self.assertEqual([len(t.search_todos(q)) for q in ("milk", "MILK", "bread")], [1, 1, 0])
    def test_UT_33(self):
        (self.tmp / "todo.json").write_text("not json"); self.assertEqual(self.todo().todos, [])


class UnitNotes(Base):
    def notes(self):
        from core.assistant import NoteTaking
        return NoteTaking(str(self.tmp))
    def test_UT_19(self):
        n = self.notes(); p = Path(n.create_note("Lab", "Content here")); self.assertTrue(p.exists())
        lines = p.read_text().split("\n"); self.assertEqual(lines[0], "Title: Lab"); self.assertTrue(lines[1].startswith("Created:"))
        self.assertEqual(lines[2], "-" * 50); self.assertIn("Content here", lines[3])
    def test_UT_20(self):
        name = Path(self.notes().create_note("My/Note:1?", "c")).name
        self.assertIn("MyNote1", name); self.assertTrue(name.endswith(".txt"))
        for ch in '/:?': self.assertNotIn(ch, name)
    def test_UT_21(self):
        n = self.notes()
        for title in ("", "!!!"): self.assertRegex(Path(n.create_note(title, "c")).name, r"_note(_\d+)?\.txt$")
    def test_UT_22(self):
        n = self.notes()
        for i in range(12):
            p = Path(n.create_note(f"n{i}", "c")); os.utime(p, (1_700_000_000 + i, 1_700_000_000 + i))
        got = n.list_notes(limit=10); self.assertEqual(len(got), 10); self.assertEqual(got[0]["title"], "n11")
        a = n.create_note("same", "1"); b = n.create_note("same", "2"); self.assertNotEqual(a, b)
    def test_UT_23(self):
        n = self.notes(); n.create_note("A", "alpha beta"); n.create_note("G", "gamma")
        self.assertEqual([r["title"] for r in n.search_notes("ALPHA")], ["A"]); self.assertEqual(n.search_notes("delta"), [])


class UnitReminders(Base):
    def rem(self):
        from core.assistant import Reminders
        return Reminders(str(self.tmp))
    def test_UT_24(self):
        r = self.rem(); r.add_reminder("x", datetime.datetime.now() + datetime.timedelta(minutes=5))
        d = json.loads((self.tmp / "reminders.json").read_text()); self.assertEqual(len(d), 1)
        self.assertFalse(d[0]["triggered"]); datetime.datetime.fromisoformat(d[0]["remind_at"])
    def test_UT_25(self):
        r = self.rem(); now = datetime.datetime.now()
        r.add_reminder("past", now - datetime.timedelta(minutes=1)); r.add_reminder("future", now + datetime.timedelta(hours=1))
        first = r.check_reminders(); second = r.check_reminders()
        self.assertEqual([x["text"] for x in first], ["past"]); self.assertEqual(second, [])
        saved = json.loads((self.tmp / "reminders.json").read_text())
        self.assertEqual({x["text"]: x["triggered"] for x in saved}, {"past": True, "future": False})
    def test_UT_26(self):
        r = self.rem(); r.reminders = [{"id": 1, "text": "bad", "remind_at": "tomorrow", "triggered": False},
                                        {"id": 2, "text": "ok", "remind_at": (datetime.datetime.now() - datetime.timedelta(seconds=1)).isoformat(), "triggered": False}]
        got = []; r.check_interval = 0.05; r.start_checking(got.append); time.sleep(0.4)
        alive = r.thread.is_alive(); r.stop_checking()
        self.assertTrue(alive); self.assertEqual([x["text"] for x in got], ["ok"])
    def test_UT_42(self):
        (self.tmp / "reminders.json").write_text("not json"); self.assertEqual(self.rem().reminders, [])


class UnitFileSearch(Base):
    def fs(self):
        from core.assistant import FileSearch
        (self.tmp / "d").mkdir(exist_ok=True); return FileSearch(str(self.tmp / "d"))
    def test_UT_27(self):
        f = self.fs(); (f.data_dir / "Report.TXT").write_text("x"); (f.data_dir / "notes.md").write_text("y")
        r = f.search_files("report"); self.assertEqual(len(r), 1); self.assertEqual(set(r[0]), {"path", "name", "size", "modified"})
    def test_UT_28(self):
        f = self.fs()
        for i in range(15): (f.data_dir / f"a{i}.txt").write_text("x")
        for i in range(3): (f.data_dir / f"b{i}.md").write_text("x")
        self.assertEqual(len(f.search_files("", max_results=5)), 5); self.assertEqual(len(f.search_files("", file_types=[".md"])), 3)
    def test_UT_29(self):
        f = self.fs(); (self.tmp / "secret.txt").write_text("x"); self.assertEqual(f.search_files("secret"), [])
    def test_UT_30(self):
        f = self.fs(); p = f.data_dir / "t.txt"; p.write_text("foo one\nbar\nFOO two\n")
        self.assertEqual([m["line"] for m in f.search_in_file(str(p), "FOO")], [1, 3])
        self.assertEqual(f.search_in_file(str(f.data_dir / "nonexistent"), "x"), [])
        outside = self.tmp / "outside.txt"; outside.write_text("foo"); self.assertEqual(f.search_in_file(str(outside), "foo"), [])


class UnitSystem(Base):
    def test_UT_31(self):
        from core.assistant import SystemInfo
        i = SystemInfo.get_system_info()
        for k in ("system", "node", "release", "version", "machine", "processor", "memory_total", "memory_available", "cpu_count", "cpu_usage"): self.assertIn(k, i)
        self.assertTrue(i["system"])
    def test_UT_32(self):
        from core.assistant import SystemInfo
        with mock.patch("psutil.sensors_battery", return_value=None): self.assertEqual(SystemInfo.get_battery_info(), {})
        b = mock.Mock(percent=80, power_plugged=True, secsleft=100)
        with mock.patch("psutil.sensors_battery", return_value=b):
            self.assertEqual(SystemInfo.get_battery_info(), {"percent": 80, "power_plugged": True, "seconds_left": 100})


class UnitInterface(Base):
    def test_UT_34(self):
        a = self.make_assistant()
        for t in ("", "   ", None):
            self.assertEqual(a.process_command(t), a.EMPTY_REPLY); self.assertEqual(a.submit_command(t), a.EMPTY_REPLY)
        self.assertEqual(a.model_manager.calls, []); self.assertEqual(a.conversation_history, [])


class UnitModel(Base):
    def mm(self, **extra):
        from models.model import ModelManager
        d = self.tmp / "m"; d.mkdir(exist_ok=True)
        cfg = {"model_directories": [str(d)], "discover_existing_model_blobs": False}; cfg.update(extra)
        return ModelManager(_Cfg(cfg)), d
    def test_UT_35(self):
        from models.model import InferenceError
        m, _ = self.mm()
        with self.assertRaises(InferenceError) as c: m.load_model()
        self.assertIn("No GGUF model is configured for general. Available models: none", str(c.exception))
    def test_UT_36(self):
        (self.tmp / "m").mkdir(); (self.tmp / "m" / "tiny.gguf").write_bytes(b"GGUF" + b"0" * 10); (self.tmp / "m" / "big.gguf").write_bytes(b"GGUF" + b"0" * 1000)
        m, _ = self.mm(model_routing={"general": "big.gguf"}); self.assertEqual(m.resolve_model_name("general"), "big")
        m2, _ = self.mm(); self.assertEqual(m2.resolve_model_name("general"), "tiny")
    def test_UT_37(self):
        from models.model import LlamaCppEngine, ModelSettings, InferenceError
        with self.assertRaises(InferenceError) as c: LlamaCppEngine(Path("nofile.gguf"), ModelSettings())
        self.assertIn("Model file not found", str(c.exception))
    def test_UT_43(self):
        from models.model import ModelManager
        got = ModelManager.format_chat_prompt([{"role": "system", "content": "S"}, {"role": "user", "content": "U"}, {"role": "assistant", "content": ""}, {"role": "user", "content": "V"}])
        self.assertEqual(got, "<|system>\nS\n<|user>\nU\n<|user>\nV\n<|assistant>\n")
    def test_UT_44(self):
        from models.model import InferenceError
        m, _ = self.mm(); outs = iter(["no json", 'x {"a": 1} y'])
        m.generate = lambda prompt, task="general", **k: next(outs)
        self.assertEqual(m.generate_structured_json("p", schema={"a": int}, retries=1), {"a": 1})
        m.generate = lambda prompt, task="general", **k: "never json"
        with self.assertRaises(InferenceError) as c: m.generate_structured_json("p", schema={"a": int}, retries=1)
        self.assertIn("Model did not return valid JSON", str(c.exception))


class UnitTimeout(Base):
    def _engine(self, delays):
        from models.model import LlamaCppEngine, ModelSettings
        e = LlamaCppEngine.__new__(LlamaCppEngine); e.model_path = Path("fake.gguf"); e._lock = threading.RLock()
        def fake_llama(prompt, **kw):
            for i, d in enumerate(delays):
                time.sleep(d); yield {"choices": [{"text": f"w{i} "}]}
        e._llama = fake_llama; return e, ModelSettings
    def test_UT_45(self):
        from models.model import InferenceError
        e, MS = self._engine([0.05, 0.05, 0.4, 0.4])
        text = e.generate("hello", settings=MS(timeout_seconds=0.2)); self.assertTrue(text.startswith("w0")); self.assertNotIn("w3", text)
        e2, MS = self._engine([0.5])
        with self.assertRaises(InferenceError) as c: e2.generate("hello", settings=MS(timeout_seconds=0.2))
        self.assertIn("timed out", str(c.exception))


class _Cfg:
    def __init__(self, d): self.d = d
    def get(self, key, default=None):
        cur = self.d
        for k in key.split("."):
            if not isinstance(cur, dict) or k not in cur: return default
            cur = cur[k]
        return cur


class UnitMemory(Base):
    def mem(self, **k):
        from core.memory import RetrievalMemory
        return RetrievalMemory(str(self.tmp / "m.db"), **k)
    def test_UT_38(self):
        m = self.mem(); a = m.embed("hello world"); b = m.embed("hello world")
        self.assertEqual(a, b); self.assertEqual(len(a), 128); self.assertAlmostEqual(sum(x * x for x in a) ** 0.5, 1.0, places=6)
        self.assertEqual(sum(abs(x) for x in m.embed("")), 0.0)
    def test_UT_39(self):
        m = self.mem(retention_limit=3)
        for i in range(5): m.add(f"q{i} python", f"a{i}"); time.sleep(0.002)
        rows = sqlite3.connect(m.db_path).execute("select user_input from conversations order by timestamp").fetchall()
        self.assertEqual([r[0] for r in rows], ["q2 python", "q3 python", "q4 python"])
    def test_UT_40(self):
        m = self.mem(); m.add("python lists tutorial", "ok"); m.add("cooking pasta recipe", "ok")
        r = m.retrieve("python lists", limit=1); self.assertEqual(len(r), 1); self.assertIn("python", r[0]["user"])
        for item in m.retrieve("python lists", limit=10): self.assertGreater(item["score"], 0.05)


class UnitTools(Base):
    def test_UT_41(self):
        from core.tools import FunctionTool, ToolParameter
        t = FunctionTool("t", "d", [ToolParameter("p", "string", "x", required=True, enum=["low", "high"])], lambda p: p)
        self.assertEqual(t.validate_args({}), "Missing required parameter: p")
        self.assertTrue(t.validate_args({"p": "bad"}).startswith("Invalid value for p"))
        self.assertIsNone(t.validate_args({"p": "low"}))


# ============================================================== INTEGRATION
class Integration(Base):
    def test_IT_01(self):
        a = self.make_assistant(); self.assertEqual(a.process_command("add task buy milk"), "Added to-do: buy milk")
        d = json.loads((self.data() / "todo.json").read_text()); self.assertEqual((len(d), d[0]["task"], d[0]["priority"]), (1, "buy milk", "medium"))
    def test_IT_02(self):
        a = self.make_assistant(); a.model_manager = mock.Mock(); a.model_manager.chat.side_effect = AssertionError("model called")
        self.assertEqual(a.process_command("Hello"), a.GREETING_REPLY); a.model_manager.chat.assert_not_called()
    def test_IT_03(self):
        import platform
        r = self.make_assistant().process_command("system info")
        self.assertTrue(r.startswith(f"System: {platform.system()} {platform.release()} on {platform.machine()}"))
    def test_IT_04(self):
        a = self.make_assistant(); import re
        self.assertRegex(a.process_command("what time is it"), r"^The current time is \d\d:\d\d (AM|PM)$")
        self.assertRegex(a.process_command("what is the date today"), r"^Today is [A-Z][a-z]+, [A-Z][a-z]+ \d\d, \d{4}$")
    def test_IT_05(self):
        a = self.make_assistant(); a.conversation_history = [{"user": f"u{i}", "assistant": f"a{i}"} for i in range(4)]
        r = a.process_command("explain recursion"); msgs = a.model_manager.calls[0]
        self.assertEqual(r, "stub reply"); self.assertEqual(len(msgs), 8); self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual([m["content"] for m in msgs[1:7:2]], ["u1", "u2", "u3"]); self.assertEqual(msgs[-1]["content"], "explain recursion")
    def test_IT_06(self):
        a = self.make_assistant(real_manager=True)
        r = a.process_command("explain recursion"); self.assertTrue(r.startswith("I'm having trouble processing that request"))
        self.assertIn("No GGUF model is configured", r); self.assertEqual(a.process_command("list todos"), "Your to-do list is empty")
    def test_IT_07(self):
        a = self.make_assistant({"todo_list": False}); r = a.process_command("add task x")
        self.assertIn("disabled", r); self.assertFalse((self.data() / "todo.json").exists())
    def test_IT_08(self):
        a = self.make_assistant(); a.process_command("add task persist me"); a.process_command("create note remember the milk")
        a.process_command("remind me to stretch in 30 minutes"); a.shutdown()
        b = self.make_assistant()
        self.assertIn("persist me", b.process_command("list todos")); self.assertIn("remember the milk", b.process_command("list notes"))
        rem = json.loads((self.data() / "reminders.json").read_text()); self.assertEqual((rem[0]["text"], rem[0]["triggered"]), ("stretch", False))
    def test_IT_09(self):
        a = self.make_assistant(); got = []; r = a.reminders; r.stop_checking(); r.check_interval = 0.1
        r.add_reminder("due soon", datetime.datetime.now() + datetime.timedelta(seconds=0.3)); r.start_checking(got.append); time.sleep(1.0); r.stop_checking()
        self.assertEqual([x["text"] for x in got], ["due soon"])
        self.assertTrue(json.loads((self.data() / "reminders.json").read_text())[0]["triggered"])
    def test_IT_10(self):
        try: import typer, rich  # noqa
        except ImportError: self.skipTest("Blocked: typer/rich not installed in this environment")
        import subprocess
        env = dict(os.environ); env["PYTHONPATH"] = str(ROOT)
        def run(*args): return subprocess.run([sys.executable, "-m", "cli.main", *args], cwd=self.tmp, capture_output=True, text=True, env=env, timeout=60)
        r = run("version"); self.assertEqual(r.returncode, 0); self.assertIn("Charlie", r.stdout)
    def test_IT_11(self):
        a = self.make_assistant(); (self.data()).mkdir(exist_ok=True); (self.data() / "report_1.txt").write_text("x")
        self.assertEqual(a.process_command("find file report"), "Found 1 files: report_1.txt")
        self.assertEqual(a.process_command("find file zzz"), "No files found matching 'zzz'")
    def test_IT_12(self):
        try: import llama_cpp  # noqa
        except ImportError: self.skipTest("Blocked: llama-cpp-python not installed in this environment")
        model = os.environ.get("CHARLIE_TEST_MODEL")
        if not model or not Path(model).exists(): self.skipTest("Blocked: set CHARLIE_TEST_MODEL to a .gguf file")
        a = self.make_assistant(real_manager=True); t = time.perf_counter()
        r = a.process_command("Say hello in one sentence"); METRICS["llm_seconds"] = round(time.perf_counter() - t, 2); self.assertTrue(r.strip())
    def test_IT_13(self):
        a = self.make_assistant(); a.tts = None; a.speak("hello")
        self.assertEqual(a.submit_command("hello"), a.GREETING_REPLY)
        self.assertEqual(a.conversation_history, [{"user": "hello", "assistant": a.GREETING_REPLY}])
        self.assertEqual(sqlite3.connect(a.memory.db_path).execute("select count(*) from conversations").fetchone()[0], 1)
    def test_IT_14(self):
        try: import tkinter  # noqa
        except ImportError: self.skipTest("Blocked: Tkinter/display not available in this environment")
        self.skipTest("Blocked: GUI test needs a display")
    def test_IT_15(self):
        import socket
        attempts = []
        def spy(*a, **k): attempts.append(a); raise OSError("network blocked by test")
        with mock.patch.object(socket.socket, "connect", spy), mock.patch.object(socket.socket, "connect_ex", spy), mock.patch("socket.create_connection", spy), mock.patch("socket.getaddrinfo", spy):
            a = self.make_assistant()
            for c in ("hello", "add task offline check", "list todos", "system info", "what time is it", "explain recursion"): a.submit_command(c)
        self.assertEqual(attempts, [])
    def test_IT_16(self):
        a = self.make_assistant()
        with mock.patch("core.assistant.subprocess.Popen") as popen, mock.patch("core.assistant.os.startfile", create=True) as sf:
            r1 = a.process_command("open chrome"); calls1 = popen.call_count + sf.call_count
            r2 = a.process_command("open notepad && calc"); r3 = a.process_command("what is an open source licence")
            total = popen.call_count + sf.call_count
        self.assertEqual(calls1, 1); self.assertEqual(r1, "Opening chrome"); self.assertEqual(total, 1)
        self.assertIn("I can only open", r2); self.assertEqual(r3, "stub reply")
    def test_IT_17(self):
        a = self.make_assistant()
        self.assertEqual(a.process_command("play music"), "Music playback feature not implemented in this version")
        self.assertEqual(a.process_command("volume up"), a.UNSUPPORTED_REPLY)
    def test_IT_18(self):
        a = self.make_assistant()
        with mock.patch("core.assistant.subprocess.Popen") as popen, mock.patch("core.assistant.os.startfile", create=True):
            q = a.process_command("shutdown pc"); self.assertIn("Do you really want", q); self.assertEqual(popen.call_count, 0)
            self.assertEqual(a.process_command("no thanks"), "Action cancelled."); self.assertEqual(popen.call_count, 0)
            a.process_command("restart"); r = a.process_command("yes"); self.assertEqual(popen.call_count, 1); self.assertIn("restart", r)
    def test_IT_19(self):
        import statistics, psutil
        a = self.make_assistant(); times = []
        for i in range(20):
            t = time.perf_counter(); a.process_command(f"add task t{i}"); times.append(time.perf_counter() - t)
        med = statistics.median(times); METRICS["command_median_seconds"] = round(med, 4); METRICS["command_max_seconds"] = round(max(times), 4)
        METRICS["peak_rss_mb_no_model"] = round(psutil.Process().memory_info().rss / 1e6, 1)
        self.assertLessEqual(med, 1.0)
    def test_IT_20(self):
        self.skipTest("Blocked: only one platform (%s) available in this environment" % sys.platform)


# ================================================================ WHITE-BOX
class WhiteBox(Base):
    def d(self, t):
        from core.intent import IntentDetector
        return IntentDetector().detect(t)
    def test_WB_01(self): self.assertEqual(self.d("hello").intent, "greeting")
    def test_WB_02(self): self.assertEqual(self.d("volume up").intent, "volume_up")
    def test_WB_03(self): self.assertEqual(self.d("mute").intent, "mute")
    def test_WB_04(self): self.assertEqual(self.d("take screenshot").intent, "take_screenshot")
    def test_WB_05(self): self.assertEqual(self.d("lock pc").intent, "lock_pc")
    def test_WB_06(self):
        r = self.d("shutdown pc"); self.assertEqual((r.intent, r.slots), ("system_power", {"action": "shutdown"}))
    def test_WB_07(self):
        r = self.d("open chrome"); self.assertEqual((r.intent, r.slots), ("open_application", {"app": "chrome"}))
    def test_WB_08(self):
        r = self.d("open downloads"); self.assertEqual((r.intent, r.slots), ("open_folder", {"folder": "downloads"}))
    def test_WB_09(self):
        r = self.d("add a task to call mom"); self.assertEqual((r.intent, r.slots["task"]), ("add_todo", "call mom"))
    def test_WB_10(self): self.assertEqual(self.d("list my notes").intent, "list_notes")
    def test_WB_11(self): self.assertEqual(self.d("system info").intent, "system_info")
    def test_WB_12(self): self.assertEqual(self.d("battery").intent, "battery")
    def test_WB_13(self):
        r = self.d("tell me a joke"); self.assertEqual((r.intent, r.confidence, r.requires_llm), ("chat", 0.5, True))
    def test_WB_14(self): self.assertEqual(self.d("list todos").intent, "list_todos")
    def test_WB_15(self): self.assertEqual(self.d("show tasks").intent, "list_todos")
    def test_WB_16(self): self.assertEqual(self.d("hello there").intent, "chat")
    def test_WB_24(self):
        r = self.d("add task buy milk"); self.assertEqual((r.intent, r.slots["task"]), ("add_todo", "buy milk"))
    def test_WB_25(self): self.assertEqual(self.d("add task").intent, "chat")

    def _rem(self, records):
        from core.assistant import Reminders
        r = Reminders(str(self.tmp)); r.reminders = records; return r
    def _rec(self, minutes, triggered=False):
        return {"id": minutes, "text": f"r{minutes}", "remind_at": (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).isoformat(), "triggered": triggered}
    def test_WB_17(self):
        r = self._rem([]); self.assertEqual(r.check_reminders(), []); self.assertFalse((self.tmp / "reminders.json").exists())
    def test_WB_18(self): self.assertEqual(self._rem([self._rec(-5, True)]).check_reminders(), [])
    def test_WB_19(self):
        r = self._rem([self._rec(60)]); self.assertEqual(r.check_reminders(), []); self.assertFalse(r.reminders[0]["triggered"])
    def test_WB_20(self):
        r = self._rem([self._rec(-1)]); out = r.check_reminders()
        self.assertEqual(len(out), 1); self.assertTrue(out[0]["triggered"]); self.assertTrue((self.tmp / "reminders.json").exists())
    def test_WB_21(self):
        bad = {"id": 1, "text": "bad", "remind_at": "tomorrow", "triggered": False}
        r = self._rem([bad]); self.assertEqual(r.check_reminders(), []); self.assertFalse(bad["triggered"])
    def test_WB_22(self):
        a = self.make_assistant(); self.assertEqual(a.process_command("what is an update"), "stub reply"); self.assertEqual(len(a.model_manager.calls), 1)
    def test_WB_23(self):
        a = self.make_assistant()
        with mock.patch("core.assistant.subprocess.Popen") as popen, mock.patch("core.assistant.os.startfile", create=True) as sf:
            r = a.process_command("what is an open source licence"); n = popen.call_count + sf.call_count
        self.assertEqual((r, n), ("stub reply", 0))


# ================================================================ BLACK-BOX
class BlackBox(Base):
    def todo(self):
        from core.assistant import TodoList
        return TodoList(str(self.tmp))
    def test_BB_01(self):
        t = self.todo(); t.add_todo("x", "low"); self.assertEqual(t.todos[0]["priority"], "low")
    def test_BB_02(self):
        t = self.todo(); t.add_todo("y"); self.assertEqual(t.todos[0]["priority"], "medium")
    def test_BB_03(self):
        t = self.todo(); t.add_todo("z", "HIGH"); self.assertEqual(t.todos[0]["priority"], "high")
    def test_BB_04(self):
        t = self.todo()
        with self.assertRaises(ValueError) as c: t.add_todo("w", "urgent")
        self.assertIn("Invalid priority 'urgent'. Choose from: low, medium, high", str(c.exception)); self.assertEqual(t.todos, [])
    def _rem(self):
        from core.assistant import Reminders
        return Reminders(str(self.tmp))
    def test_BB_05(self):
        r = self._rem()
        with self.assertRaises(ValueError): r.schedule_in("r", minutes=-1)
        self.assertEqual(r.reminders, [])
    def test_BB_06(self):
        r = self._rem(); r.schedule_in("r", minutes=0); self.assertEqual(len(r.check_reminders()), 1)
    def test_BB_07(self):
        r = self._rem(); r.schedule_in("r", minutes=1); self.assertEqual(r.check_reminders(), [])
        due = datetime.datetime.fromisoformat(r.reminders[0]["remind_at"]); self.assertGreater((due - datetime.datetime.now()).total_seconds(), 50)
    def _hist(self, n):
        a = self.make_assistant(); a.conversation_history = [{"user": f"u{i}", "assistant": f"a{i}"} for i in range(n)]
        a.process_command("explain recursion"); return a.model_manager.calls[0]
    def test_BB_08(self): self.assertEqual(len(self._hist(2)), 6)
    def test_BB_09(self): self.assertEqual(len(self._hist(3)), 8)
    def test_BB_10(self):
        m = self._hist(4); self.assertEqual(len(m), 8); self.assertNotIn("u0", [x["content"] for x in m])
    def _fs(self, n_matches):
        from core.assistant import FileSearch
        d = self.tmp / "d"; d.mkdir(exist_ok=True)
        for i in range(n_matches): (d / f"hit{i}.txt").write_text("x")
        return FileSearch(str(d))
    def test_BB_11(self): self.assertEqual(self._fs(3).search_files("hit", max_results=0), [])
    def test_BB_12(self): self.assertEqual(len(self._fs(3).search_files("hit", max_results=1)), 1)
    def test_BB_13(self): self.assertEqual(len(self._fs(6).search_files("hit", max_results=5)), 5)
    def test_BB_14(self):
        a = self.make_assistant(); self.assertEqual(a.process_command("add task call dentist"), "Added to-do: call dentist")
    def test_BB_15(self):
        a = self.make_assistant(); self.assertEqual(a.process_command("add task"), "Please specify what task to add"); self.assertEqual(a.todo_list.todos, [])
    def test_BB_16(self):
        a = self.make_assistant({"todo_list": False}); r = a.process_command("add task x")
        self.assertIn("disabled", r); self.assertFalse((self.data() / "todo.json").exists())
    def test_BB_17(self):
        a = self.make_assistant(); a.todo_list = None; r = a.process_command("add task x"); self.assertIn("unavailable", r)
    def test_BB_18(self):
        r = self._rem(); r.add_reminder("a", datetime.datetime.now() - datetime.timedelta(seconds=1)); got = r.check_reminders()
        self.assertEqual((len(got), r.reminders[0]["triggered"]), (1, True))
    def test_BB_19(self):
        r = self._rem(); r.add_reminder("a", datetime.datetime.now() - datetime.timedelta(seconds=1)); r.check_reminders(); self.assertEqual(r.check_reminders(), [])
    def test_BB_20(self):
        t = self.todo(); t.add_todo("a"); i = t.todos[0]["id"]; t.complete_todo(i); first = t.todos[0]["completed_at"]
        self.assertTrue(t.complete_todo(i)); self.assertEqual(t.todos[0]["completed_at"], first); self.assertTrue(t.todos[0]["completed"])
    def test_BB_21(self):
        t = self.todo(); t.add_todo("a"); i = t.todos[0]["id"]; t.complete_todo(i)
        self.assertTrue(t.remove_todo(i)); self.assertFalse(t.remove_todo(i))
    def test_BB_22(self):
        from models.model import ModelManager
        d = self.tmp / "m"; d.mkdir(); (d / "bad.gguf").write_text("not a model")
        a = self.make_assistant(model=ModelManager(_Cfg({"model_directories": [str(d)], "discover_existing_model_blobs": False})))
        r1 = a.process_command("explain recursion"); r2 = a.process_command("explain recursion")
        self.assertTrue(r1.startswith("I'm having trouble")); self.assertTrue(r2.startswith("I'm having trouble")); self.assertFalse(a.model_manager.models["bad"].loaded)
    def test_BB_23(self):
        from models import model as M
        class FakeEngine:
            def __init__(s, path, settings): s.path = path
            def generate(s, prompt, **k): return "ok"
            def unload(s): pass
        d = self.tmp / "m"; d.mkdir(); (d / "x.gguf").write_bytes(b"GGUF0")
        with mock.patch.object(M, "LlamaCppEngine", FakeEngine):
            mm = M.ModelManager(_Cfg({"model_directories": [str(d)], "discover_existing_model_blobs": False}))
            mm.generate("p"); self.assertTrue(mm.models["x"].loaded); mm.unload_model("x"); self.assertFalse(mm.models["x"].loaded)
            mm.generate("p"); self.assertTrue(mm.models["x"].loaded); self.assertEqual(mm.stats["x"].load_count, 2)
    def test_BB_24(self):
        a = self.make_assistant(); self.assertEqual(a.process_command("Add Task Buy Eggs"), "Added to-do: Buy Eggs")
    def test_BB_25(self):
        a = self.make_assistant()
        for t in ("", "   "): self.assertEqual(a.submit_command(t), a.EMPTY_REPLY)
        self.assertEqual(a.model_manager.calls, [])
    def test_BB_26(self):
        a = self.make_assistant(); self.assertEqual(a.process_command("   "), a.EMPTY_REPLY); self.assertEqual(a.model_manager.calls, [])
    def test_BB_27(self):
        self.assertEqual(self.make_assistant().process_command("play music"), "Music playback feature not implemented in this version")
    def test_BB_28(self): self.assertEqual(self.make_assistant().process_command("explain recursion"), "stub reply")
    def test_BB_29(self):
        self.assertRegex(self.make_assistant().process_command("what time is it"), r"^The current time is \d\d:\d\d (AM|PM)$")
    def test_BB_30(self):
        a = self.make_assistant(); txt = "Buy 'milk'; DROP TABLE x; -- प्रोजेक्ट जमा करें"
        a.process_command("add task " + txt); self.assertEqual(self.todo_reload()[0]["task"], txt)
    def todo_reload(self):
        return json.loads((self.data() / "todo.json").read_text())
    def test_BB_31(self):
        a = self.make_assistant(); r = a.process_command("explain " + "x" * 10000); self.assertIsInstance(r, str); self.assertTrue(r)


if __name__ == "__main__":
    unittest.main()
