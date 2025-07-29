# Copyright (c) 2021 Emanuele Bellocchia
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#
# Imports
#
from typing import Dict, List, Union


#
# Classes
#

# Chart info class
class ChartInfo:

    coin_id: str
    coin_vs: str
    last_days: int
    x: List[int]
    y: List[float]

    # Constructor
    def __init__(self,
                 chart_info: Dict[str, List[List[Union[int, float]]]],
                 coin_id: str,
                 coin_vs: str,
                 last_days: int) -> None:
        self.coin_id = coin_id
        self.coin_vs = coin_vs
        self.last_days = last_days
        self.x = []
        self.y = []

        for price in chart_info["prices"]:
            self.x.append(int(price[0] / 1000))     # Convert timestamp from milliseconds to seconds
            self.y.append(price[1])

    # Get coin ID
    def CoinId(self) -> str:
        return self.coin_id

    # Get coin VS
    def CoinVs(self) -> str:
        return self.coin_vs

    # Get last days
    def LastDays(self) -> int:
        return self.last_days

    # Get x coordinates
    def X(self) -> List[int]:
        return self.x

    # Get y coordinates
    def Y(self) -> List[float]:
        return self.y
