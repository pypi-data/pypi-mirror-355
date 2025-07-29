import ast
import inspect
import os
import pickle
import shutil

import executing


class _DummyObject:
    def __init__(self, locals, varname: str, file_path: str):
        self.varname = varname
        self.file_path = file_path
        self.locals = locals

    def __load__(self):
        try:
            with open(self.file_path, "rb") as f:
                print(f"Loading {self.varname} from {self.file_path}")
                object = pickle.load(f)
            self.locals[self.varname] = object
            return object
        except Exception as e:
            print(f"Error loading {self.varname}: {e}")

    def __getattribute__(self, item):
        if item in {"varname", "file_path", "locals", "__load__"}:
            return super().__getattribute__(item)
        else:
            print(f"Getting attribute {item} of {self.varname}")
            return self.__load__().__getattribute__(item)

    def __repr__(self):
        return self.__load__().__repr__()


class Session:
    def __init__(self, locals, save_dir: str, clean: bool):
        self.save_dir = save_dir
        self.locals = locals

        if clean:
            shutil.rmtree(save_dir, ignore_errors=True)

        os.makedirs(save_dir, exist_ok=True)
        # get all files in the save_dir
        loaded = []
        not_loaded = []
        for file in os.listdir(save_dir):
            if file.endswith(".pkl"):
                varname = file.removesuffix(".pkl")
                if varname not in self.locals:
                    loaded.append(varname)
                    self.locals[varname] = _DummyObject(
                        self.locals, varname, os.path.join(save_dir, file)
                    )
                else:
                    not_loaded.append(varname)
        if loaded:
            print(f"Lazily loaded {loaded}")
        if not_loaded:
            print(
                f"Did not load the following variables because they already exist: {not_loaded}. Use load() to load them."
            )

    def save(self, varname, value):
        with open(os.path.join(self.save_dir, f"{varname}.pkl"), "wb") as f:
            pickle.dump(value, f)

    def load(self, varname):
        with open(os.path.join(self.save_dir, f"{varname}.pkl"), "rb") as f:
            self.locals[varname] = pickle.load(f)
            return self.locals[varname]


def _save_fn(fn):
    def wrapper(*args, **kwargs):
        output = fn(*args, **kwargs)
        frame = inspect.currentframe().f_back  # Get caller's frame
        node = executing.Source.executing(frame).node
        if node is not None:
            source = executing.Source.for_frame(frame)
            line = source.lines[node.lineno - 1]
            # now we need to get the name of the variable
            varname = line.split("=")[0].strip()
            _get_session(frame).save(varname, output)
        return output

    return wrapper


def save(x):
    if callable(x):
        return _save_fn(x)
    else:
        frame = inspect.currentframe().f_back  # Get caller's frame
        node = executing.Source.executing(frame).node
        if node is not None and isinstance(node, ast.Call) and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Name):
                varname = arg.id
                _get_session(frame).save(varname, x)
                return x
        raise ValueError(f"Could not determine name of variable to save: {node}")


def load(varname):
    return _get_session().load(varname)


def init(folder: str = "tmp", clean: bool = False, frame=None):
    if frame is None:
        frame = inspect.currentframe().f_back
    global session
    session = Session(frame.f_locals, folder, clean)


def _get_session(frame):
    if session is None:
        init(frame=frame)
    return session


session = None
