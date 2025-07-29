# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root
# for license information.

import codecs
import inspect
import os
import pydevd
import socket
import sys
import threading
import traceback # Ensure traceback is imported for the custom logic block
# for changing variable 기능
import json as std_json
import importlib.util
from ast import literal_eval

# This class and functions are used to parse the capture_data json file
from dataclasses import dataclass, field
from typing import List, Optional, Any

import debugpy
from debugpy import adapter
from debugpy.common import json, log, sockets
from _pydevd_bundle.pydevd_constants import get_global_debugger
from _pydevd_bundle.pydevd_net_command import NetCommand # Ensure this import is present
from pydevd_file_utils import absolute_path
from debugpy.common.util import hide_debugpy_internals
from _pydevd_bundle.pydevd_vars import change_attr_expression
from _pydevd_bundle.pydevd_process_net_command_json import PyDevJsonCommandProcessor
from _pydevd_bundle._debug_adapter import pydevd_schema
from _pydevd_bundle.pydevd_constants import get_thread_id

_tls = threading.local()

# TODO: "gevent", if possible.
_config = {
    "qt": "none",
    "subProcess": True,
    "python": sys.executable,
    "pythonEnv": {},
}

_config_valid_values = {
    # If property is not listed here, any value is considered valid, so long as
    # its type matches that of the default value in _config.
    "qt": ["auto", "none", "pyside", "pyside2", "pyqt4", "pyqt5"],
}

# This must be a global to prevent it from being garbage collected and triggering
# https://bugs.python.org/issue37380.
_adapter_process = None


def _settrace(*args, **kwargs):
    log.debug("pydevd.settrace(*{0!r}, **{1!r})", args, kwargs)
    # The stdin in notification is not acted upon in debugpy, so, disable it.
    kwargs.setdefault("notify_stdin", False)
    try:
        pydevd.settrace(*args, **kwargs)
    except Exception:
        raise


def ensure_logging():
    """Starts logging to log.log_dir, if it hasn't already been done."""
    if ensure_logging.ensured:
        return
    ensure_logging.ensured = True
    log.to_file(prefix="debugpy.server")
    log.describe_environment("Initial environment:")
    if log.log_dir is not None:
        pydevd.log_to(log.log_dir + "/debugpy.pydevd.log")


ensure_logging.ensured = False


def log_to(path):
    if ensure_logging.ensured:
        raise RuntimeError("logging has already begun")

    log.debug("log_to{0!r}", (path,))
    if path is sys.stderr:
        log.stderr.levels |= set(log.LEVELS)
    else:
        log.log_dir = path


def configure(properties=None, **kwargs):
    ensure_logging()
    log.debug("configure{0!r}", (properties, kwargs))

    if properties is None:
        properties = kwargs
    else:
        properties = dict(properties)
        properties.update(kwargs)

    for k, v in properties.items():
        if k not in _config:
            raise ValueError("Unknown property {0!r}".format(k))
        expected_type = type(_config[k])
        if type(v) is not expected_type:
            raise ValueError("{0!r} must be a {1}".format(k, expected_type.__name__))
        valid_values = _config_valid_values.get(k)
        if (valid_values is not None) and (v not in valid_values):
            raise ValueError("{0!r} must be one of: {1!r}".format(k, valid_values))
        _config[k] = v


def _starts_debugging(func):
    def debug(address, **kwargs):
        try:
            _, port = address
        except Exception:
            port = address
            address = ("127.0.0.1", port)
        try:
            port.__index__()  # ensure it's int-like
        except Exception:
            raise ValueError("expected port or (host, port)")
        if not (0 <= port < 2**16):
            raise ValueError("invalid port number")

        ensure_logging()
        log.debug("{0}({1!r}, **{2!r})", func.__name__, address, kwargs)
        log.info("Initial debug configuration: {0}", json.repr(_config))

        qt_mode = _config.get("qt", "none")
        if qt_mode != "none":
            pydevd.enable_qt_support(qt_mode)

        settrace_kwargs = {
            "suspend": False,
            "patch_multiprocessing": _config.get("subProcess", True),
        }

        if hide_debugpy_internals():
            debugpy_path = os.path.dirname(absolute_path(debugpy.__file__))
            settrace_kwargs["dont_trace_start_patterns"] = (debugpy_path,)
            settrace_kwargs["dont_trace_end_patterns"] = (str("debugpy_launcher.py"),)

        try:
            return func(address, settrace_kwargs, **kwargs)
        except Exception:
            log.reraise_exception("{0}() failed:", func.__name__, level="info")

    return debug


@_starts_debugging
def listen(address, settrace_kwargs, in_process_debug_adapter=False):
    # Errors below are logged with level="info", because the caller might be catching
    # and handling exceptions, and we don't want to spam their stderr unnecessarily.

    if listen.called:
        # Multiple calls to listen() cause the debuggee to hang
        raise RuntimeError("debugpy.listen() has already been called on this process")

    if in_process_debug_adapter:
        host, port = address
        log.info("Listening: pydevd without debugpy adapter: {0}:{1}", host, port)
        settrace_kwargs["patch_multiprocessing"] = False
        _settrace(
            host=host,
            port=port,
            wait_for_ready_to_run=False,
            block_until_connected=False,
            **settrace_kwargs
        )
        return

    import subprocess

    server_access_token = codecs.encode(os.urandom(32), "hex").decode("ascii")

    try:
        endpoints_listener = sockets.create_server("127.0.0.1", 0, timeout=30)
    except Exception as exc:
        log.swallow_exception("Can't listen for adapter endpoints:")
        raise RuntimeError("can't listen for adapter endpoints: " + str(exc))

    try:
        endpoints_host, endpoints_port = endpoints_listener.getsockname()
        log.info(
            "Waiting for adapter endpoints on {0}:{1}...",
            endpoints_host,
            endpoints_port,
        )

        host, port = address
        adapter_args = [
            _config.get("python", sys.executable),
            os.path.dirname(adapter.__file__),
            "--for-server",
            str(endpoints_port),
            "--host",
            host,
            "--port",
            str(port),
            "--server-access-token",
            server_access_token,
        ]
        if log.log_dir is not None:
            adapter_args += ["--log-dir", log.log_dir]
        log.info("debugpy.listen() spawning adapter: {0}", json.repr(adapter_args))

        # On Windows, detach the adapter from our console, if any, so that it doesn't
        # receive Ctrl+C from it, and doesn't keep it open once we exit.
        creationflags = 0
        if sys.platform == "win32":
            creationflags |= 0x08000000  # CREATE_NO_WINDOW
            creationflags |= 0x00000200  # CREATE_NEW_PROCESS_GROUP

        # On embedded applications, environment variables might not contain
        # Python environment settings.
        python_env = _config.get("pythonEnv")
        if not bool(python_env):
            python_env = None

        # Adapter will outlive this process, so we shouldn't wait for it. However, we
        # need to ensure that the Popen instance for it doesn't get garbage-collected
        # by holding a reference to it in a non-local variable, to avoid triggering
        # https://bugs.python.org/issue37380.
        try:
            global _adapter_process
            _adapter_process = subprocess.Popen(
                adapter_args,
                close_fds=True,
                creationflags=creationflags,
                env=python_env,
            )
            if os.name == "posix":
                # It's going to fork again to daemonize, so we need to wait on it to
                # clean it up properly.
                _adapter_process.wait()
            else:
                # Suppress misleading warning about child process still being alive when
                # this process exits (https://bugs.python.org/issue38890).
                _adapter_process.returncode = 0
                pydevd.add_dont_terminate_child_pid(_adapter_process.pid)
        except Exception as exc:
            log.swallow_exception("Error spawning debug adapter:", level="info")
            raise RuntimeError("error spawning debug adapter: " + str(exc))

        try:
            sock, _ = endpoints_listener.accept()
            try:
                sock.settimeout(None)
                sock_io = sock.makefile("rb", 0)
                try:
                    endpoints = json.loads(sock_io.read().decode("utf-8"))
                finally:
                    sock_io.close()
            finally:
                sockets.close_socket(sock)
        except socket.timeout:
            log.swallow_exception(
                "Timed out waiting for adapter to connect:", level="info"
            )
            raise RuntimeError("timed out waiting for adapter to connect")
        except Exception as exc:
            log.swallow_exception("Error retrieving adapter endpoints:", level="info")
            raise RuntimeError("error retrieving adapter endpoints: " + str(exc))

    finally:
        endpoints_listener.close()

    log.info("Endpoints received from adapter: {0}", json.repr(endpoints))

    if "error" in endpoints:
        raise RuntimeError(str(endpoints["error"]))

    try:
        server_host = str(endpoints["server"]["host"])
        server_port = int(endpoints["server"]["port"])
        client_host = str(endpoints["client"]["host"])
        client_port = int(endpoints["client"]["port"])
    except Exception as exc:
        log.swallow_exception(
            "Error parsing adapter endpoints:\n{0}\n",
            json.repr(endpoints),
            level="info",
        )
        raise RuntimeError("error parsing adapter endpoints: " + str(exc))
    log.info(
        "Adapter is accepting incoming client connections on {0}:{1}",
        client_host,
        client_port,
    )

    _settrace(
        host=server_host,
        port=server_port,
        wait_for_ready_to_run=False,
        block_until_connected=True,
        access_token=server_access_token,
        **settrace_kwargs
    )
    log.info("pydevd is connected to adapter at {0}:{1}", server_host, server_port)
    listen.called = True
    return client_host, client_port

listen.called = False


@_starts_debugging
def connect(address, settrace_kwargs, access_token=None):
    host, port = address
    _settrace(host=host, port=port, client_access_token=access_token, **settrace_kwargs)



# jump_to function for buggerking
def jump_to(pydb, file_path, target_line):
    
    """
    Jump to a specific line in a file using the debugger.
    
    :param pydb: The debugger instance.
    :param file_path: The path to the file.
    :param target_line: The line number to jump to.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Ensure the debugger is set up correctly
    if pydb is None:
        raise RuntimeError("Debugger instance is not available. Ensure settrace() was called.")
    
    
    print("Custom logic: Starting jump to cursor test.")
    try:
        # JSON 명령 처리용 프로세서
        json_processor = PyDevJsonCommandProcessor(
            from_json=lambda data, cls=None: cls(**data) if cls else data
        )
        print("Custom logic: Using a new instance of PyDevJsonCommandProcessor for test.")
        
        # GotoTargets 요청 시퀀스 증가
        NetCommand.next_seq += 2
        seq_gototargets = NetCommand.next_seq

        # GotoTargetsArguments 생성
        gototargets_args = pydevd_schema.GotoTargetsArguments(
            source=pydevd_schema.Source(
                path=file_path,
                name=os.path.basename(file_path)
            ),
            line=target_line
        )
        gototargets_request = pydevd_schema.GotoTargetsRequest(
            arguments=gototargets_args,
            seq=seq_gototargets,
            type='request',
            command='gotoTargets'
        )
        print(f"Custom logic: Calling on_gototargets_request (seq: {seq_gototargets}) "
              f"for {file_path} line {target_line}")
        
        # 실제 요청 실행
        net_command_gototargets = json_processor.on_gototargets_request(pydb, gototargets_request)

        # 응답 확인
        if not (net_command_gototargets and hasattr(net_command_gototargets, 'as_dict')):
            print(f"Custom logic: No valid response object from on_gototargets_request. "
                  f"Command object: {net_command_gototargets}")
            return

        response_payload = net_command_gototargets.as_dict
        success = response_payload.get('success', False)
        if not success:
            print(f"Custom logic: on_gototargets_request failed. "
                  f"Success: {success}, Message: {response_payload.get('message')}")
            return

        body = response_payload.get('body')
        if not body or not body.get('targets'):
            print(f"Custom logic: No goto targets found in response body: {body}")
            return

        # 첫 번째 타겟 정보 꺼내기
        first_target: dict = body['targets'][0]
        target_obj = pydevd_schema.GotoTarget(**first_target)
        target_id = target_obj.id
        print(f"Custom logic: Got goto target ID: {target_id} "
              f"(label: '{target_obj.label}', line: {target_obj.line})")

        # 현재 스레드의 DAP threadId 얻기
        dap_thread_id = get_thread_id(threading.current_thread())
        if dap_thread_id is None:
            print("Custom logic: Critical - DAP thread ID not found. Cannot proceed with on_goto_request.")
            return
        print(f"Custom logic: DAP thread ID finally obtained: {dap_thread_id}. Proceeding with on_goto_request.")

        # Goto 요청 생성 및 전송
        NetCommand.next_seq += 2
        seq_goto = NetCommand.next_seq
        goto_args = pydevd_schema.GotoArguments(
            threadId=dap_thread_id,
            targetId=target_id
        )
        goto_request = pydevd_schema.GotoRequest(
            arguments=goto_args,
            seq=seq_goto,
            type='request',
            command='goto'
        )
        print(f"Custom logic: Calling on_goto_request (seq: {seq_goto}) for target ID {target_id} "
              f"on DAP thread {dap_thread_id}")
        net_command_goto = json_processor.on_goto_request(pydb, goto_request)

        if not (net_command_goto and hasattr(net_command_goto, 'as_dict')):
            print(f"Custom logic: No valid response dict from on_goto_request. Command object: {net_command_goto}")
            return

        response_goto = net_command_goto.as_dict
        if response_goto.get('success'):
            print("Custom logic: Jump to cursor successfully initiated by on_goto_request.")
        else:
            print(f"Custom logic: on_goto_request indicates failure: {response_goto.get('message')}")

    except ImportError as imp_err:
        print(f"Custom logic: ImportError during jump to cursor test: {imp_err}\n{traceback.format_exc()}")
    except Exception as gen_err:
        print(f"Custom logic: General exception in jump to cursor test block: {gen_err}\n{traceback.format_exc()}")

def parse(variable_data: dict) -> list:
    if variable_data['name'] == 'function variables':
        return []

    if variable_data['type'] in ('int', 'float', 'bool', 'str'):
        return [[variable_data['evaluateName'], variable_data['value']]]
    
    elif variable_data['type'] in ('list', 'tuple', 'set'):
        return [
            [variable_data['evaluateName'], f'{variable_data["type"]}(range({len(variable_data["value"][1:-1].split(","))}))'],
            *[
                item
                for var in variable_data['recursive_children']
                for item in parse(var)
                if var['name'] not in ('function variables', 'len()', 'keys()', 'values()', 'items()')
            ]
        ]
    
    elif variable_data['type'] == 'dict':
        return [
            [variable_data['evaluateName'], f'{variable_data["type"]}()'],
            *[
                item
                for var in variable_data['recursive_children']
                for item in parse(var)
                if var['name'] not in ('function variables', 'len()', 'keys()', 'values()', 'items()')
            ]
        ]
    
    else:  # Class
        return [
            [variable_data['evaluateName'], f'{variable_data["type"]}.__new__({variable_data["type"]})'],
            *[
                item
                for var in variable_data['recursive_children']
                for item in parse(var)
            ]
        ]

def receive_dap_message(sock):
    """DAP 표준 형식으로 데이터 수신"""
    try:
        print("📥 [DAP-RECV] 메시지 수신 시작...")
        
        # 1단계: 헤더 읽기
        header_data = b""
        while b"\r\n\r\n" not in header_data:
            chunk = sock.recv(1024)
            if not chunk:
                print("❌ [DAP-RECV] 연결 종료됨 (헤더 읽기 중)")
                return None
            header_data += chunk
        
        # 2단계: Content-Length 파싱
        header_str = header_data.decode('ascii')
        content_length = None
        for line in header_str.split('\r\n'):
            if line.startswith('Content-Length:'):
                content_length = int(line.split(':', 1)[1].strip())
                break
        
        if content_length is None:
            print("❌ [DAP-RECV] Content-Length 헤더 없음")
            return None
        
        print(f"📥 [DAP-RECV] Content-Length: {content_length}")
        
        # 3단계: 정확한 크기만큼 데이터 읽기
        data_bytes = b""
        while len(data_bytes) < content_length:
            remaining = content_length - len(data_bytes)
            chunk = sock.recv(min(remaining, 8192))
            if not chunk:
                print("❌ [DAP-RECV] 연결 종료됨 (데이터 읽기 중)")
                return None
            data_bytes += chunk
        
        print(f"✅ [DAP-RECV] 수신 완료: {len(data_bytes)} bytes")
        return data_bytes
        
    except Exception as e:
        print(f"❌ [DAP-RECV] 수신 오류: {e}")
        return None

class wait_for_client:
    def __call__(self, exception=None, context=None, restart=False):
        ensure_logging()
        log.debug("wait_for_client()")
        print("wait_for_client() called with exception:", exception, "and restart:", restart)

        # <--- 여기에 사용자 정의 기능 추가 (대기 시작 전) --- >
        # 예시: 특정 조건 확인 또는 로그 기록
        print("Custom logic: wait_for_client() is about to start waiting.")
        # <--- 사용자 정의 기능 끝 --- >

        pydb = get_global_debugger()
        if pydb is None:
            # This means that settrace() was not called, so there's nothing to wait for.
            # This can happen if listen() or connect() failed.
            log.info("wait_for_client() ignored - settrace() not called")
            return

        cancel_event = threading.Event()
        self.cancel = cancel_event.set
        pydevd._wait_for_attach(cancel=cancel_event)

        # <--- 여기에 사용자 정의 기능 추가 (대기 종료 후) --- >
        # 예시: 클라이언트 연결 성공/실패 또는 취소 시 로그 기록
        if is_client_connected():
            # ---------------------- Custom Logic: send remaining time to developer PC & if restart, receive the capture_data ----------------------
            remaining = context.get_remaining_time_in_millis()
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(("165.194.27.222", 6689))  # 개발자 PC IP + 수신 포트
                msg = std_json.dumps({"remaining_ms": remaining}).encode('utf-8')
                sock.sendall(msg)
                print(f"📤 timeout = {remaining} ms 전송 완료")
                
                # 재디버깅인 경우, apply process 시작
                if(restart):
                    # capture_data를 수신
                    print("🔄 이전 상태 JSON 응답 대기 중...")
            
                    # DAP 방식으로 JSON 수신
                    json_data = receive_dap_message(sock)
                    
                    # 잘 받았는지 테스트
                    if json_data:
                        print(f"✅ JSON 수신 성공! 크기: {len(json_data)} bytes")
                        
                        
                        try:
                            parsed_json = std_json.loads(json_data.decode('utf-8'))
                            
                            print(f"📊 JSON 구조 확인:")
                            print(f"  - 최상위 키: {list(parsed_json.keys())}")
                            
                            if "callstacks" in parsed_json:
                                callstacks = parsed_json["callstacks"]
                                print(f"  - callstacks 개수: {len(callstacks)}")
                                
                                if len(callstacks) > 0:
                                    first_frame = callstacks[0]
                                    print(f"  - 첫 번째 프레임: {first_frame.get('function', 'unknown')}")
                                    
                                    variables = first_frame.get('variables', {})
                                    locals_count = len(variables.get('locals', []))
                                    globals_count = len(variables.get('globals', []))
                                    print(f"  - 변수 개수: locals={locals_count}, globals={globals_count}")
                            
                            print("🎉 DAP JSON 파일 전송 테스트 성공!")
                            
                        except std_json.JSONDecodeError as e:
                            print(f"❌ JSON 파싱 실패: {e}")
                            print(f"📋 받은 데이터 (처음 200자): {json_data[:200]}")
                            
                    else:
                        print("❌ JSON 수신 실패")
                        
                    # apply process 시작
                    # json_data를 std_json.load()로 파싱하려면 BytesIO로 감싸야 함
                    import io
                    with io.BytesIO(json_data) as f:
                        data = std_json.load(f)
                       
                    capture_callstacks = data.get("callstacks", [])
                    
                    
                    for i in range(len(capture_callstacks)):
                        if capture_callstacks[i].get("line") == -1:
                            continue  # -1인 경우는 무시
                        
                        function_name = capture_callstacks[i].get("function", "unknown_function")
                        file_name = capture_callstacks[i].get("file", "unknown_file.py")
                        print(f"🔄 복원할 프레임: {function_name} in {file_name}")
                        # ---------------------- jump_to()를 사용하여 각 프레임으로 이동 ---------------------- 
                        try:
                            jump_to(pydb,
                                    file_path=os.path.normpath("/var/task/".join(file_name)),  # 실제 파일 경로로 변경
                                    target_line=capture_callstacks[i].get("line", 1))  # 기본값 1로 설정
                        except Exception as e:
                            print(f"❗ jump_to 실패: {e}")
                            
                        # ---------------------- 각 프레임 변수 복원 ----------------------
                        function_name_from_capture = capture_callstacks[i].get("function")    # lambda_handler
                        if not function_name_from_capture:
                            print(f"Custom logic: Skipping a captured frame because it has no function name. Frame ID: {capture_callstacks[i].get('frame_id')}")
                            continue

                        print(f"Custom logic: Processing captured frame: {function_name_from_capture}")
                        
                        frame_file_name_from_capture = capture_callstacks[i].get('file', 'unknown_file.py')   # lambda_function.py
                        

                        target_frame = None
                        expected_filename = None
                        if frame_file_name_from_capture:
                            # Assuming /var/task is the root for lambda execution environment or similar
                            # This path might need to be made more robust or configurable
                            expected_filename = os.path.normpath(os.path.join("/var/task", frame_file_name_from_capture))
                            print(f"Custom logic: Using inspect.stack(). Expected file for '{function_name_from_capture}': {expected_filename}")

                            # 복원할 프레임을 찾기 위해 현재 스택을 검사
                            try:
                                current_stack = inspect.stack()
                                for frame_info in current_stack:
                                    frame_obj = frame_info.frame if hasattr(frame_info, 'frame') else frame_info[0]
                                    filename_live = os.path.normpath(frame_obj.f_code.co_filename)
                                    func_name_live = frame_obj.f_code.co_name

                                    if func_name_live == function_name_from_capture and filename_live == expected_filename:
                                        print(f"Custom logic: Found target '{function_name_from_capture}' stack frame in '{filename_live}'.")
                                        target_frame = frame_obj
                                        break 
                                    del frame_obj # Clean up frame_obj if not the target
                                del current_stack # Clean up stack
                            except Exception as e:
                                print(f"Custom logic: Error inspecting stack for {function_name_from_capture}: {e}")
                            
                            # target_frame이 발견되면 캡처 데이터를 적용
                            if target_frame:
                                try:
                                    for _var_data in capture_callstacks[i].get('variables', {}).get('locals', []):
                                        for item in parse(_var_data):
                                            print(f"Custom logic: Attempting to change '{item[0]}' to '{item[1]}' in frame {target_frame.f_code.co_name if hasattr(target_frame, 'f_code') else target_frame}.")
                                            change_attr_expression(
                                                target_frame,
                                                item[0],
                                                item[1],
                                                pydb
                                            )
                                except Exception as e:
                                    print(f"Custom logic: Failed to apply capture data to frame {function_name_from_capture}: {e}")
                        else:
                            print(f"Custom logic: frame_file_name_from_capture is not set for {function_name_from_capture}, cannot determine expected_filename.")
                        
                        # ---------------------- 다음 callstack이 있으면 step_in()을 사용하여 다음 프레임으로 이동 ----------------------
                        if (i < len(capture_callstacks) - 1):
                            print("Custom logic: Finished jump to cursor test.")                
                            print("Custom logic: Starting step-in test.")

                            try:
                                json_processor = PyDevJsonCommandProcessor(from_json=lambda data, cls=None: cls(**data) if cls else data)
                                print("Custom logic: Using PyDevJsonCommandProcessor for step-in test.")

                                # 현재 스레드의 DAP thread ID 가져오기
                                dap_thread_id = get_thread_id(threading.current_thread())
                                print(f"Custom logic: Current DAP thread ID: {dap_thread_id}")

                                if dap_thread_id is not None:
                                    # Step Into 요청 생성
                                    NetCommand.next_seq += 2
                                    seq_step_in = NetCommand.next_seq
                                    
                                    step_in_args = pydevd_schema.StepInArguments(
                                        threadId=dap_thread_id,
                                        singleThread=True  # 단일 스레드에서만 step
                                    )
                                    
                                    step_in_request = pydevd_schema.StepInRequest(
                                        arguments=step_in_args,
                                        seq=seq_step_in,
                                        type='request',
                                        command='stepIn'
                                    )
                                    
                                    print(f"Custom logic: Calling on_stepin_request (seq: {seq_step_in}) for thread {dap_thread_id}")
                                    net_command_step_in = json_processor.on_stepin_request(pydb, step_in_request)

                                    if net_command_step_in and hasattr(net_command_step_in, 'as_dict'):
                                        response_payload_step_in = net_command_step_in.as_dict
                                        print(f"Custom logic: on_stepin_request response: {std_json.dumps(response_payload_step_in)}")
                                        if response_payload_step_in and response_payload_step_in.get('success'):
                                            print("Custom logic: Step-in command successfully initiated.")
                                        else:
                                            print(f"Custom logic: Step-in failed: {response_payload_step_in.get('message') if response_payload_step_in else 'No response'}")
                                    else:
                                        print(f"Custom logic: No valid response from on_stepin_request. Command object: {net_command_step_in}")
                                else:
                                    print("Custom logic: DAP thread ID not available for step-in test.")

                            except ImportError as e_step_imp:
                                print(f"Custom logic: ImportError during step-in test: {e_step_imp}\\n{traceback.format_exc()}")
                            except Exception as e_step:
                                print(f"Custom logic: Exception during step-in test: {e_step}\\n{traceback.format_exc()}")
                            
                            print("Custom logic: Finished step-in test.")
                        
                
                # if not restart -> jump to the line Exception occurred    
                else:
                    print("🔄 재디버깅이 아니므로 예외 발생 위치로 이동합니다.")
                    # ---------------------- Custom logic: Test jump to cursor ----------------------
                    try: 
                        last = list(traceback.walk_tb(exception.__traceback__))[-1]
                        target_line = last[1]
                        print("라인 번호:", target_line)
                        jump_to(pydb, 
                                file_path=os.path.normpath("/var/task/lambda_function.py"),  # 실제 파일 경로로 변경
                                target_line=target_line)
                    except Exception as e:
                        print(f"❗ jump_to 실패: {e}")
                        
                # restart이든 첫 실행이든, 소켓 닫기        
                sock.close()                
                        
            except Exception as e:
                print(f"❗ 전송 실패: {e}")

        else: # This is the else for if is_client_connected()
            print("Custom logic: wait_for_client() finished, but no client connected (possibly cancelled).")        
        # <--- 사용자 정의 기능 끝 --- >
        # debugpy.breakpoint()

wait_for_client = wait_for_client()


def is_client_connected():
    return pydevd._is_attached()


def breakpoint():
    ensure_logging()
    if not is_client_connected():
        log.info("breakpoint() ignored - debugger not attached")
        return
    log.debug("breakpoint()")

    # Get the first frame in the stack that's not an internal frame.
    pydb = get_global_debugger()
    stop_at_frame = sys._getframe().f_back
    while (
        stop_at_frame is not None
        and pydb.get_file_type(stop_at_frame) == pydb.PYDEV_FILE
    ):
        stop_at_frame = stop_at_frame.f_back

    _settrace(
        suspend=True,
        trace_only_current_thread=True,
        patch_multiprocessing=False,
        stop_at_frame=stop_at_frame,
    )
    stop_at_frame = None


def debug_this_thread():
    ensure_logging()
    log.debug("debug_this_thread()")

    _settrace(suspend=False)


def trace_this_thread(should_trace):
    ensure_logging()
    log.debug("trace_this_thread({0!r})", should_trace)

    pydb = get_global_debugger()
    if should_trace:
        pydb.enable_tracing()
    else:
        pydb.disable_tracing()
