# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
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
"""Functions to wrap angles at different values."""

# Third Party
import numpy as np


def at_180(value: float) -> float:
    """Remap an angle from [0, 360) to [-180, 180).

    Note: Zero maps to zero.
       -1   ->  -1
        0   ->  0
        1   ->  1
           ...
        179 ->  179
        180 -> -180
        181 -> -179
           ...
        359 -> -1
        360 ->  0
        361 ->  1
    """
    return (value + 180) % 360 - 180


def at_pi(value: float) -> float:
    """Remap an angle from [0, 2*pi) to [-pi, pi).

    Note: Zero maps to zero.
        0-eps    ->  0-eps
        0        ->  0
        0+eps    ->  0+eps
                 ...
        pi-eps   ->  pi-eps
        pi       -> -pi
        pi+eps   -> -pi+eps
                 ...
        2*pi-eps ->  0-eps
        2*pi     ->  0
        2*pi+eps ->  0+eps
    """
    return ((value + np.pi) % (2 * np.pi)) - np.pi


def at_360(value: float) -> float:
    """Remap an angle from [-180, 180) to [0, 360).

    Note: Zero maps to zero.
        -181 -> 179
        -180 -> 180
        -179 -> 181
           ...
        -1   -> 359
         0   -> 0
         1   -> 1
           ...
         179 -> 179
         180 -> 180
         181 -> 181
    """
    return value % 360


def at_2pi(value: float) -> float:
    """Remap an angle from [-pi, pi) to [0, 2*pi).

    Note: Zero maps to zero.
        -pi-eps -> pi-eps
        -pi     -> pi
        -pi+eps -> pi+eps
           ...
        0-eps   -> 2*pi-eps
        0       -> 0
        0+eps   -> 0+eps
           ...
        pi-eps  -> pi-eps
        pi      -> pi
        pi+eps  -> pi+eps
    """
    return value % (2 * np.pi)
