# -*- coding: utf-8 -*-
# Copyright (c) 2025-2025 Huawei Technologies Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from collections import deque

from ..validation import validate_params
from ..constraints import Rule, where


class WalkLimitError(Exception):
    pass


@validate_params({"root_dir": Rule.input_dir_traverse})
def walk_s(root_dir, *, dir_rule=Rule.input_dir_traverse, file_rule=Rule.input_file_read, max_files=10000, max_depths=100):
    depth = 0
    root_dir = os.path.realpath(root_dir)
    queue = deque([(root_dir, depth)])

    file_scanned = 0

    while queue:
        current_dir, current_depth = queue.pop()

        if file_scanned > max_files:
            raise WalkLimitError(f"Limit exceeded: {file_scanned} / {max_files}")
        
        if current_depth > max_depths:
            raise WalkLimitError(f"Limit exceeded: {current_depth} / {max_depths}")

        for it in os.scandir(current_dir):
            if it.is_dir(follow_symlinks=False):
                if dir_rule is None or dir_rule.is_satisfied_by(it.path):
                    yield it.path

                    queue.append((it.path, depth + 1))
            
            elif it.is_file(follow_symlinks=False):
                if file_rule is None or file_rule.is_satisfied_by(it.path):
                    yield it.path
            
            file_scanned += 1


def open_s(path, mode='r', **kwargs):
    if mode not in {'r', 'w', 'x', 'a', 'b', '+'}:
        raise ValueError(f"'mode' must be in {{'r', 'w', 'x', 'a', 'b', '+'}}. Got {mode} instead")
    
    flags = 0
    if '+' in mode:
        flags |= os.O_RDWR
    elif 'r' in mode:
        flags |= os.O_RDONLY
    else:
        flags |= os.O_WRONLY
    
    if 'w' in mode or 'x' in mode:
        flags |= os.O_CREAT
    if 'w' in mode:
        flags |= os.O_TRUNC
    if 'x' in mode:
        flags |= os.O_EXCL
    if 'a' in mode:
        flags |= os.O_APPEND | os.O_CREAT
    
    if 'b' in mode:
        flags |= getattr(os, 'O_BINARY', 0)
    
    @validate_params(
        {"path": where('r' in mode, Rule.input_file_read, Rule.output_path_write, description="open file in read mode")}
    )
    def get_fd(path, flags):
        fd = os.open(path, flags, mode=0o640)
        return fd
    
    fd = get_fd(path, flags)
    return os.fdopen(fd, mode, **kwargs)
